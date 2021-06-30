from tespy.networks import Network
from tespy.components import (
    Sink, Source, Compressor, Condenser, Pump, HeatExchangerSimple,
    Valve, Drum, HeatExchanger, CycleCloser
)
from tespy.connections import Connection, Ref
from tespy.tools.characteristics import CharLine
from tespy.tools.characteristics import load_default_char as ldc
from tespy.tools import logger
from bisect import bisect_left
import json
import os
import logging
# logging.basicConfig(level=logging.ERROR)
# logger.define_logging(log_path=True, log_version=True,
#                       screen_level=logging.ERROR,
#                       file_level=logging.DEBUG)
JSON_DATA_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data_file.json'))


class Heat_Pump_Des():

    def __init__(self, params, COP_m_data):

        self.Q_Demand = params.get('Q_Demand')

        self.cons_T = params.get('cons_T', None)

        self.cond_in_T = params.get('cond_in_T')
        # self.cond_in_T = self.cons_T - 5

        self.heat_source = params['heat_source']

        self.heat_source_T = params.get('heat_source_T', None)

        self.LWE = None
        self.LWC = None

        self.LWC_des = None
        self.LWE_des = None
        self.heat_source_T_des = None

        self.etas_des = None
        self.heatload_des = None

        self.idx = None
        self.nw = None

        self.skip_step = False

        self.Q_Supplied = None

        self.cond_m = None

        self.calc_mode = params.get('calc_mode')

        self.COP_m_data = COP_m_data



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
        with open(JSON_DATA_FILE, "r") as read_file_1:
            data_1 = json.load(read_file_1)

        etas_dict = data_1['etas_list'][self.heat_source]
        heatload_dict = data_1['heatload_list'][self.heat_source]
        id_dict = data_1['id_list'][self.heat_source]

        heat_source_T_min = min(list(map(int, etas_dict)))
        heat_source_T_max = max(list(map(int, etas_dict)))

        if self.heat_source.lower() == 'air':
            if heat_source_T_min <= self.heat_source_T <= heat_source_T_max:
                idx_T = self._take_closest(list(map(int, etas_dict)), (self.heat_source_T))
                self.heat_source_T_des = idx_T
                self.LWE_des = self.heat_source_T_des - 5
            else:
                self.skip_step = True
        else:
            if heat_source_T_min <= (self.heat_source_T-5) <= heat_source_T_max:
                idx_T = self._take_closest(list(map(int, etas_dict)), (self.heat_source_T - 5))
                self.LWE_des = idx_T
                self.heat_source_T_des = self.LWE_des + 5
            else:
                self.skip_step = True

        cons_T_min = min(list(map(int, etas_dict[str(idx_T)])))
        cons_T_max = max(list(map(int, etas_dict[str(idx_T)])))

        cons_T_des = self.cond_in_T + 5

        if cons_T_des < cons_T_min or cons_T_des > cons_T_max:
            self.skip_step = True

        self.LWC_des = self._take_closest(list(map(int, etas_dict[str(idx_T)])), cons_T_des)

        self.etas_des = etas_dict[str(idx_T)][str(self.LWC_des)]

        self.heatload_des = heatload_dict[str(idx_T)][str(self.LWC_des)] * 1000

        self.heatload_max = self.heatload_des
        self.heatload_min = 5000
        self.idx = id_dict[str(idx_T)][str(self.LWC_des)]



    # Method to design the heat pump
    def _design_hp(self):

        # The parameters that will vary for the different heat pump models are defined here
        if self.heat_source.lower() == 'air':
            params_des = {'m_R410a': 1, 'm_air': 1, 'm_R407c': 0, 'm_water': 0,
                          'ttd_u': 15, 'amb_p': 1
                          }
        elif self.heat_source.lower() == 'water':
            params_des = {'m_R410a': 0, 'm_air': 0, 'm_R407c': 1, 'm_water': 1,
                          'ttd_u': 23, 'amb_p': 1
                          }

        self.nw = Network(
            fluids=['R407c', 'R410a', 'water', 'air'], T_unit='C', p_unit='bar',
            h_unit='kJ / kg', m_unit='kg / s'
        )

        self.nw.set_attr(iterinfo=False)

        # %% components

        # sources & sinks
        cc = CycleCloser('coolant cycle closer')
        cons_closer = CycleCloser('consumer cycle closer')
        amb_in = Source('source ambient')
        amb_out = Sink('sink ambient')

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

        # compressor-system

        cp = Compressor('compressor')

        # %% connections

        # consumer system

        c_in_cd = Connection(cc, 'out1', cd, 'in1')
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
        dr_cp = Connection(dr, 'out2', cp, 'in1')
        cp_cc = Connection(cp, 'out1', cc, 'in1')

        self.nw.add_conns(va_dr, dr_erp, erp_ev, ev_dr, dr_cp, cp_cc)

        amb_in_apu = Connection(amb_in, 'out1', apu, 'in1')
        apu_ev = Connection(apu, 'out1', ev, 'in1')
        ev_amb_out = Connection(ev, 'out1', amb_out, 'in1')

        self.nw.add_conns(amb_in_apu, apu_ev, ev_amb_out)

        # connection evaporator system - compressor system

        # compressor-system

        # %% component parametrization

        # condenser system

        cd.set_attr(pr1=0.99, pr2=0.99, ttd_u=params_des['ttd_u'], design=['pr2', 'ttd_u'],
                    offdesign=['zeta2', 'kA_char'])

        crp.set_attr(eta_s=0.8, design=['eta_s'], offdesign=['eta_s_char'])
        cons.set_attr(pr=0.99, design=['pr'], offdesign=['zeta'])

        # evaporator system

        kA_char1 = ldc('heat exchanger', 'kA_char1', 'DEFAULT', CharLine)
        kA_char2 = ldc('heat exchanger', 'kA_char2', 'EVAPORATING FLUID', CharLine)

        ev.set_attr(pr1=0.99, pr2=0.99, ttd_l=2,
                    kA_char1=kA_char1, kA_char2=kA_char2,
                    design=['pr1', 'ttd_l'], offdesign=['zeta1', 'kA_char'])
        erp.set_attr(eta_s=0.8, design=['eta_s'], offdesign=['eta_s_char'])
        apu.set_attr(eta_s=0.8, design=['eta_s'], offdesign=['eta_s_char'])

        # compressor system

        cp.set_attr(eta_s=self.etas_des, design=['eta_s'], offdesign=['eta_s_char'])

        # %% connection parametrization

        # condenser system

        c_in_cd.set_attr(p0=30, fluid={'R407c': params_des['m_R407c'], 'water': 0, 'air': 0,
                                       'R410a': params_des['m_R410a']
                                       }
                         )
        close_crp.set_attr(T=(self.LWC_des-5), p=2, fluid={'R407c': 0, 'R410a': 0, 'water': 1, 'air': 0},
                           offdesign=['m']
                           )
        cd_cons.set_attr(T=self.LWC_des, design=['T'])

        # evaporator system cold side

        erp_ev.set_attr(m=Ref(va_dr, 1.15, 0), p0=6.5)

        # evaporator system hot side

        # pumping at constant rate in partload
        amb_in_apu.set_attr(T=self.heat_source_T_des, p=params_des['amb_p'],
                            fluid={'R407c': 0, 'R410a': 0, 'water': params_des['m_water'],
                                   'air': params_des['m_air']
                                   }
                            )

        apu_ev.set_attr(p=1.0001)  # check this
        # ev_amb_out.set_attr(T=self.LWE_des, design=['T'])
        ev_amb_out.set_attr(T=self.LWE_des)
        dr_cp.set_attr(p0=6.5, h0=400)

        # %% key paramter

        cons.set_attr(Q=-self.heatload_des)

        # %% Calculation of the design condition


        self.nw.solve('design')
        # self.nw.print_results()
        self.nw.save('heat_pump')

    def p_cop_calc(self):

        self.P_cons = (self.nw.get_comp('compressor').P.val +
                       self.nw.get_comp('evaporator recirculation pump').P.val +
                       self.nw.get_comp('condenser recirculation pump').P.val +
                       self.nw.get_comp('ambient pump').P.val
                       )

        self.COP = -self.nw.get_comp('consumer').Q.val / self.P_cons

        if self.COP < 1 or self.COP > 6:
            self.step_error()

    def step(self, inputs):

        self.skip_step = False

        heat_source_T = inputs.get('heat_source_T')
        if heat_source_T is not None:
            self.heat_source_T = heat_source_T

        cond_in_T = inputs.get('cond_in_T')
        if cond_in_T is not None:
            self.cond_in_T = cond_in_T

        Q_Demand = inputs.get('Q_Demand')
        if Q_Demand is not None:
            self.Q_Demand = Q_Demand

        id_old = self.idx

        if self.calc_mode == 'fixed':
            self.heatload_min = 5000
            self.heatload_max = 11040
        else:
            self._etas_heatload_id()

        if self.Q_Demand < self.heatload_min:
            self.skip_step = True
        elif self.Q_Demand > self.heatload_max:
            self.Q_Supplied = self.heatload_max
            Q_Demand_Excess = self.Q_Demand - self.Q_Supplied
        else:
            self.Q_Supplied = self.Q_Demand
            Q_Supply_Excess = self.heatload_max - self.Q_Supplied

        if not self.skip_step:

            if self.calc_mode == 'fast':
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
                    self.P_cons = self.Q_Supplied/self.COP
                else:
                    self.step_error()

            elif self.calc_mode == 'fixed':

                self.cond_m = 0.52
                self.COP = 2
                self.cons_T = self.cond_in_T + self.Q_Supplied/self.cond_m/4184
                self.P_cons = self.Q_Supplied/self.COP

            elif self.calc_mode == 'detailed':

                if id_old != self.idx:
                    try:
                        self._design_hp()
                    except:
                        self.step_error()

                if not self.skip_step:
                    self.nw.get_conn('source ambient:out1_ambient pump:in1').set_attr(T=self.heat_source_T)
                    self.nw.get_conn('consumer cycle closer:out1_condenser recirculation pump:in1').set_attr(T=self.cond_in_T)
                    self.LWE = self.heat_source_T - 5
                    self.nw.get_conn('evaporator:out1_sink ambient:in1').set_attr(T=self.LWE)
                    self.nw.get_comp('consumer').set_attr(Q=-self.Q_Supplied)
                    try:
                        self.nw.solve('offdesign', design_path='heat_pump')
                        self.cond_m = self.nw.get_conn('condenser:out2_consumer:in1').m.val
                        self.cons_T = self.nw.get_conn('condenser:out2_consumer:in1').T.val
                        self.p_cop_calc()
                    except:
                        self.step_error()

        else:
            self.step_error()

    def step_error(self):
        self.skip_step = True
        self.P_cons = 0
        self.COP = 0
        self.Q_Supplied = 0
        self.cond_m = 0
        self.cons_T = 0




if __name__ == '__main__':

    params_air = {
        'heat_source': 'air',
        'heat_source_T': 7,
        'cons_T': 35,
        'calc_mode': 'detailed'
    }

    heat_pump_1 = Heat_Pump_Des(params_air, COP_m_data=None)

    inputs_air_1 = {'heat_source_T': 2, 'Q_Demand': 11040, 'cond_in_T': 45}

    heat_pump_1.step(inputs_air_1)

    print('P : ', heat_pump_1.P_cons)
    print('COP : ', heat_pump_1.COP)
    print('cond_m :',  heat_pump_1.cond_m)
    # print('cond_m : ', heat_pump_1.nw.get_conn('condenser:out2_consumer:in1').m.val)

    # inputs_air_2 = {'heat_source_T': 7, 'Q_Demand': 15220, 'cons_T': 45}
    #
    # heat_pump_1.step(inputs_air_2)
    # print('P : ', heat_pump_1.P_cons)
    # print('COP : ', heat_pump_1.COP)
    # # print('cond_m : ', heat_pump_1.nw.get_conn('condenser:out2_consumer:in1').m.val)
    #
    # params_water = {
    #     'heat_source': 'water',
    #     'heat_source_T': 12,
    #     'cons_T': 35,
    # }
    #
    # heat_pump_2 = Heat_Pump_Des(params_water)
    # inputs_water_1 = {'heat_source_T': 12, 'Q_Demand': 16700, 'cons_T': 35}
    #
    # heat_pump_2.step(inputs_water_1)
    # print('P : ', heat_pump_2.P_cons)
    # print('COP : ', heat_pump_2.COP)
    #
    # inputs_water_2 = {'heat_source_T': 9, 'Q_Demand': 15900, 'cons_T': 30}
    #
    # heat_pump_2.step(inputs_water_2)
    # print('P : ', heat_pump_2.P_cons)
    # print('COP : ', heat_pump_2.COP)
