from tespy.networks import network
from tespy.components import (
    sink, source, splitter, compressor, condenser, pump, heat_exchanger_simple,
    valve, drum, heat_exchanger, cycle_closer
)
from tespy.connections import connection, ref
from tespy.tools.characteristics import char_line
from tespy.tools.characteristics import load_default_char as ldc

import numpy as np
import pandas as pd

class Heat_Pump_Des():

    def __init__(self, params):
        self.cd_cons_temp = params['cd_cons_temp']
        self.cb_dhp_temp = params['cb_dhp_temp']
        self.amb_p_temp = params['amb_p_temp']
        self.amb_p_pres = params['amb_p_pres']
        self.ev_amb_out_temp = params['ev_amb_out_temp']
        self.ev_amb_out_pres = params['ev_amb_out_pres']
        self.cons_Q = params['cons_Q']
        self.ic_out_temp = params['ic_out_temp']

        self.design_hp()

        self.P_cons = (self.nw.components['compressor 1'].P.val +
                      self.nw.components['compressor 2'].P.val +
                      self.nw.components['evaporator recirculation pump'].P.val +
                      self.nw.components['pump'].P.val)
        self.COP = params['cons_Q']/self.P_cons

    def design_hp(self):

        self.nw = network(
            fluids=['water', 'NH3', 'air'], T_unit='C', p_unit='bar', h_unit='kJ / kg',
            m_unit='kg / s'
        )

        self.nw.set_attr(iterinfo=False)

        # %% components

        # sources & sinks
        cc = cycle_closer('coolant cycle closer')
        cb = source('consumer back flow')
        cf = sink('consumer feed flow')
        amb = source('ambient air')
        amb_out1 = sink('sink ambient 1')
        amb_out2 = sink('sink ambient 2')

        # ambient air system
        sp = splitter('splitter')
        pu = pump('pump')

        # consumer system

        cd = condenser('condenser')
        dhp = pump('district heating pump')
        cons = heat_exchanger_simple('consumer')

        # evaporator system

        ves = valve('valve')
        dr = drum('drum')
        ev = heat_exchanger('evaporator')
        su = heat_exchanger('superheater')
        erp = pump('evaporator recirculation pump')

        # compressor-system

        cp1 = compressor('compressor 1')
        cp2 = compressor('compressor 2')
        ic = heat_exchanger('intercooler')

        # %% connections

        # consumer system

        c_in_cd = connection(cc, 'out1', cd, 'in1')

        cb_dhp = connection(cb, 'out1', dhp, 'in1')
        dhp_cd = connection(dhp, 'out1', cd, 'in2')
        cd_cons = connection(cd, 'out2', cons, 'in1')
        cons_cf = connection(cons, 'out1', cf, 'in1')

        self.nw.add_conns(c_in_cd, cb_dhp, dhp_cd, cd_cons, cons_cf)

        # connection condenser - evaporator system

        cd_ves = connection(cd, 'out1', ves, 'in1')

        self.nw.add_conns(cd_ves)

        # evaporator system

        ves_dr = connection(ves, 'out1', dr, 'in1')
        dr_erp = connection(dr, 'out1', erp, 'in1')
        erp_ev = connection(erp, 'out1', ev, 'in2')
        ev_dr = connection(ev, 'out2', dr, 'in2')
        dr_su = connection(dr, 'out2', su, 'in2')

        self.nw.add_conns(ves_dr, dr_erp, erp_ev, ev_dr, dr_su)

        amb_p = connection(amb, 'out1', pu, 'in1')
        p_sp = connection(pu, 'out1', sp, 'in1')
        sp_su = connection(sp, 'out1', su, 'in1')
        su_ev = connection(su, 'out1', ev, 'in1')
        ev_amb_out = connection(ev, 'out1', amb_out1, 'in1')

        self.nw.add_conns(amb_p, p_sp, sp_su, su_ev, ev_amb_out)

        # connection evaporator system - compressor system

        su_cp1 = connection(su, 'out2', cp1, 'in1')

        self.nw.add_conns(su_cp1)

        # compressor-system

        cp1_he = connection(cp1, 'out1', ic, 'in1')
        he_cp2 = connection(ic, 'out1', cp2, 'in1')
        cp2_c_out = connection(cp2, 'out1', cc, 'in1')

        sp_ic = connection(sp, 'out2', ic, 'in2')
        ic_out = connection(ic, 'out2', amb_out2, 'in1')

        self.nw.add_conns(cp1_he, he_cp2, sp_ic, ic_out, cp2_c_out)

        # %% component parametrization

        # condenser system

        cd.set_attr(pr1=0.99, pr2=0.99, ttd_u=5, design=['pr2', 'ttd_u'],
                    offdesign=['zeta2', 'kA_char'])
        dhp.set_attr(eta_s=0.8, design=['eta_s'], offdesign=['eta_s_char'])
        cons.set_attr(pr=0.99, design=['pr'], offdesign=['zeta'])

        # water pump

        pu.set_attr(eta_s=0.75, design=['eta_s'], offdesign=['eta_s_char'])

        # evaporator system

        kA_char1 = ldc('heat exchanger', 'kA_char1', 'DEFAULT', char_line)
        kA_char2 = ldc('heat exchanger', 'kA_char2', 'EVAPORATING FLUID', char_line)

        ev.set_attr(pr1=0.98, pr2=0.99, ttd_l=5,
                    kA_char1=kA_char1, kA_char2=kA_char2,
                    design=['pr1', 'ttd_l'], offdesign=['zeta1', 'kA_char'])
        su.set_attr(pr1=0.98, pr2=0.99, ttd_u=2, design=['pr1', 'pr2', 'ttd_u'],
                    offdesign=['zeta1', 'zeta2', 'kA_char'])
        erp.set_attr(eta_s=0.8, design=['eta_s'], offdesign=['eta_s_char'])

        # compressor system

        cp1.set_attr(eta_s=0.85, design=['eta_s'], offdesign=['eta_s_char'])
        cp2.set_attr(eta_s=0.9, pr=3, design=['eta_s'], offdesign=['eta_s_char'])
        ic.set_attr(pr1=0.99, pr2=0.98, design=['pr1', 'pr2'],
                    offdesign=['zeta1', 'zeta2', 'kA_char'])

        # %% connection parametrization

        # condenser system

        c_in_cd.set_attr(fluid={'air': 0, 'NH3': 1, 'water': 0})
        cb_dhp.set_attr(T=self.cb_dhp_temp, p=10, fluid={'air': 0, 'NH3': 0, 'water': 1})
        cd_cons.set_attr(T=self.cd_cons_temp)
        cons_cf.set_attr(h=ref(cb_dhp, 1, 0), p=ref(cb_dhp, 1, 0))

        # evaporator system cold side

        erp_ev.set_attr(m=ref(ves_dr, 1.25, 0), p0=5)
        su_cp1.set_attr(p0=5, state='g')

        # evaporator system hot side

        # pumping at constant rate in partload
        amb_p.set_attr(T=self.amb_p_temp, p=self.amb_p_pres, fluid={'air': 0, 'NH3': 0, 'water': 1},
                       offdesign=['v'])
        sp_su.set_attr(offdesign=['v'])
        ev_amb_out.set_attr(p=self.ev_amb_out_pres, T=self.ev_amb_out_temp, design=['T'])

        # compressor-system

        he_cp2.set_attr(Td_bp=5, p0=20, design=['Td_bp'])
        ic_out.set_attr(T=self.ic_out_temp, design=['T'])

        # %% key paramter

        cons.set_attr(Q=-self.cons_Q)

        # %% Calculation

        self.nw.solve('design')
        # nw.print_results()
        self.nw.save('heat_pump')



    def step(self, inputs):
        self.nw.connections['ambient air:out1_pump:in1'].set_attr(T=inputs['amb_T'])
        self.nw.components['consumer'].set_attr(Q=-inputs['cons_Q'])
        self.nw.solve('offdesign', design_path='heat_pump')
        self.P_cons = (self.nw.components['compressor 1'].P.val +
                       self.nw.components['compressor 2'].P.val +
                       self.nw.components['evaporator recirculation pump'].P.val +
                       self.nw.components['pump'].P.val)
        self.COP = inputs['cons_Q']/self.P_cons

        return self.P_cons, self.COP


if __name__ == '__main__':
    params = {'cd_cons_temp': 90,
              'cb_dhp_temp': 60,
              'amb_p_temp': 12,
              'amb_p_pres': 2,
              'ev_amb_out_temp': 9,
              'ev_amb_out_pres': 2,
              'cons_Q': 200e3,
              'ic_out_temp': 30
              }
    heat_pump_1 = Heat_Pump_Des(params)

    print('P : ', heat_pump_1.P_cons)
    print('COP : ', heat_pump_1.COP)

    inputs = {'amb_T': 24, 'cons_Q': 120e3}

    heat_pump_1.step(inputs)
    print('P : ', heat_pump_1.P_cons)
    print('COP : ', heat_pump_1.COP)
