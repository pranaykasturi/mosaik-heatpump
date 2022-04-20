# -*- coding: utf-8 -*-

from tespy.components import Compressor
from tespy.components import Condenser
from tespy.components import CycleCloser
from tespy.components import Drum
from tespy.components import HeatExchanger
from tespy.components import HeatExchangerSimple
from tespy.components import Pump
from tespy.components import Sink
from tespy.components import Source
from tespy.components import Valve
from tespy.connections import Connection
from tespy.connections import Ref
from tespy.networks import Network
from tespy.tools.characteristics import CharLine
from tespy.tools.characteristics import load_default_char as ldc


cond_in_T = 30
T_amb = 7
Q = -60.1e3
# %% network

nw = Network(fluids=['water', 'R22', 'air'], T_unit='C', p_unit='bar',
             h_unit='kJ / kg', m_unit='kg / s')

# %% components

# sources & sinks

cool_closer = CycleCloser('coolant cycle closer')
cons_closer = CycleCloser('consumer cycle closer')

amb_in = Source('source ambient')
amb_out = Sink('sink ambient')

ic_in = Source('source intercool')
ic_out = Sink('sink intercool')

# consumer system

cd = Condenser('condenser')
rp = Pump('recirculation pump')
cons = HeatExchangerSimple('consumer')

# evaporator system

va = Valve('valve')
dr = Drum('drum')
ev = HeatExchanger('evaporator')
su = HeatExchanger('superheater')
pu = Pump('pump evaporator')

# compressor-system

cp1 = Compressor('compressor 1')
cp2 = Compressor('compressor 2')
he = HeatExchanger('intercooler')

apu = Pump('ambient pump')

# %% connections

# consumer system

c_in_cd = Connection(cool_closer, 'out1', cd, 'in1')
close_rp = Connection(cons_closer, 'out1', rp, 'in1')
rp_cd = Connection(rp, 'out1', cd, 'in2')
cd_cons = Connection(cd, 'out2', cons, 'in1')
cons_close = Connection(cons, 'out1', cons_closer, 'in1')

nw.add_conns(c_in_cd, close_rp, rp_cd, cd_cons, cons_close)

# connection condenser - evaporator system

cd_va = Connection(cd, 'out1', va, 'in1')

nw.add_conns(cd_va)

# evaporator system

va_dr = Connection(va, 'out1', dr, 'in1')
dr_pu = Connection(dr, 'out1', pu, 'in1')
pu_ev = Connection(pu, 'out1', ev, 'in2')
ev_dr = Connection(ev, 'out2', dr, 'in2')
dr_su = Connection(dr, 'out2', su, 'in2')

nw.add_conns(va_dr, dr_pu, pu_ev, ev_dr, dr_su)

amb_in_apu = Connection(amb_in, 'out1', apu, 'in1')
apu_su = Connection(apu, 'out1', su, 'in1')
su_ev = Connection(su, 'out1', ev, 'in1')
ev_amb_out = Connection(ev, 'out1', amb_out, 'in1')

nw.add_conns(amb_in_apu, apu_su, su_ev, ev_amb_out)

# connection evaporator system - compressor system

su_cp1 = Connection(su, 'out2', cp1, 'in1')

nw.add_conns(su_cp1)

# compressor-system

cp1_he = Connection(cp1, 'out1', he, 'in1')
he_cp2 = Connection(he, 'out1', cp2, 'in1')
cp2_close = Connection(cp2, 'out1', cool_closer, 'in1')

ic_in_he = Connection(ic_in, 'out1', he, 'in2')
he_ic_out = Connection(he, 'out2', ic_out, 'in1')

nw.add_conns(cp1_he, he_cp2, ic_in_he, he_ic_out, cp2_close)

# %% component parametrization

# condenser system

cd.set_attr(pr1=0.99, pr2=0.99, ttd_u=15, design=['pr2', 'ttd_u'],
            offdesign=['zeta2', 'kA_char'])
rp.set_attr(eta_s=0.8, design=['eta_s'], offdesign=['eta_s_char'])
cons.set_attr(pr=0.99, design=['pr'], offdesign=['zeta'])

# evaporator system

kA_char1 = ldc('heat exchanger', 'kA_char1', 'DEFAULT', CharLine)
kA_char2 = ldc('heat exchanger', 'kA_char2', 'EVAPORATING FLUID', CharLine)

ev.set_attr(pr1=0.99, pr2=0.99, ttd_l=2,
            kA_char1=kA_char1, kA_char2=kA_char2,
            design=['pr1', 'ttd_l'], offdesign=['zeta1', 'kA_char'])
su.set_attr(pr1=0.99, pr2=0.99, ttd_u=2, design=['pr1', 'pr2', 'ttd_u'],
            offdesign=['zeta1', 'zeta2', 'kA_char'])
pu.set_attr(eta_s=0.8, design=['eta_s'], offdesign=['eta_s_char'])
apu.set_attr(eta_s=0.8, design=['eta_s'], offdesign=['eta_s_char'])

# compressor system

cp1.set_attr(eta_s=0.8, design=['eta_s'], offdesign=['eta_s_char'])
cp2.set_attr(eta_s=0.8, pr=2, design=['eta_s'], offdesign=['eta_s_char'])

he.set_attr(pr1=0.98, pr2=0.98, design=['pr1', 'pr2'],
            offdesign=['zeta1', 'zeta2', 'kA_char'])

# %% connection parametrization

# condenser system

c_in_cd.set_attr(p0=15, fluid={'water': 0, 'R22': 1, 'air': 0})
close_rp.set_attr(T=cond_in_T, p=1.5, fluid={'water': 1, 'R22': 0, 'air': 0}, offdesign=['m'])
cd_cons.set_attr(T=cond_in_T+5, design=['T'])

# evaporator system cold side

pu_ev.set_attr(m=Ref(va_dr, 1.15, 0), p0=6)
su_cp1.set_attr(state='g')

# evaporator system hot side

amb_in_apu.set_attr(T=T_amb, p=1, fluid={'water': 0, 'R22': 0, 'air': 1})
apu_su.set_attr(p=1.0001)
ev_amb_out.set_attr(T=Ref(amb_in_apu, 1, -5))

he_cp2.set_attr(T=Ref(close_rp, 1, 0), p0=8) #, design=['T']
ic_in_he.set_attr(p=1.5, T=T_amb, fluid={'water': 0, 'R22': 0, 'air': 1})
he_ic_out.set_attr(T=cond_in_T-5, design=['T'])

# %% key paramter

cons.set_attr(Q=Q)

# %% Calculation

nw.solve('design')
# alternatively use:
# nw.solve('design', init_path='condenser_eva')
nw.print_results()
nw.save('heat_pump')


cond_in_T = 30
T_amb = 8
Q = -48.5e3
nw.get_conn('source ambient:out1_ambient pump:in1').set_attr(T=T_amb)
nw.get_conn('consumer cycle closer:out1_recirculation pump:in1').set_attr(T=cond_in_T)
LWE = T_amb - 5
# nw.get_conn('evaporator:out1_sink ambient:in1').set_attr(T=LWE)
nw.get_comp('consumer').set_attr(Q=Q)

nw.solve('offdesign', design_path='heat_pump')
#
# nw.solve('offdesign', design_path='heat_pump')
# nw.print_results()
