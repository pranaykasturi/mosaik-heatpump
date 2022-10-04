import jsonpickle

class Controller():

    def __init__(self, params):

        self.T_amb = None
        self.heat_source_T = None
        self.sh_demand = None
        self.sh_supply = None
        self.dhw_demand = None
        self.dhw_supply = None
        self.hp_demand = None
        self.hp_supply = None
        self.heat_demand = None
        self.heat_supply = None
        self.hwt_connections = None
        self.T_mean = None
        self.T_room = None

        self.sh_in_F = None
        self.sh_in_T = None
        self.sh_out_F = None
        self.sh_out_T = None

        self.dhw_in_F = None
        self.dhw_in_T = None
        self.dhw_out_F = None
        self.dhw_out_T = None

        self.bottom_layer_T = None
        self.top_layer_T = None

        self.hp_in_F = None
        self.hp_in_T = None
        self.hp_out_F = None
        self.hp_out_T = None
        self.hp_cond_m = None
        self.hp_on_fraction = None

        self.hwt_mass = None

        self.hwt_hr_P_th_set = None

        self.hp_signal = None
        self.heater_signal = None
        self.hp_status = None

        self.P_hr_sh = None
        self.P_hr_dhw = None

        self.T_hp_sp_h = params.get('T_hp_sp_h')
        self.T_hp_sp_l = params.get('T_hp_sp_l')

        # self.T_hp_sp_h = None
        # self.T_hp_sp_l = None
        # self.T_hp_sp_h_1 = params.get('T_hp_sp_h_1')
        # self.T_hp_sp_h_2 = params.get('T_hp_sp_h_2')
        # self.T_hp_sp_l_1 = params.get('T_hp_sp_l_1')
        # self.T_hp_sp_l_2 = params.get('T_hp_sp_l_2')

        self.T_hr_sp = params.get('T_hr_sp')
        self.T_hr_sp_dhw = params.get('T_hr_sp_dhw')
        self.T_hr_sp_sh = params.get('T_hr_sp_sh')
        self.T_max = params.get('T_max')
        self.T_min = params.get('T_min')
        self.dhw_in_T = params.get('dhw_in_T')
        self.sh_dT = params.get('sh_dT')
        self.operation_mode = params.get('operation_mode')

        self.new_hp_sp = False

    def step(self):

        if self.heat_demand is None or self.heat_demand < 0:
            self.heat_demand = 0
        if self.sh_demand is None or self.sh_demand < 0:
            self.sh_demand = 0
        else:
            self.sh_demand *= 1000
        if self.dhw_demand is None or self.dhw_demand < 0:
            self.dhw_demand = 0

        # if self.hwt_connections is not None:
        #     hwt_connections = jsonpickle.decode((self.hwt_connections))

        # self.calc_dhw_supply(hwt_connections)
        self.calc_dhw_supply()

        if self.dhw_out_T < self.T_hr_sp_dhw:
            self.P_hr_dhw = self.dhw_in_F * 4184 * (self.T_hr_sp_dhw - self.dhw_out_T)
        else:
            self.P_hr_dhw = 0

        # self.calc_sh_supply(hwt_connections)
        self.calc_sh_supply()

        if self.sh_out_T < self.T_hr_sp_sh:
            self.P_hr_sh = self.sh_in_F * 4184 * (self.T_hr_sp_sh - self.sh_out_T)
            self.sh_in_T = self.T_hr_sp_sh - self.sh_dT
        else:
            self.P_hr_sh = 0

        if self.sh_supply is None:
            self.sh_supply = 0
        if self.dhw_supply is None:
            self.dhw_supply = 0

        self.heat_supply = self.sh_supply + self.dhw_supply

        # self.get_hp_out_T(hwt_connections)

        if self.operation_mode.lower() == 'heating':

            # if self.T_amb > 15:
            #     if self.hp_in_T < 35:
            #     if not self.new_hp_sp:
            #         self.T_hp_sp_l += 5
            #         self.T_hp_sp_h += 5
            #         self.new_hp_sp = True
            # else:
            #     if self.new_hp_sp:
            #         self.T_hp_sp_l -= 5
            #         self.T_hp_sp_h -= 5
            #         self.new_hp_sp = False

            # if self.hp_out_T < self.T_hp_sp_l:
            #     self.hp_status = 'on'
            # #
            #
            # if self.hp_status == 'on':
            #     if self.hp_out_T < self.T_hp_sp_h:
            #         self.hp_demand = self.hwt_mass * 4184 * (self.T_hp_sp_h - self.hp_out_T) / self.step_size
            #     else:
            #         self.hp_demand = 0
            #         self.hp_status = 'off'
            # else:
            #     self.hp_demand = 0
            #
            # if self.heat_source_T > (self.T_amb + 2):
            #     self.T_hp_sp_h = self.T_hp_sp_h_2
            #     self.T_hp_sp_l = self.T_hp_sp_l_2
            # else:
            #     self.T_hp_sp_h = self.T_hp_sp_h_1
            #     self.T_hp_sp_l = self.T_hp_sp_l_1

            if self.top_layer_T < self.T_hp_sp_h:
                self.hp_status = 'on'
            #

            if self.hp_status == 'on':
                if self.bottom_layer_T < self.T_hp_sp_l:
                    self.hp_demand = self.hwt_mass * 4184 * (self.T_hp_sp_l - self.bottom_layer_T) / self.step_size * 100
                else:
                    self.hp_demand = 0
                    self.hp_status = 'off'
            else:
                self.hp_demand = 0

        elif self.operation_mode.lower() == 'cooling':

            if (self.T_room > self.T_hp_sp_h) or ((self.bottom_layer_T - self.T_room) < 5):
                self.hp_status = 'on'

            if self.bottom_layer_T > 52:
                self.hp_status = 'off'

            if self.hp_status == 'on':
                if self.T_room > (self.T_hp_sp_l+0.5):
                    self.hp_demand = 10000000
                else:
                    self.hp_demand = 0
                    self.hp_status = 'off'
            else:
                self.hp_demand = 0

        if self.hp_in_T is None:
            self.hp_in_T = self.hp_out_T
        
        if self.hp_supply is None:
            #print('hp_supply is None')
            self.hp_supply = 0

        self.hp_in_F = self.hp_on_fraction * self.hp_cond_m
        self.hp_out_F = -self.hp_on_fraction * self.hp_cond_m
            
        if self.T_hr_sp is not None:
            if self.T_mean < self.T_hr_sp:
                self.hwt_hr_P_th_set = (self.hwt_mass * 4184 * (self.T_hr_sp - self.T_mean)) / self.step_size
            else:
                self.hwt_hr_P_th_set = 0

    # def calc_dhw_supply(self, hwt_connections):
    def calc_dhw_supply(self):

        # sh_fraction = 1 # remove later/

        # for key, connection in hwt_connections.items():
        #
        #     if connection.type == 'dhw_out':
        dhw_m_flow = self.dhw_demand / self.step_size

            # if connection.T > self.T_hr_sp_dhw:
            #     dhw_m_flow *= (self.T_hr_sp_dhw - self.dhw_in_T) / (connection.T - self.dhw_in_T)
            #     self.dhw_supply = dhw_m_flow * 4184 * (connection.T - self.dhw_in_T)
        if self.dhw_out_T > self.T_hr_sp_dhw:
            dhw_m_flow *= (self.T_hr_sp_dhw - self.dhw_in_T) / (self.dhw_out_T - self.dhw_in_T)
            self.dhw_supply = dhw_m_flow * 4184 * (self.dhw_out_T - self.dhw_in_T)
        else:
            self.dhw_supply = dhw_m_flow * 4184 * (self.T_hr_sp_dhw - self.dhw_in_T)

        self.dhw_out_F = - dhw_m_flow
        self.dhw_in_F = dhw_m_flow
            # self.dhw_out_T = connection.T

                # break

    # def calc_sh_supply(self, hwt_connections):
    def calc_sh_supply(self):

        # for key, connection in hwt_connections.items():
        #
        #     if connection.type == 'sh_out':
        sh_m_flow = self.sh_demand / (4184 * self.sh_dT)

        self.sh_supply = sh_m_flow * 4184 * self.sh_dT

            # if connection.T >= self.T_hr_sp_sh:
            #     sh_in_T = connection.T - self.sh_dT
        if self.sh_out_T >= self.T_hr_sp_sh:
            self.sh_in_T = self.sh_out_T - self.sh_dT
        else:
            self.sh_in_T = self.T_hr_sp_sh - self.sh_dT

        self.sh_in_F = sh_m_flow
        # self.sh_in_T = sh_in_T
        self.sh_out_F = - sh_m_flow
            # self.sh_out_T = connection.T

                # break

    # def get_hp_out_T (self, hwt_connections):
    #
    #     for key, connection in hwt_connections.items():
    #
    #         if connection.type == 'hp_out':
    #             self.hp_out_T = connection.T
