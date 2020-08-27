"""
This module contains a simulation model of a Heat Pump based on the library TESPy.
"""

# from ..model import Model
from Heat_Pump_Des import Heat_Pump_Des


class Heat_Pump_Design():
    """Design of the Heat Pump based on the initial parameters"""
    def __init__(self, params):
        self.Heat_Pump = Heat_Pump_Des(params)


class Heat_Pump_State():
    """Attributes that define the state of the Heat_Pump"""
    def __init__(self):
        self.p_kw = None
        """Power consumption of the Heat Pump in kW"""
        self.COP = None
        """COP of the Heat Pump"""
        self.cons_Q = None
        """The heat demand of the consumer in kW"""
        self.amb_T = None
        """The ambient temperature in °C"""


class Heat_Pump_Inputs():
    """Inputs variables to the heat pump for each time step"""
    __slots__ = ['cons_Q', 'amb_T', 'step_size']

    def __init__(self, params):
        self.cons_Q = params['cons_Q']
        """The heat demand of the consumer in kW"""

        self.amb_T = params['amb_p_temp']
        """The ambient temperature in °C"""

        self.step_size = None
        """step size in seconds"""


class Heat_Pump():
    """
    Simulation model of a heat pump based on the library TESPy.

    You have to provide the *params* dictionary that contains all the parameters
    required for the design of the heat pump. It will look like this::

        {
            'cd_cons_temp': 90,
            'cb_dhp_temp': 60,
            'amb_p_temp': 12,
            'amb_p_pres': 2,
            'ev_amb_out_temp': 9,
            'ev_amb_out_pres': 2,
            'cons_q': 200e3,
            'ic_out_temp': 30
        }

    -*cd_cons_temp* is the temperature, in °C, at which the consumer is supplied heat.

    -*cd_dhp_temp*  is the temperature, in °C, at which the consumer returns the heating
    fluid to the condenser.

    -*amb_p_temp* is the temperature, in °C, and *amb_p_pres* is the pressure, in bar, at
     which the ambient fluid (water or air) is available as the heat source.

    -*ev_amb_out_temp* is the temperature, in °C, and *ev_amb_out_pres* is the pressure,
    in bar, at which the ambient fluid (water or air) is available released back to the
    ambient.

    -*cons_q* is the consumer heat demand, in kW, in the design case.

    -*ic_out_temp* is the temperature, in °C, at which the ambient fluid is released back
    to the ambient from the intercooler of the compressor.
    """

    __slots__ = ['design', 'state', 'inputs']

    def __init__(self, params):
        self.design = Heat_Pump_Design(params)
        """stores the design of the heat pump in a
        :class:`.Heat_Pump_Model.Heat_Pump_Design` object"""
        self.state = Heat_Pump_State()
        """stores the state variables of the heat pump in a
        :class:`.Heat_Pump_Model.Heat_Pump_State` object"""
        self.inputs = Heat_Pump_Inputs(params)
        """stores the input parameters of the heat pump model in a
        :class:`.Heat_Pump_Model.Heat_Pump_Inputs` object"""

    def step(self):
        """
        perform simulation step

        The power consumption of the heat pump in the offdesign mode
        is calculated based on the consumer heat demand and the ambient
        fluid temperature.

        """

        step_inputs = {'amb_T': self.inputs.amb_T, 'cons_Q': self.inputs.cons_Q}

        self.state.cons_Q = self.inputs.cons_Q

        self.state.amb_T = self.inputs.amb_T

        self.state.p_kw, self.state.COP = self.design.Heat_Pump.step(step_inputs)
