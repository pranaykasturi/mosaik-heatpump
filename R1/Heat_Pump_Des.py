from tespy.networks import network
from tespy.components import (
    sink, source, splitter, compressor, condenser, pump, heat_exchanger_simple,
    valve, drum, heat_exchanger, cycle_closer
)
from tespy.connections import connection, ref
from tespy.tools.characteristics import char_line
from tespy.tools.characteristics import load_default_char as ldc
from tespy.tools import logger
from bisect import bisect_left
import json
import logging
logger.define_logging(log_path=True, log_version=True,
                      screen_level=logging.ERROR,
                      file_level=logging.DEBUG)

class Heat_Pump_Des():

    def __init__(self, params):

        self.cons_Q = params['cons_Q']

        self.cons_T = params['cons_T']

        self.heat_source = params['heat_source']

        self.heat_source_T = params['heat_source_T']

        self.LWE = None
        self.LWC = None

        self.LWC_des = None
        self.LWE_des = None
        self.evap_T_des = None

        self.etas = None
        self.heatload = None

        self.idx = None
        self.nw = None

        # Finding the design point for the heat pump
        self.etas_heatload_id()

        # Designing the heat pump
        self.design_hp()

        # Calculating the Power & COP of the heat pump
        self.p_cop_calc()

    def take_closest(self, myList, myNumber):
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


    def etas_heatload_id(self):

        with open("data_file.json", "r") as read_file_1:
            data_1 = json.load(read_file_1)

        etas_dict = data_1['etas_list'][self.heat_source]
        heatload_dict = data_1['heatload_list'][self.heat_source]
        id_dict = data_1['id_list'][self.heat_source]

        if self.heat_source.lower() == 'air':
            self.evap_T_des = self.take_closest(list(map(int, etas_dict)), (self.heat_source_T))
            self.LWE_des = self.evap_T_des - 5
        else:
            self.evap_T_des = self.take_closest(list(map(int, etas_dict)), (self.heat_source_T - 5))
            self.LWE_des = self.evap_T_des

        self.LWC_des = self.take_closest(list(map(int, etas_dict[str(self.evap_T_des)])), self.cons_T)

        self.etas = etas_dict[str(self.evap_T_des)][str(self.LWC_des)]
        self.heatload = heatload_dict[str(self.evap_T_des)][str(self.LWC_des)]
        self.idx = id_dict[str(self.evap_T_des)][str(self.LWC_des)]

    # Method to design the heat pump
    def design_hp(self):

        # The parameters that will vary for the different heat pump models are defined here
        if self.heat_source.lower() == 'air':
            params_des = {'m_R410a': 1, 'm_air': 1, 'm_R407c': 0, 'm_water': 0,
                      'ttd_u': 14, 'amb_temp': self.evap_T_des, 'amb_m': None, 'amb_p': 1,
                          }
        elif self.heat_source.lower() == 'water':
            params_des = {'m_R410a': 0, 'm_air': 0, 'm_R407c': 1, 'm_water': 1,
                      'ttd_u': 23, 'amb_m': 0.61, 'amb_p': 1,
                          }

        self.nw = network(
            fluids=['R407c', 'R410a', 'water', 'air'], T_unit='C', p_unit='bar', h_unit='kJ / kg',
            m_unit='kg / s'
        )

        self.nw.set_attr(iterinfo=False)

        # %% components

        # sources & sinks
        cc = cycle_closer('coolant cycle closer')
        cons_closer = cycle_closer('consumer cycle closer')
        amb_in = source('source ambient')
        amb_out = sink('sink ambient')

        # ambient air system
        apu = pump('ambient pump')

        # consumer system

        cd = condenser('condenser')
        crp = pump('condenser recirculation pump')
        cons = heat_exchanger_simple('consumer')

        # evaporator system

        va = valve('valve')
        dr = drum('drum')
        ev = heat_exchanger('evaporator')
        erp = pump('evaporator recirculation pump')

        # compressor-system

        cp = compressor('compressor')

        # %% connections

        # consumer system

        c_in_cd = connection(cc, 'out1', cd, 'in1')
        close_crp = connection(cons_closer, 'out1', crp, 'in1')
        crp_cd = connection(crp, 'out1', cd, 'in2')
        cd_cons = connection(cd, 'out2', cons, 'in1')
        cons_close = connection(cons, 'out1', cons_closer, 'in1')


        self.nw.add_conns(c_in_cd, close_crp, crp_cd, cd_cons, cons_close)

        # connection condenser - evaporator system

        cd_va = connection(cd, 'out1', va, 'in1')

        self.nw.add_conns(cd_va)

        # evaporator system

        va_dr = connection(va, 'out1', dr, 'in1')
        dr_erp = connection(dr, 'out1', erp, 'in1')
        erp_ev = connection(erp, 'out1', ev, 'in2')
        ev_dr = connection(ev, 'out2', dr, 'in2')
        dr_cp = connection(dr, 'out2', cp, 'in1')
        cp_cc = connection(cp, 'out1', cc, 'in1')

        self.nw.add_conns(va_dr, dr_erp, erp_ev, ev_dr, dr_cp, cp_cc)

        amb_in_apu = connection(amb_in, 'out1', apu, 'in1')
        apu_ev = connection(apu, 'out1', ev, 'in1')
        ev_amb_out = connection(ev, 'out1', amb_out, 'in1')

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

        kA_char1 = ldc('heat exchanger', 'kA_char1', 'DEFAULT', char_line)
        kA_char2 = ldc('heat exchanger', 'kA_char2', 'EVAPORATING FLUID', char_line)

        ev.set_attr(pr1=0.98, pr2=0.99, ttd_l=2,
                    kA_char1=kA_char1, kA_char2=kA_char2,
                    design=['pr1', 'ttd_l'], offdesign=['zeta1', 'kA_char'])
        erp.set_attr(eta_s=0.8, design=['eta_s'], offdesign=['eta_s_char'])
        apu.set_attr(eta_s=0.8, design=['eta_s'], offdesign=['eta_s_char'])

        # compressor system

        cp.set_attr(eta_s=self.etas, design=['eta_s'], offdesign=['eta_s_char'])

        # %% connection parametrization

        # condenser system

        c_in_cd.set_attr(p0=15, fluid={'R407c': params_des['m_R407c'], 'water': 0, 'air': 0,
                                       'R410a': params_des['m_R410a']}
                         )
        close_crp.set_attr(T=(self.LWC_des-5), p=2, fluid={'R407c': 0, 'R410a': 0, 'water': 1, 'air': 0}, design=['T'],
                           offdesign=['m'])
        cd_cons.set_attr(T=self.LWC_des)

        # evaporator system cold side

        erp_ev.set_attr(m=ref(va_dr, 1.25, 0), p0=6.5)

        # evaporator system hot side

        # pumping at constant rate in partload
        if params_des['amb_m'] is not None:
            amb_in_apu.set_attr(p=params_des['amb_p'], m=params_des['amb_m'],
                                fluid={'R407c': 0, 'R410a': 0, 'water': params_des['m_water'],
                                       'air': params_des['m_air']}
                                )
        else:
            amb_in_apu.set_attr(T=params_des['amb_temp'], p=params_des['amb_p'],
                                fluid={'R407c': 0, 'R410a': 0, 'water': params_des['m_water'],
                                       'air': params_des['m_air']}
                                )
        apu_ev.set_attr(p=1.1)
        ev_amb_out.set_attr(T=self.LWE_des, design=['T'])
        dr_cp.set_attr(p0=6.5, h0=400)

        # %% key paramter

        cons.set_attr(Q=-self.heatload*1000)

        # %% Calculation of the design condition

        self.nw.solve('design')
        # # nw.print_results()
        self.nw.save('heat_pump')

        # %% Calculation of the off-design condition for the timestep

        # if self.heat_source.lower() == 'air':
        self.nw.connections['source ambient:out1_ambient pump:in1'].set_attr(T=self.heat_source_T)

        self.LWE = self.heat_source_T - 5
        self.nw.connections['evaporator:out1_sink ambient:in1'].set_attr(T=self.LWE)

        self.nw.connections['condenser:out2_consumer:in1'].set_attr(T=self.cons_T)

        self.nw.components['consumer'].set_attr(Q=-self.cons_Q)

        self.nw.solve('offdesign', design_path='heat_pump')

    def p_cop_calc(self):

        self.P_cons = (self.nw.components['compressor'].P.val +
                       self.nw.components['evaporator recirculation pump'].P.val +
                       self.nw.components['condenser recirculation pump'].P.val +
                       self.nw.components['ambient pump'].P.val)
        self.COP = -self.nw.components['consumer'].Q.val / self.P_cons

    def step(self, inputs):

        heat_source_T = inputs.get('heat_source_T')
        if heat_source_T is not None:
            self.heat_source_T = heat_source_T

        cons_T = inputs.get('cons_T')
        if cons_T is not None:
            self.cons_T = cons_T

        cons_Q = inputs.get('cons_Q')
        if cons_Q is not None:
            self.cons_Q = cons_Q

        id_old = self.idx

        self.etas_heatload_id()

        if id_old != self.idx:
            self.design_hp()
        else:
            self.nw.connections['source ambient:out1_ambient pump:in1'].set_attr(T=self.heat_source_T)
            self.nw.connections['condenser:out2_consumer:in1'].set_attr(T=self.cons_T)
            self.LWE = self.heat_source_T - 5
            self.nw.connections['evaporator:out1_sink ambient:in1'].set_attr(T=self.LWE)
            self.nw.components['consumer'].set_attr(Q=-self.cons_Q)
            self.nw.solve('offdesign', design_path='heat_pump')

        self.p_cop_calc()

        return self.P_cons/1000, self.COP


if __name__ == '__main__':

    params = {
        'cons_Q': 16700,
        'heat_source': 'water',
        'heat_source_T': 12,
        'cons_T': 35,
    }

    heat_pump_1 = Heat_Pump_Des(params)
    #
    print('P : ', heat_pump_1.P_cons)
    print('COP : ', heat_pump_1.COP)
    #
    inputs = {'heat_source_T': 9, 'cons_Q': 15900, 'cons_T': 30}
    # inputs = {'amb_T': 13.7, 'cons_Q': 3845.051}
    # #
    heat_pump_1.step(inputs)
    print('P : ', heat_pump_1.P_cons)
    print('COP : ', heat_pump_1.COP)

    # heat_source_2 = 'air'
    # heat_pump_2 = Heat_Pump_Des(heat_source_2)
    #
    # print('P : ', heat_pump_2.P_cons)
    # print('COP : ', heat_pump_2.COP)
    # heat_pump_1.nw.print_results()

    # inputs = {'amb_T': 6, 'cons_Q': 14500}
    #
    # heat_pump_2.step(inputs)
    # print('P : ', heat_pump_2.P_cons)
    # print('COP : ', heat_pump_2.COP)
