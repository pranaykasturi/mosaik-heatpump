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
        self.heat_source = None
        """The temperature of the heat source (in °C)"""
        self.heat_source_T = None
        """The temperature of the heat source (in °C)"""
        self.cons_T = None
        """The temperature at which heat is supplied to the consumer (in °C)"""
        self.amb_T = None


class Heat_Pump_Inputs():
    """Inputs variables to the heat pump for each time step"""
    __slots__ = ['cons_Q', 'heat_source', 'heat_source_T', 'cons_T', 'step_size', 'amb_T']

    def __init__(self, params):
        self.cons_Q = params.get('cons_Q')

        self.heat_source = params.get('heat_source')
        """The source of heat ('water' or 'air')"""

        self.heat_source_T = params.get('heat_source_T')
        """The temperature of the heat source (in °C)"""

        self.cons_T = params.get('cons_T')
        """The temperature at which heat is supplied to the consumer (in °C)"""

        self.amb_T = params.get('amb_T')

        self.step_size = None
        """step size in seconds"""


class Heat_Pump():
    """
    Simulation model of a heat pump based on the library TESPy.

    You have to provide the *params* dictionary that contains the parameters
    required for the design of the heat pump. It will look like this::

        {
            'cons_T': 35,
            'heat_source_T': 12,
            'heat_source': 'water' or 'air'
        }

    -*cons_T* is the temperature, in °C, at which heat is supplied to the consumer.

    -*heat_source_T* is the temperature, in °C, at which the ambient fluid (water or air)
    is available as the heat source.

    -*heat_source* is the fluid, either 'water' or 'air', that acts as the heat source for
    the system.
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

        step_inputs = {'heat_source_T': self.inputs.heat_source_T,
                       'cons_Q': self.inputs.cons_Q,
                       'cons_T': self.inputs.cons_T,
                       'amb_T': self.inputs.amb_T
                       }

        self.state.cons_Q = self.inputs.cons_Q

        self.state.heat_source_T = self.inputs.heat_source_T

        self.state.cons_T = self.inputs.cons_T

        self.state.amb_T = self.inputs.amb_T

        self.state.p_kw, self.state.COP = self.design.Heat_Pump.step(step_inputs)
