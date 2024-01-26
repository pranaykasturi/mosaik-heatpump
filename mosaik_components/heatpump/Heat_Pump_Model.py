__doc__ = """
This module contains a simulation model of a Heat Pump based on the library TESPy.
"""

from mosaik_components.heatpump.Heat_Pump_Design import Heat_Pump_Design

class Heat_Pump_Initiation():
    """Initiation of the Heat Pump based on the initial parameters"""
    def __init__(self, params, COP_m_data):
        self.Heat_Pump = Heat_Pump_Design(params, COP_m_data)


class Heat_Pump_State():
    """Attributes that define the state of the Heat_Pump"""
    def __init__(self):
        self.P_Required = 0
        """Power consumption of the heat pump in W"""
        self.COP = 0
        """COP of the heat pump"""
        self.Q_Demand = 0
        """The heat demand of the consumer in W"""
        self.Q_Supplied = 0
        """The heat supplied to the consumer in W"""
        self.Q_evap = 0
        """The heat removed in the evaporator in W"""
        self.cons_T = 0
        """The temperature at which heat is supplied to the consumer (in °C)"""
        self.cond_in_T = 0
        """The temperature at which the water reenters the condenser (in °C)"""
        self.heat_source_T = 0
        """The temperature of the heat source (in °C)"""
        self.T_amb = 0
        """The ambient temperature (in °C)"""
        self.cond_m = 0
        """The mass flow rate of water in the condenser of the heat pump (in kg/s)"""
        self.cond_m_neg = 0
        """The negative of the mass flow rate of water in the condenser of the heat pump (in kg/s)"""
        self.step_executed = False
        """The execution of the step function of the heat pump model"""

class Heat_Pump_Inputs():
    """Inputs variables to the heat pump for each time step"""
    __slots__ = ['Q_Demand', 'heat_source_T', 'cons_T', 'step_size', 'cond_in_T', 'T_amb']

    def __init__(self, params):

        self.Q_Demand = None
        """The heat demand of the consumer in W"""

        self.heat_source_T = None
        """The temperature of the heat source (in °C)"""

        self.T_amb = None
        """The ambient temperature (in °C)"""

        self.cond_in_T = None
        """The temperature at which the water reenters the condenser (in °C)"""

        self.step_size = None
        """step size in seconds"""


class Heat_Pump():
    """
    Simulation model of a heat pump based on the libraries **TESPy** and **hplib**.

    Heat pump parameters are provided at instantiation by the dictionary **params**. The following dictionary contains
    the parameters that are mandatory::

        {
            'calc_mode': 'hplib',
            'hp_model': 'LW 300(L)',
            'heat_source': 'air',
        }

    Explanation of the entries in the dictionary:

    * **calc_mode**: The calculation mode that is used by the heat pump model. Currently, *'detailed'*, *'fast'*,
      *'hplib'*, and *'fixed'* calculation modes are available. The differences are explained in the documentation.
    * **hp_model**: The specific model of the heat pump that must be simulated. The different models available currently
      can be found in the documentation. This need not be specified for the *'fixed'* calculation mode.
    * **heat_source**: The fluid that acts as the source of heat for the heat pump, either *'water'* or *'air'*

    If the **'hplib'** calculation mode is chosen, the following parameter is required in addition to the mandatory
    ones::

        {
            'equivalent_hp_model': 'Air_30kW',
        }

    * **equivalent_hp_model**: The heat pump model from the saved data file whose limits of operation will be applied

    Alternatively, the limits can be directly specified in the following parameter::

        {
            'hp_limits': { 'heat_source_T_min': -10, 'heat_source_T_max': 35, 'cons_T_min': 25, 'cons_T_max': 55,
                           'heatload_min': 15000 }
        }

    For the **'hplib'** calculation mode if the *'Generic'* heat pump model is chosen, the following parameters are
    required in addition to the mandatory ones::

        {
            'cons_T': 35,
            'heat_source_T': 12,
            'P_th': 35000,
        }

    * **cons_T**: The temperature at which heat is supplied to the consumer (in °C).
    * **heat_source_T**: The temperature at which the fluid (water or air) is available as the heat source (in °C).
    * **P_th**: The heating capacity of the heat pump (in W).

    If the *'fixed'* calculation mode is chosen, the following parameters are required in addition to the mandatory
    ones::

        {
            'COP': 3.5,
            'heating capacity': 35000,
            'cond_m': 0.5,
        }

    * **COP**: The COP of the heat pump.
    * **heating_capacity**: The heating capacity of the heat pump (in W).
    * **cond_m**: The mass flow rate of water in the condenser (in kg/s).

    """

    __slots__ = ['design', 'state', 'inputs']

    def __init__(self, params, COP_m_data):
        self.design = Heat_Pump_Initiation(params, COP_m_data)
        """stores the design of the heat pump in a
        :class:`.Heat_Pump_Model.Heat_Pump_Initiation` object"""
        self.state = Heat_Pump_State()
        """stores the state variables of the heat pump in a
        :class:`.Heat_Pump_Model.Heat_Pump_State` object"""
        self.inputs = Heat_Pump_Inputs(params)
        """stores the input parameters of the heat pump model in a
        :class:`.Heat_Pump_Model.Heat_Pump_Inputs` object"""

    def step(self):
        """Perform simulation step with step size step_size"""

        step_inputs = {'heat_source_T': self.inputs.heat_source_T,
                       'Q_Demand': self.inputs.Q_Demand,
                       'cond_in_T': self.inputs.cond_in_T,
                       'T_amb': self.inputs.T_amb
                       }
        # Update the state of the heat pump for the inputs
        if self.inputs.Q_Demand is not None:
            self.state.Q_Demand = self.inputs.Q_Demand

        if self.inputs.heat_source_T is not None:
            self.state.heat_source_T = self.inputs.heat_source_T

        if self.inputs.T_amb is not None:
            self.state.T_amb = self.inputs.T_amb

        if self.inputs.cond_in_T is not None:
            self.state.cond_in_T = self.inputs.cond_in_T

        # Perform the step of the heat pump model
        self.design.Heat_Pump.step(step_inputs)

        # Update the state of the heat pump for the outputs
        self.state.P_Required = self.design.Heat_Pump.P_cons
        self.state.COP = self.design.Heat_Pump.COP
        self.state.Q_Supplied = self.design.Heat_Pump.Q_Supplied
        self.state.Q_evap = self.design.Heat_Pump.Q_evap
        self.state.on_fraction = self.design.Heat_Pump.on_fraction
        self.state.cond_m = self.design.Heat_Pump.cond_m
        self.state.cond_m_neg = - self.design.Heat_Pump.cond_m
        self.state.cons_T = self.design.Heat_Pump.cons_T
        self.state.step_executed = True

