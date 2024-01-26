__doc__ = """
The controller module contains a class for the controller model (:class:`Controller`).
"""

class Controller():
    """
        Simulation model of a controller.

        The controller model used in this work utilizes simple Boolean logic to:
            1.	Match the heating demands with the supply from the hot water tank/back up heaters
            2.	Control the operation of the heat pump using different control strategies

        Controller parameters are provided at instantiation by the dictionary **params**. This is an example, how
        the dictionary might look like::

            params = {
                'T_hp_sp_h': 50,
                'T_hp_sp_l': 40,
                'T_hr_sp_hwt': 40,
                'T_hr_sp_dhw': 40,
                'T_hr_sp_sh': 35,
                'dhw_in_T': 10,
                'sh_dT': 7,
                'operation_mode': 'heating',
                'control_strategy': '1'
                }

        Explanation of the entries in the dictionary:

        * **T_hp_sp_h**: The higher temperature set point for heat pump operation (in °C)
        * **T_hp_sp_l**: The lower temperature set point for heat pump operation (in °C)
        * **T_hr_sp_hwt**: The temperature set point for the back up heater within the hot water tank (in °C)
        * **T_hr_sp_dhw**: The temperature set point for the back up heater for domestic hot water supply (in °C)
        * **T_hr_sp_sh**: The temperature set point for the back up heater for space heating supply (in °C)
        * **dhw_in_T**: The default temperature of cold water inlet  for domestic hot water (in °C)
        * **sh_dT**: The temperature difference of the water in the space heating supply circuit (in °C)
        * **operation_mode**: The operation mode of the heating system, either 'heating' or 'cooling'
        * **control_strategy**: The control strategy to be used for the heat pump operation. Currently, two
          strategies have been implemented ('1' & '2')

        """
    def __init__(self, params):

        self.T_hp_sp_h = params.get('T_hp_sp_h')
        self.T_hp_sp_l = params.get('T_hp_sp_l')
        self.T_hr_sp_hwt = params.get('T_hr_sp_hwt', None)
        self.T_hr_sp_dhw = params.get('T_hr_sp_dhw', None)
        self.T_hr_sp_sh = params.get('T_hr_sp_sh', None)
        self.dhw_in_T = params.get('dhw_in_T', 10)
        self.sh_dT = params.get('sh_dT', 7)
        self.operation_mode = params.get('operation_mode', 'heating')
        self.control_strategy = params.get('control_strategy', '1')

        self.T_amb = None                   # The ambient air temperature (in °C)
        self.heat_source_T = None           # The temperature of source for the heat pump (in °C)
        self.T_room = None                  # The temperature of the room (used in cooling mode, in °C)

        self.sh_demand = None               # The space heating (SH) demand (in kW)
        self.sh_supply = None               # The heat supplied by the heating system for SH (in W)
        self.dhw_demand = None              # The domestic hot water (DHW) demand (in L)
        self.dhw_supply = None              # The heat supplied by the heating system for DHW (in W)
        self.heat_demand = None             # The total heat demand from SH & DHW (in W)
        self.heat_supply = None             # The total heat supplied by the heating system for SH & DHW (in W)
        self.hp_demand = None               # The heat demand for the heat pump from the hot water tank (in W)
        self.hp_supply = None               # The heat supplied by the heat pump to the hot water tank (in W)

        self.sh_in_F = None                 # The mass flow of water into the hot water tank from SH circuit (in kg/s)
        self.sh_in_T = None                 # The temperature of water into the hot water tank from SH circuit (in °C)
        self.sh_out_F = None                # The mass flow of water from the hot water tank into SH circuit (in kg/s)
        self.sh_out_T = None                # The temperature of water from the hot water tank into SH circuit (in °C)

        self.dhw_in_F = None                # The mass flow of water into the hot water tank from DHW circuit (in kg/s)
        self.dhw_in_T = None                # The temperature of water into the hot water tank from DHW circuit (in °C)
        self.dhw_out_F = None               # The mass flow of water from the hot water tank into DHW circuit (in kg/s)
        self.dhw_out_T = None               # The temperature of water from the hot water tank into DHW circuit (in °C)

        self.hp_in_F = None                 # The mass flow of water into the hot water tank from heat pump (in kg/s)
        self.hp_in_T = None                 # The temperature of water into the hot water tank from heat pump (in °C)
        self.hp_out_F = None                # The mass flow of water from the hot water tank into heat pump (in kg/s)
        self.hp_out_T = None                # The temperature of water from the hot water tank into heat pump (in °C)
        self.hp_cond_m = None               # The mass flow of water in the condenser of heat pump (in kg/s)
        self.hp_on_fraction = None          # The fraction of the time step for which the heat pump is on

        self.bottom_layer_T = None          # The temperature of the bottom layer of the hot water tank (in °C)
        self.top_layer_T = None             # The temperature of the top layer of the hot water tank (in °C)
        self.T_mean_hwt = None              # The mean temperature of the hot water tank (in °C)
        self.hwt_mass = None                # The total mass of water inside the hot water tank (kg)

        self.hwt_hr_P_th_set = None         # The heat demand for the in built heating rod of the hot water tank (in W)

        self.hp_status = None               # The status of the heat pump, either "on" or "off"

        self.P_hr_sh = None                 # The heat supplied by the back up heater in SH circuit (in W)
        self.P_hr_dhw = None                # The heat supplied by the back up heater in DHW circuit (in W)

    def step(self):
        """Perform simulation step with step size step_size"""

        # Convert the SH demand available in kW to W
        if self.sh_demand is None or self.sh_demand < 0:
            self.sh_demand = 0
        else:
            self.sh_demand *= 1000

        # Calculate the mass flows, temperatures and heat from back up heater for the SH circuit
        self.calc_sh_supply()

        if self.dhw_demand is None or self.dhw_demand < 0:
            self.dhw_demand = 0

        # Calculate the mass flows, temperatures and heat from back up heater for the DHW circuit
        self.calc_dhw_supply()

        # Calculate the total heat demand for SH & DHW
        self.heat_demand = self.sh_demand + self.dhw_demand
        # Calculate the total heat supply of the heating system
        self.heat_supply = self.sh_supply + self.dhw_supply

        # Control strategies for the operation of heat pump in heating mode
        if self.operation_mode.lower() == 'heating':

            # Control strategy 1 - start
            if self.control_strategy == '1':
                if self.bottom_layer_T < self.T_hp_sp_l:
                    self.hp_status = 'on'

                if self.hp_status == 'on':
                    if self.bottom_layer_T < self.T_hp_sp_h:
                        self.hp_demand = self.hwt_mass * 4184 * (self.T_hp_sp_h - self.bottom_layer_T) / self.step_size
                    else:
                        self.hp_demand = 0
                        self.hp_status = 'off'
                else:
                    self.hp_demand = 0
            # Control strategy 1 - end

            # Control strategy 2 - start
            elif self.control_strategy == '2':
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

        # Control strategies for the operation of heat pump in cooling mode
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

        # Setting the inlet temperature to the hot water tank from the heat pump, in the case where heat pump isn't
        # operational
        if self.hp_in_T is None:
            self.hp_in_T = self.hp_out_T
        
        if self.hp_supply is None:
            self.hp_supply = 0

        # Adjusting the mass flow rates for hot water tank in the heat pump circuit, when heat pump operates for only
        # a fraction of the time step
        if self.hp_on_fraction is not None and self.hp_cond_m is not None:
            self.hp_in_F = self.hp_on_fraction * self.hp_cond_m
            self.hp_out_F = -self.hp_on_fraction * self.hp_cond_m

        # Calculating the heat required from the in-built heating rod of the hot water tank
        if self.T_hr_sp_hwt is not None:
            if self.T_mean_hwt < self.T_hr_sp_hwt:
                self.hwt_hr_P_th_set = (self.hwt_mass * 4184 * (self.T_hr_sp_hwt - self.T_mean_hwt)) / self.step_size
            else:
                self.hwt_hr_P_th_set = 0

    def calc_dhw_supply(self):
        """Calculate the mass flows and temperatures of water, and the heat from the back up heater in the domestic hot
        water (DHW) circuit"""

        self.dhw_in_F = self.dhw_demand / self.step_size
        # If the water is hotter than the requirement, it is mixed with cold water and the flow rate is adjusted
        if self.dhw_out_T >= self.T_hr_sp_dhw:
            self.dhw_in_F *= (self.T_hr_sp_dhw - self.dhw_in_T) / (self.dhw_out_T - self.dhw_in_T)
            self.dhw_supply = self.dhw_in_F * 4184 * (self.dhw_out_T - self.dhw_in_T)
            self.P_hr_dhw = 0
        else:
            self.dhw_supply = self.dhw_in_F * 4184 * (self.T_hr_sp_dhw - self.dhw_in_T)
            self.P_hr_dhw = self.dhw_in_F * 4184 * (self.T_hr_sp_dhw - self.dhw_out_T)
        self.dhw_out_F = - self.dhw_in_F


    def calc_sh_supply(self):
        """Calculate the mass flows and temperatures of water, and the heat from the back up heater in the space
        heating (SH) circuit"""

        self.sh_in_F = self.sh_demand / (4184 * self.sh_dT)
        self.sh_supply = self.sh_in_F * 4184 * self.sh_dT
        if self.sh_out_T >= self.T_hr_sp_sh:
            self.sh_in_T = self.sh_out_T - self.sh_dT
            self.P_hr_sh = 0
        else:
            self.P_hr_sh = self.sh_in_F * 4184 * (self.T_hr_sp_sh - self.sh_out_T)
            self.sh_in_T = self.T_hr_sp_sh - self.sh_dT
        self.sh_out_F = - self.sh_in_F
