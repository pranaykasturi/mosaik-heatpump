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
        self.T_hr_sp = params.get('T_hr_sp')
        self.T_hr_sp_dhw = params.get('T_hr_sp_dhw')
        self.T_hr_sp_sh = params.get('T_hr_sp_sh')
        self.dhw_in_T = params.get('dhw_in_T')
        self.sh_dT = params.get('sh_dT')
        self.operation_mode = params.get('operation_mode')
        self.control_strategy = params.get('control_strategy')

    def step(self):

        if self.sh_demand is None or self.sh_demand < 0:
            self.sh_demand = 0
        else:
            self.sh_demand *= 1000

        self.calc_sh_supply()

        if self.dhw_demand is None or self.dhw_demand < 0:
            self.dhw_demand = 0

        self.calc_dhw_supply()

        self.heat_supply = self.sh_supply + self.dhw_supply

        self.heat_demand = self.sh_demand + self.dhw_demand

        if self.operation_mode.lower() == 'heating':

            if self.control_strategy == '1':
                # Control strategy 1 - start
                if self.bottom_layer_T < self.T_hp_sp_l:
                    self.hp_status = 'on'

                if self.hp_status == 'on':
                    if self.bottom_layer_T < self.T_hp_sp_h:
                        self.hp_demand = self.hwt_mass * 4184 * (self.T_hp_sp_l - self.bottom_layer_T) / self.step_size
                    else:
                        self.hp_demand = 0
                        self.hp_status = 'off'
                else:
                    self.hp_demand = 0
                # Control strategy 1 - end

            elif self.control_strategy == '2':
                # Control strategy 2 - start
                if self.top_layer_T < self.T_hp_sp_h:
                    self.hp_status = 'on'
                #
                if self.hp_status == 'off':
                    if self.bottom_layer_T < self.T_hp_sp_l:
                        self.hp_status = 'on'

                if self.hp_status == 'on':
                    if self.bottom_layer_T < self.T_hp_sp_l:
                        self.hp_demand = self.hwt_mass * 4184 * (self.T_hp_sp_l - self.bottom_layer_T) / self.step_size
                    else:
                        self.hp_demand = 0
                        self.hp_status = 'off'
                else:
                    self.hp_demand = 0
                # Control strategy 2 - end


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
            self.hp_supply = 0

        if self.hp_on_fraction is not None and self.hp_cond_m is not None:
            self.hp_in_F = self.hp_on_fraction * self.hp_cond_m
            self.hp_out_F = -self.hp_on_fraction * self.hp_cond_m

        if self.T_hr_sp is not None:
            if self.T_mean < self.T_hr_sp:
                self.hwt_hr_P_th_set = (self.hwt_mass * 4184 * (self.T_hr_sp - self.T_mean)) / self.step_size
            else:
                self.hwt_hr_P_th_set = 0

    def calc_dhw_supply(self):
        self.dhw_in_F = self.dhw_demand / self.step_size
        if self.dhw_out_T >= self.T_hr_sp_dhw:
            self.dhw_in_F *= (self.T_hr_sp_dhw - self.dhw_in_T) / (self.dhw_out_T - self.dhw_in_T)
            self.dhw_supply = self.dhw_in_F * 4184 * (self.dhw_out_T - self.dhw_in_T)
            self.P_hr_dhw = 0
        else:
            self.dhw_supply = self.dhw_in_F * 4184 * (self.T_hr_sp_dhw - self.dhw_in_T)
            self.P_hr_dhw = self.dhw_in_F * 4184 * (self.T_hr_sp_dhw - self.dhw_out_T)
        self.dhw_out_F = - self.dhw_in_F


    def calc_sh_supply(self):
        self.sh_in_F = self.sh_demand / (4184 * self.sh_dT)
        self.sh_supply = self.sh_in_F * 4184 * self.sh_dT
        if self.sh_out_T >= self.T_hr_sp_sh:
            self.sh_in_T = self.sh_out_T - self.sh_dT
            self.P_hr_sh = 0
        else:
            self.P_hr_sh = self.sh_in_F * 4184 * (self.T_hr_sp_sh - self.sh_out_T)
            self.sh_in_T = self.T_hr_sp_sh - self.sh_dT
        self.sh_out_F = - self.sh_in_F
