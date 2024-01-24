import math
import os
from hplib import hplib as hpl
from tespy.networks import Network
from tespy.components import (
    Sink, Source, Compressor, Condenser, Pump, HeatExchangerSimple,
    Valve, Drum, HeatExchanger, CycleCloser
)
from tespy.connections import Connection, Ref
from tespy.tools.characteristics import CharLine
from tespy.tools.characteristics import load_default_char as ldc
from bisect import bisect_left

import json
# Saved design data and limits for the different heat pump models
JSON_DATA_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), 'eta_s_data.json'))

class Heat_Pump_Design():
    """
    Design of the heat pump model for the different calculation modes
    """
    def __init__(self, params, COP_m_data=None):

        # Parameters required for all models
        self.hp_model = params.get('hp_model')
        self.heat_source = params.get('heat_source')
        self.calc_mode = params.get('calc_mode')

        # Parameters required if the 'hplib' calculation mode is chosen
        self.hp_limits = params.get('hp_limits', None)

        # Parameters required if 'Generic' heat pump is chosen in the 'hplib' calculation mode
        self.P_th = params.get('P_th', None)
        self.cons_T = params.get('cons_T', None)
        self.heat_source_T = params.get('heat_source_T', None)

        # Parameters required for the 'fixed' calculation mode
        self.COP_fixed = params.get('COP', None)
        self.HC_fixed = params.get('heating capacity', None)
        self.cond_m_fixed = params.get('cond_m', None)

        # Attributes of the heat pump
        self.LFE = None  # The temperature of the fluid leaving the evaporator
        self.LFE_des = None  # The temperature of the water leaving the condenser in design case
        self.LWC = None  # The temperature of the water leaving the condenser
        self.LWC_des = None  # The temperature of the fluid leaving the evaporator in design case
        self.heat_source_T_des = None  # The heat source temperature in design case
        self.etas_des = None  # The compressor efficiency in design case
        self.heatload_des = None  # The heating capacity in design case
        self.cmp_stages = 1  # The number of stages of compression
        self.ic = False  # Intercooler between the compressors, if more than one stage of compression
        self.sh = False  # Super heater for the fluid entering the evaporator
        self.idx = None  # Index to keep track of the current design point
        self.id_old = None  # Index to keep track of the previous design point
        self.nw = None  # The network with all the components
        self.Q_Demand = None  # The heat demand for the heat pump
        self.Q_Supplied = None  # Heat supplied by the heat pump
        self.on_fraction = None  # The fraction of timestep for which the heat pump operates
        self.cond_m = None  # The mass flow of water in condenser
        self.Q_evap = None  # The heat extracted from source in the evaporator
        self.COP_m_data = COP_m_data  # The saved data for fast calculation mode
        self.skip_step = False  # Used to skip a step in case of an error

        # Initiating the heat pump model for the hplib mode
        if 'hplib' in self.calc_mode.lower():
            if self.hp_model == 'Generic':
                if 'air' in self.heat_source.lower():
                    parameters = hpl.get_parameters(model=self.hp_model, group_id=1, t_in=self.heat_source_T, t_out=self.cons_T,
                                                    p_th=self.P_th)
                elif 'water' in self.heat_source.lower():
                    parameters = hpl.get_parameters(model=self.hp_model, group_id=2, t_in=self.heat_source_T, t_out=self.cons_T,
                                                    p_th=self.P_th)
            else:
                parameters = hpl.get_parameters(self.hp_model)

            self.hp = hpl.HeatPump(parameters)
            # Update the heat pump model to the equivalent model for the control limits
            self.hp_model = params.get('equivalent_hp_model', None)

        # Initiating the heat pump model for the detailed mode
        if 'detailed' in self.calc_mode.lower():
            if self.cons_T is None:
                self.cons_T = 35
            if self.heat_source_T is None:
                self.heat_source_T = 5
            self.cond_in_T = self.cons_T - 5
            self._etas_heatload_id()
            self._design_hp()



    def _take_closest(self, myList, myNumber):
        """
        Assumes myList is sorted. Returns closest value to myNumber.
        If two numbers are equally close, return the smallest number.
        """
        pos = bisect_left(myList, myNumber)
        if pos == 0:
            return myList[0]
        if pos == len(myList):
            return myList[-1]
        before = myList[pos - 1]
        after = myList[pos]
        if after - myNumber < myNumber - before:
            return after
        else:
            return before


    def _etas_heatload_id(self):
        """
        * Used for all the calculation modes except 'fixed' mode.
        * Uses the pre-saved data from the "eta_s_data.json" file
        * Checks the inputs, **cond_in_T** and **heat_source_T**, against the limits of operation for the chosen heat
          pump model.
        * Identifies the closest design point for the inputs, for the 'detailed' calculation mode
        """

        # Check to ensure temperature in the condenser is higher than in the evaporator
        if self.heat_source_T > self.cond_in_T:
            self.skip_step = True

        if not self.skip_step:

            # If the heat pump operation limits have to be read from the saved data files
            if self.hp_limits is None:
                # Reading the pre-saved json data file
                with open(JSON_DATA_FILE, "r") as read_file_1:
                    data_1 = json.load(read_file_1)

                etas_dict = data_1[self.hp_model]['eta_s']
                heatload_dict = data_1[self.hp_model]['heatload']
                id_dict = data_1[self.hp_model]['ids']

                # Identifying the limits for the heat source temperature
                heat_source_T_min = min(list(map(int, etas_dict)))
                heat_source_T_max = max(list(map(int, etas_dict)))

                # Identifying the design point temperatures in the evaporator
                if heat_source_T_min <= self.heat_source_T <= heat_source_T_max:
                    idx_T = self._take_closest(list(map(int, etas_dict)), (self.heat_source_T))
                    self.heat_source_T_des = idx_T
                    self.LFE_des = self.heat_source_T_des - 5  # A delta_T of 5K is assumed in the evaporator
                else:
                    self.skip_step = True

                if not self.skip_step:

                    # Identifying the limits for the condenser outlet temperatures
                    clean_dict = {k: etas_dict[str(idx_T)][k] for k in etas_dict[str(idx_T)] if
                                  etas_dict[str(idx_T)][k] is not None}

                    cons_T_min = min(list(map(int, clean_dict)))
                    self.cons_T_max = max(list(map(int, clean_dict)))

                    # A delta_T of 5K is assumed in the condenser
                    cons_T_des = self.cond_in_T + 5

                    # Calculating the design point temperature for the condenser  outlet
                    if cons_T_des < cons_T_min:
                        self.skip_step = True
                    elif cons_T_des > self.cons_T_max:
                        if (self.cond_in_T < self.cons_T_max) and ('hplib' not in self.calc_mode.lower()):
                            cons_T_des = self.cons_T_max
                        else:
                            self.skip_step = True

                    self.LWC_des = self._take_closest(list(map(int, etas_dict[str(idx_T)])), cons_T_des)

                    # Identifying the isentropic efficiency of the compressor for the design point
                    self.etas_des = etas_dict[str(idx_T)][str(self.LWC_des)]

                    # Identifying the heating capacity of the heat pump for the design point
                    heatload_des = heatload_dict[str(idx_T)][str(self.LWC_des)]

                    if heatload_des is None:
                        self.skip_step = True
                        self.heatload_des = 0.0
                        self.heatload_max = 0.0
                        self.heatload_min = 0.0

                    else:
                        self.heatload_des = heatload_des * 1000
                        self.heatload_max = self.heatload_des
                        self.heatload_min = data_1[self.hp_model]['min_heatload']

                    # Saving the index of the design point
                    self.idx = id_dict[str(idx_T)][str(self.LWC_des)]

            # If temperature limits are specified via the 'hp_limits' parameter
            else:
                if self.hp_limits['heat_source_T_min'] > self.heat_source_T:
                    self.skip_step = True
                elif self.hp_limits['heat_source_T_max'] < self.heat_source_T:
                    self.skip_step = True

                cons_T_des = self.cond_in_T + 5
                if cons_T_des < self.hp_limits['cons_T_min']:
                    self.skip_step = True
                elif cons_T_des > self.hp_limits['cons_T_max']:
                    self.skip_step = True

                self.heatload_min = self.hp_limits['heatload_min']

    def _design_hp(self):
        """
        * Used in the 'detailed' calculation mode to solve the TESPy network of the heat pump in the design mode
        * Number of stages of compression can be 1 (default) or 2
        * Intercooler between the two stages of compression is optional
        * Superheater between the evaporator and the compressor is optional
        * fixed and variable mass flow in the evaporator
        """

        # Index for the design point in the 'detailed' calculation mode
        self.id_old = self.idx

        # The parameters that will vary for the different heat pump models are defined here
        # 'ref' is the refrigerant, 'm_air'/'m_water' define the heat source of the heat pump
        # Parametrization obtained from 'Parametrization_NominalData.py'
        if 'air_6kw' in self.hp_model.lower():
            params_des = {'ref': 'R410a', 'm_air': 1, 'm_water': 0, 'ttd_u': 10}
        elif 'air_8kw' in self.hp_model.lower():
            params_des = {'ref': 'R410a', 'm_air': 1, 'm_water': 0, 'ttd_u': 12}
        elif 'air_16kw' in self.hp_model.lower():
            params_des = {'ref': 'R410a', 'm_air': 1, 'm_water': 0, 'ttd_u': 15}
        elif 'air_60kw' in self.hp_model.lower():
            params_des = {'ref': 'R22', 'm_air': 1, 'm_water': 0, 'ttd_u': 15, 'pr': 2}
            self.cmp_stages = 2  # Number of stages of compression
            self.ic = True       # Intercooler between compression stages
            self.sh = True       # Superheater between evaporator and compressor
        elif 'air_30kw' in self.hp_model.lower():
            params_des = {'ref': 'R404a', 'm_air': 1, 'm_water': 0, 'ttd_u': 5}
            if '1stage' not in self.hp_model.lower():
                self.cmp_stages = 2
                params_des['pr'] = 1.35
        elif 'water' in self.hp_model.lower():
            params_des = {'ref': 'R407c', 'm_air': 0, 'm_water': 1, 'ttd_u': 23}

        self.nw = Network(fluids=[params_des['ref'], 'air', 'water'], T_unit='C', p_unit='bar',
                          h_unit='kJ / kg', m_unit='kg / s')

        self.nw.set_attr(iterinfo=False)

        # %% components

        # sources & sinks
        cool_closer = CycleCloser('coolant cycle closer')
        cons_closer = CycleCloser('consumer cycle closer')
        amb_in = Source('source ambient')
        amb_out = Sink('sink ambient')

        if self.cmp_stages == 2:
            if self.ic is True:
                ic_in = Source('source intercool')
                ic_out = Sink('sink intercool')

        # ambient air system
        apu = Pump('ambient pump')

        # consumer system

        cd = Condenser('condenser')
        crp = Pump('condenser recirculation pump')
        cons = HeatExchangerSimple('consumer')

        # evaporator system

        va = Valve('valve')
        dr = Drum('drum')
        ev = HeatExchanger('evaporator')
        erp = Pump('evaporator recirculation pump')

        if self.sh is True:
            su = HeatExchanger('superheater')

        # compressor-system

        cp1 = Compressor('compressor 1')

        if self.cmp_stages == 2:
            cp2 = Compressor('compressor 2')
            if self.ic is True:
                he = HeatExchanger('intercooler')

        # %% connections

        # consumer system

        c_in_cd = Connection(cool_closer, 'out1', cd, 'in1')
        close_crp = Connection(cons_closer, 'out1', crp, 'in1')
        crp_cd = Connection(crp, 'out1', cd, 'in2')
        cd_cons = Connection(cd, 'out2', cons, 'in1')
        cons_close = Connection(cons, 'out1', cons_closer, 'in1')


        self.nw.add_conns(c_in_cd, close_crp, crp_cd, cd_cons, cons_close)

        # connection condenser - evaporator system

        cd_va = Connection(cd, 'out1', va, 'in1')

        self.nw.add_conns(cd_va)

        # evaporator system

        va_dr = Connection(va, 'out1', dr, 'in1')
        dr_erp = Connection(dr, 'out1', erp, 'in1')
        erp_ev = Connection(erp, 'out1', ev, 'in2')
        ev_dr = Connection(ev, 'out2', dr, 'in2')

        self.nw.add_conns(va_dr, dr_erp, erp_ev, ev_dr)

        amb_in_apu = Connection(amb_in, 'out1', apu, 'in1')
        ev_amb_out = Connection(ev, 'out1', amb_out, 'in1')

        self.nw.add_conns(amb_in_apu, ev_amb_out)

        if self.sh is True:
            dr_su = Connection(dr, 'out2', su, 'in2')
            apu_su = Connection(apu, 'out1', su, 'in1')
            su_ev = Connection(su, 'out1', ev, 'in1')
            su_cp1 = Connection(su, 'out2', cp1, 'in1')
            self.nw.add_conns(dr_su, apu_su, su_ev, su_cp1)
        else:
            dr_cp1 = Connection(dr, 'out2', cp1, 'in1')

            apu_ev = Connection(apu, 'out1', ev, 'in1')

            self.nw.add_conns(dr_cp1, apu_ev)

        if self.ic is True:
            cp1_he = Connection(cp1, 'out1', he, 'in1')
            he_cp2 = Connection(he, 'out1', cp2, 'in1')
            cp2_cc = Connection(cp2, 'out1', cool_closer, 'in1')

            ic_in_he = Connection(ic_in, 'out1', he, 'in2')
            he_ic_out = Connection(he, 'out2', ic_out, 'in1')

            self.nw.add_conns(cp1_he, he_cp2, ic_in_he, he_ic_out, cp2_cc)
        else:
            if self.cmp_stages == 2:
                cp1_cp2 = Connection(cp1, 'out1', cp2, 'in1')
                cp2_cc = Connection(cp2, 'out1', cool_closer, 'in1')
                self.nw.add_conns(cp1_cp2, cp2_cc)
            else:
                cp1_cc = Connection(cp1, 'out1', cool_closer, 'in1')
                self.nw.add_conns(cp1_cc)

        # %% component parametrization

        # condenser system

        cd.set_attr(pr1=0.99, pr2=0.99, ttd_u=params_des['ttd_u'], design=['pr2', 'ttd_u'],
                    offdesign=['zeta2', 'kA_char'])

        crp.set_attr(eta_s=0.8, design=['eta_s'], offdesign=['eta_s_char'])
        cons.set_attr(pr=0.99, design=['pr'], offdesign=['zeta'])

        # evaporator system

        kA_char1 = ldc('heat exchanger', 'kA_char1', 'DEFAULT', CharLine)
        kA_char2 = ldc('heat exchanger', 'kA_char2', 'EVAPORATING FLUID', CharLine)

        ev.set_attr(pr1=0.99, pr2=0.99, ttd_l=5,
                    kA_char1=kA_char1, kA_char2=kA_char2,
                    design=['pr1', 'ttd_l'], offdesign=['zeta1', 'kA_char'])
        erp.set_attr(eta_s=0.8, design=['eta_s'], offdesign=['eta_s_char'])
        apu.set_attr(eta_s=0.8, design=['eta_s'], offdesign=['eta_s_char'])

        if self.sh is True:
            su.set_attr(pr1=0.99, pr2=0.99, ttd_u=2, design=['pr1', 'pr2', 'ttd_u'],
                        offdesign=['zeta1', 'zeta2', 'kA_char'])
        # compressor system

        cp1.set_attr(eta_s=self.etas_des, design=['eta_s'], offdesign=['eta_s_char'])

        if self.cmp_stages == 2:
            cp2.set_attr(eta_s=self.etas_des, pr=params_des['pr'], design=['eta_s'], offdesign=['eta_s_char'])

        if self.ic is True:
            he.set_attr(pr1=0.98, pr2=0.98, design=['pr1', 'pr2'],
                        offdesign=['zeta1', 'zeta2', 'kA_char'])
        # %% connection parametrization

        # condenser system

        c_in_cd.set_attr(p0=30, fluid={params_des['ref']: 1, 'water': 0,
                                       'air': 0}
                         )
        close_crp.set_attr(T=(self.LWC_des-5), p=1.5, fluid={params_des['ref']: 0, 'water': 1, 'air': 0},
                           offdesign=['m']
                           )
        cd_cons.set_attr(T=self.LWC_des, design=['T'])

        # evaporator system cold side

        erp_ev.set_attr(m=Ref(va_dr, 1.15, 0))

        # evaporator system hot side

        # pumping at constant rate in partload
        amb_in_apu.set_attr(T=self.heat_source_T_des, p=1,
                            fluid={params_des['ref']: 0, 'water': params_des['m_water'],
                                   'air': params_des['m_air']
                                   }
                            )
        if self.sh is True:
            apu_su.set_attr(p=1.0001)
        else:
            apu_ev.set_attr(p=1.0001)  # check this
        if self.ic is True:
            he_cp2.set_attr(T=(self.LWC_des-5), p0=10)
            ic_in_he.set_attr(p=1.5, T=7, fluid={'water': params_des['m_water'], params_des['ref']: 0,
                                                 'air': params_des['m_air']})
            he_ic_out.set_attr(T=(self.LWC_des-10), design=['T'])
        else:
            dr_cp1.set_attr(h0=400)

        if 'fixed_evap_m' in self.hp_model.lower():
            amb_in_apu.set_attr(m=params_des['evap_m'])
            dr_erp.set_attr(p0=params_des['ev_p0'])
            c_in_cd.set_attr(p0=params_des['cd_p0'])
            if not self.sh:
                dr_cp1.set_attr(h0=params_des['dr_h0'])
        else:
            ev_amb_out.set_attr(T=self.LFE_des)

        # %% key paramter
        cons.set_attr(Q=-self.heatload_des)

        # %% Calculation of the design condition
        self.nw.solve('design')
        # self.nw.print_results()
        self.nw.save('heat_pump')

    def p_cop_calc(self):
        """
        Calculates the power consumption and the COP of the heat pump in the 'detailed' calculation mode
        """
        self.P_cons = (self.nw.get_comp('compressor 1').P.val +
                       self.nw.get_comp('evaporator recirculation pump').P.val +
                       self.nw.get_comp('condenser recirculation pump').P.val +
                       self.nw.get_comp('ambient pump').P.val
                       )

        if self.cmp_stages == 2:
            self.P_cons += self.nw.get_comp('compressor 2').P.val

        self.COP = -self.nw.get_comp('consumer').Q.val / self.P_cons

        self.Q_evap = self.nw.get_comp('evaporator').Q.val

        if self.COP < 1 or self.COP > 20:
            self.step_error()

    def step(self, inputs):
        """
        Performs simulation step with the step size 'step_size'
        """
        self.skip_step = False
        self.on_fraction = 1

        # Inputs for the step
        heat_source_T = inputs.get('heat_source_T')
        if heat_source_T is not None:
            self.heat_source_T = heat_source_T

        T_amb = inputs.get('T_amb')
        if T_amb is not None:
            self.T_amb = T_amb

        cond_in_T = inputs.get('cond_in_T')
        if cond_in_T is not None:
            self.cond_in_T = cond_in_T

        Q_Demand = inputs.get('Q_Demand')
        if Q_Demand is not None:
            self.Q_Demand = Q_Demand
        else:
            self.Q_Demand = 0.0

        if self.Q_Demand <= 0:
            self.skip_step = True

        if (self.calc_mode != 'fixed') and (self.skip_step is not True):
            self._etas_heatload_id()

        if not self.skip_step:

            # 'hplib' calcuation mode - start
            if self.calc_mode == 'hplib':

                if self.Q_Demand < self.heatload_min:
                    # Forcing the heat pump to operate atleast at the minimum heating capacity
                    self.Q_Demand = self.heatload_min

                results = self.hp.simulate(t_in_primary=self.heat_source_T, t_in_secondary=self.cond_in_T,
                                           t_amb=self.T_amb, mode=1)
                self.cond_m = round(results['m_dot'], 2)
                self.COP = round(results['COP'], 2)
                self.P_cons = round(results['P_el'], 2)
                self.cons_T = round(results['T_out'], 2)
                self.Q_Supplied = round(results['P_th'], 2)
                if self.Q_Supplied > self.Q_Demand:
                    self.on_fraction = round(self.Q_Demand/self.Q_Supplied, 2)
                    self.Q_Supplied = self.Q_Demand
                    self.P_cons *= self.on_fraction
                    self.cond_m *= self.on_fraction
            # 'hplib' calcuation mode - end

            # 'fixed' calcuation mode - start
            elif self.calc_mode == 'fixed':

                self.COP = self.COP_fixed
                self.Q_Supplied = self.HC_fixed
                self.cond_m = self.cond_m_fixed
                self.P_cons = self.Q_Supplied/self.COP
                self.cons_T = self.cond_in_T + self.Q_Supplied / self.cond_m / 4184

                if self.Q_Supplied > self.Q_Demand:
                    self.on_fraction = round(self.Q_Demand / self.Q_Supplied, 2)
                    self.Q_Supplied = self.Q_Demand
                    self.P_cons *= self.on_fraction
                    self.cond_m *= self.on_fraction
            # 'fixed' calcuation mode - end

            else:

                # # Regulated operation of the heat pump
                # if self.Q_Demand < self.heatload_min:
                #     self.skip_step = True
                # elif self.Q_Demand > self.heatload_max:
                #     self.Q_Supplied = self.heatload_max
                #     Q_Demand_Excess = self.Q_Demand - self.Q_Supplied
                # else:
                #     self.Q_Supplied = self.Q_Demand
                #     Q_Supply_Excess = self.heatload_max - self.Q_Supplied

                # Conditions for always operating te heat pump at the maximum heating capacity for the conditions
                self.Q_Supplied = self.heatload_max

                if not self.skip_step:

                    # 'fast' calculation mode - start
                    if self.calc_mode == 'fast':
                        # Read the saved data from 'COP_m_data.json' file
                        heat_source_T_idx = str(self._take_closest(list(map(int, self.COP_m_data.keys())), self.heat_source_T))
                        cond_in_T_idx = str(self._take_closest(list(map(int, self.COP_m_data[heat_source_T_idx].keys())),
                                                               self.cond_in_T))
                        HL_idx = str(self._take_closest(list(map(float, self.COP_m_data[heat_source_T_idx][cond_in_T_idx].keys())),
                                                        self.Q_Supplied))
                        try:
                            self.cond_m = self.COP_m_data[heat_source_T_idx][cond_in_T_idx][HL_idx]['cond_m']
                            self.COP = self.COP_m_data[heat_source_T_idx][cond_in_T_idx][HL_idx]['COP']
                        except:
                            self.step_error()

                        if self.cond_m > 0:
                            self.cons_T = self.cond_in_T + self.Q_Supplied/self.cond_m/4184
                            if self.cons_T > self.cons_T_max:
                                self.cons_T = self.cons_T_max
                                self.Q_Supplied = self.cond_m * 4184 * (self.cons_T - self.cond_in_T)
                            self.P_cons = self.Q_Supplied/self.COP
                            self.Q_evap = -(self.Q_Supplied - self.P_cons -50)
                        else:
                            self.step_error()
                    # 'fast' calculation mode - end

                    # 'detailed' calculation mode - start
                    elif self.calc_mode == 'detailed':

                        # Solving the TESPy network in design mode for the closest design point
                        if self.id_old != self.idx:
                            try:
                                self._design_hp()
                            except:
                                self.step_error()
                            self.p_cop_calc()

                        # Solving the TESPy network in offdesign mode for the actual input conditions
                        if not self.skip_step:
                            self.nw.get_conn('source ambient:out1_ambient pump:in1').set_attr(T=self.heat_source_T)
                            self.nw.get_conn('consumer cycle closer:out1_condenser recirculation pump:in1').set_attr(T=self.cond_in_T)
                            if 'fixed_evap_m' not in self.hp_model.lower():
                                self.LFE = self.heat_source_T - 5
                                self.nw.get_conn('evaporator:out1_sink ambient:in1').set_attr(T=self.LFE)
                            self.nw.get_comp('consumer').set_attr(Q=-self.Q_Supplied)
                            try:
                                self.nw.solve('offdesign', design_path='heat_pump')
                                self.cond_m = self.nw.get_conn('condenser:out2_consumer:in1').m.val
                                self.cons_T = self.nw.get_conn('condenser:out2_consumer:in1').T.val
                                self.p_cop_calc()
                            except:
                                self.step_error()
                    # 'detailed' calculation mode - end

                else:
                    self.step_error()
        else:
            self.step_error()

    def step_error(self):
        """
        Sets the outputs of the heat pump model to 0
        """
        self.skip_step = True
        self.P_cons = 0
        self.COP = 0
        self.Q_Supplied = 0
        self.cond_m = 0
        self.cons_T = 0
        self.Q_evap = 0


