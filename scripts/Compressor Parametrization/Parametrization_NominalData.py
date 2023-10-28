from tespy.components import Condenser
from tespy.components import CycleCloser
from tespy.components import Drum
from tespy.components import HeatExchanger
from tespy.components import HeatExchangerSimple
from tespy.components import Pump
from tespy.components import Sink
from tespy.components import Source
from tespy.components import Valve
from tespy.components import Compressor
from tespy.connections import Connection
from tespy.connections import Ref
from tespy.networks import Network
from tespy.tools.characteristics import CharLine
from tespy.tools.characteristics import load_default_char as ldc

eta_s = 0.63  # Compressor efficiency
pr = 1.35     # Compressor 2 pressure ratio
LWC = 35      # Leaving Water Condenser temperature (in deg.C)
T_amb = 7     # Ambient air temperature (in deg.C)
HL = 32500    # Heat load in W
ref = 'R404a' # Refrigerant

# %% network
nw = Network(
            fluids=[ref, 'water', 'air'], T_unit='C', p_unit='bar',
            h_unit='kJ / kg', m_unit='kg / s'
        )

nw.set_attr(iterinfo=False)

# %% components

# sources & sinks
cool_closer = CycleCloser('coolant cycle closer')
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

cp1 = Compressor('compressor 1')
cp2 = Compressor('compressor 2')
# %% connections

# consumer system

c_in_cd = Connection(cool_closer, 'out1', cd, 'in1')
close_crp = Connection(cons_closer, 'out1', crp, 'in1')
crp_cd = Connection(crp, 'out1', cd, 'in2')
cd_cons = Connection(cd, 'out2', cons, 'in1')
cons_close = Connection(cons, 'out1', cons_closer, 'in1')


nw.add_conns(c_in_cd, close_crp, crp_cd, cd_cons, cons_close)

# connection condenser - evaporator system

cd_va = Connection(cd, 'out1', va, 'in1')

nw.add_conns(cd_va)

# evaporator system

va_dr = Connection(va, 'out1', dr, 'in1')
dr_erp = Connection(dr, 'out1', erp, 'in1')
erp_ev = Connection(erp, 'out1', ev, 'in2')
ev_dr = Connection(ev, 'out2', dr, 'in2')

nw.add_conns(va_dr, dr_erp, erp_ev, ev_dr)

amb_in_apu = Connection(amb_in, 'out1', apu, 'in1')
apu_ev = Connection(apu, 'out1', ev, 'in1')
ev_amb_out = Connection(ev, 'out1', amb_out, 'in1')

nw.add_conns(amb_in_apu, apu_ev, ev_amb_out)

# connection evaporator system - compressor system
dr_cp1 = Connection(dr, 'out2', cp1, 'in1')
nw.add_conns(dr_cp1)

# compressor-system
cp1_cp2 = Connection(cp1, 'out1', cp2, 'in1')
cp2_close = Connection(cp2, 'out1', cool_closer, 'in1')
nw.add_conns(cp1_cp2, cp2_close)

# %% component parametrization

# condenser system

cd.set_attr(pr1=0.99, pr2=0.99, ttd_u=5, design=['pr2', 'ttd_u'],
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

# compressor system

cp1.set_attr(eta_s=eta_s, design=['eta_s'], offdesign=['eta_s_char'])
cp2.set_attr(eta_s=eta_s, pr=pr, design=['eta_s'], offdesign=['eta_s_char'])

# %% connection parametrization

# condenser system

c_in_cd.set_attr(p0=25, fluid={'water': 0, ref: 1, 'air': 0})
close_crp.set_attr(T=(LWC-5), p=1.5, fluid={'water': 1, ref: 0, 'air': 0},
                   offdesign=['m'])
cd_cons.set_attr(T=LWC, design=['T'])

# evaporator system cold side
dr_erp.set_attr(p0=2)
erp_ev.set_attr(m=Ref(va_dr, 1.15, 0))
dr_cp1.set_attr(h0=350)

# evaporator system hot side

# pumping at constant rate in partload
amb_in_apu.set_attr(T=T_amb, p=1, fluid={'water': 0, ref: 0, 'air': 1})
apu_ev.set_attr(p=1.0001) # check this
ev_amb_out.set_attr(T=T_amb-5)

# %% key paramter

cons.set_attr(Q=-HL)

# %% Calculation

nw.solve('design')
nw.print_results()
print(nw.get_comp('compressor 1').P.val + nw.get_comp('compressor 2').P.val)
nw.save('Par_NominalData')
