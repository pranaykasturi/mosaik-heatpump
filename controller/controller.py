import jsonpickle

class Controller():

    def __init__(self, params):

        self.outside_temperature = None
        self.sh_demand = None
        self.sh_supply = None
        self.dhw_demand = None
        self.dhw_supply = None
        self.hp_demand = None
        self.heat_demand = None
        self.heat_supply = None
        self.hwt_snapshot = None
        self.T_mean = None

        self.sh_in_F = None
        self.sh_in_T = None
        self.sh_out_F = None

        self.dhw_in_F = None
        self.dhw_in_T = None
        self.dhw_out_F = None

        self.hp_in_F = None
        self.hp_in_T = None
        self.hp_out_F = None
        self.hp_out_T = None

        self.T_hp_sp = params.get('T_hp_sp')
        self.T_max = params.get('T_max')
        self.T_min = params.get('T_min')
        self.dhw_in_T = params.get('dhw_in_T')
        self.sh_dT = params.get('sh_dT')

        self.i = 0

    def step(self):

        if self.heat_demand is None or self.heat_demand < 0:
            self.heat_demand = 0
        if self.sh_demand is None or self.sh_demand < 0:
            self.sh_demand = 0
        if self.dhw_demand is None or self.dhw_demand < 0:
            self.dhw_demand = 0

        # self.sh_demand = self.heat_demand/2
        # self.dhw_demand = self.heat_demand/2

        if self.hwt_snapshot is not None:
            hwt = jsonpickle.decode((self.hwt_snapshot))

        self.T_mean = hwt.T_mean

        sh_fraction, dhw_m_flow = self.calc_dhw_supply(self.step_size, hwt)
        self.dhw_out_F = - dhw_m_flow
        self.dhw_in_F = dhw_m_flow
        self.dhw_in_T = self.dhw_in_T

        sh_m_flow, sh_in_T = self.calc_sh_supply(self.step_size, hwt, sh_fraction)
        self.sh_in_F = sh_m_flow
        self.sh_in_T = sh_in_T
        self.sh_out_F = - sh_m_flow

        if self.sh_supply is None:
            self.sh_supply = 0
        if self.dhw_supply is None:
            self.dhw_supply = 0

        self.heat_supply = self.sh_supply + self.dhw_supply

        if hwt.T_mean < self.T_hp_sp:
            self.hp_demand = hwt.mass * 4184 * (self.T_hp_sp - hwt.T_mean) / self.step_size
        else:
            self.hp_demand = 0

        self.get_hp_out_T(hwt)

        if self.hp_in_T is None:
            self.hp_in_T = self.hp_out_T

    def calc_dhw_supply(self, step_size, hwt):

        sh_fraction = 1 # remove later

        for key, connection in hwt.connections.items():

            if connection.type == 'dhw_out':
                if connection.T > self.T_min:
                    dhw_m_flow = self.dhw_demand / (4184 * (connection.T - self.dhw_in_T))
                    if dhw_m_flow > (connection.corresponding_layer.volume / step_size):
                        dhw_m_flow = connection.corresponding_layer.volume / step_size
                        sh_fraction = 0
                    else:
                        sh_fraction = (connection.corresponding_layer.volume - (dhw_m_flow * step_size))/connection.corresponding_layer.volume
                else:
                    dhw_m_flow = 0
                    sh_fraction = 1

                self.dhw_supply = dhw_m_flow * 4184 * (connection.T - self.dhw_in_T)

                return sh_fraction, dhw_m_flow

    def calc_sh_supply(self, step_size,  hwt, sh_fraction):

        for key, connection in hwt.connections.items():

            if connection.type == 'sh_out':
                if self.T_min <= connection.T <= self.T_max:
                    sh_m_flow = self.sh_demand/(4184 * self.sh_dT)
                    if sh_fraction == 0:
                        sh_m_flow = 0
                    elif sh_m_flow > (sh_fraction * connection.corresponding_layer.volume / step_size):
                        sh_m_flow = sh_fraction * connection.corresponding_layer.volume / step_size
                else:
                    sh_m_flow = 0

                self.sh_supply = sh_m_flow * 4184 * self.sh_dT

                # print(connection.T, self.sh_dT)

                sh_in_T = connection.T - self.sh_dT

                return sh_m_flow, sh_in_T

    def get_hp_out_T (self, hwt):

        for key, connection in hwt.connections.items():

            if connection.type == 'hp_out':
                self.hp_out_T = connection.T