
class CoolingLoadSim:

    def __init__(self, params):

        # parameters set during initialization
        self.room_area = params.get('room_area') #m^2
        self.room_height = params.get('room_height') #m

        self.room_volume = self.room_area * self.room_height

        self.window_area = params.get('window_area') #m^2
        self.opt_transmission = params.get('opt_transmission')
        self.air_changes = params.get('air_changes') #/hr
        self.internal_heat_gain = params.get('internal_heat_gain') #W/m^2
        self.T_room = params.get('initial_room_temp') #deg. C

        # Inputs passed during simulation
        self.T_amb = None
        self.G = None # Solar heat gain W/m^2
        self.T_air_in = None
        self.m_air_in = None
        self.Q_evap = None
        self.step_size = None

        # constants
        self.rho = 1.225 # kg/m^3
        self.C_p = 1006 # J/kg.K


    def step(self):

        # Solar Heat Gain Calculation
        Q_solar = self.G * self.window_area * self.opt_transmission

        # Heat addition due to air change
        Q_air_change = ((self.air_changes/3600) * (self.room_volume) * (self.rho)) * self.C_p * (self.T_amb - self.T_room)

        # Internal heat gain addition
        Q_int_heat_gain = self.internal_heat_gain * self.room_area

        # Total heat addition
        Q_total = Q_solar + Q_air_change + Q_int_heat_gain + self.Q_evap

        # Updating room temperature

        self.T_room += (Q_total * self.step_size) / (self.room_volume * self.rho * self.C_p)

if __name__ == '__main__':
    params_coolingloadsim = {
        'room_area': 408,
        'room_height': 2.74,
        'window_area': 22,
        'opt_transmission': 0.6,
        'air_changes': 0.5,
        'internal_heat_gain': 5,
        'initial_room_temp': 20,
    }
    CoolingLoadSim1 = CoolingLoadSim(params_coolingloadsim)

    CoolingLoadSim1.T_room = 63.9274
    CoolingLoadSim1.T_amb = 31.02
    CoolingLoadSim1.G = 496.715
    CoolingLoadSim1.Q_evap = 0
    CoolingLoadSim1.step_size = 60


    CoolingLoadSim1.step ()

    print('simulation done')