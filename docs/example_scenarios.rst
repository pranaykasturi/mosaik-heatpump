Example Co-simulation Scenarios
=================================

Example scenarios of the co-simulation of the heat pump, hot water tank
and controller models are available in the `examples <https://gitlab.com/mosaik/
components/energy/mosaik-heatpump/-/blob/10-improve-documentation/docs/code/
examples?ref_type=heads>`_ folder.

There are cyclic dependencies between the models for each time step, for ex.,
the hot water tank needing the information from the controller regarding
the demands and the water flows, and the controller needing information
from the hot water tank regarding the temperature of the water to
calculate the flows. mosaik offers two different ways to resolve such
cyclic dependencies. The first is the *time-shifted* resolution, where the
information from one model is passed to the other model in the next time
step. The second is the *same-time-loop* resolution, where the information
exchange between the models is done in the same time step before
progressing the simulation to the next time step. The mosaik
documentation describes these two ways of dealing with cyclic
dependencies in detail (:ref:`cyclic-data-flows <cyclic_data-flows>`).

The user can choose between the two types of execution, by specifying
the parameter *‘same_time_loop’*, while initializing the simulators for
each of the models. The default execution mode is the *time-shifted*
resolution. For the *same-time-loop* resolution, the parameter
*‘same_time_loop’* has to be set to *‘True’*. Depending on the type of
execution, the way the connections between the different models are
setup varies, and can be seen in the example scenarios below.

Time-shifted resolution of cyclic dependencies
----------------------------------------------

The  `first example scenario <https://gitlab.com/mosaik/
components/energy/mosaik-heatpump/-/blob/10-improve-documentation/docs/code/
examples/scenario_time_shifted.py?ref_type=heads>`_ uses the *time-based* resolution
of the cyclic dependencies offered by mosaik. The different heat pumps, and
calculation modes available in the heat pump model are simulated along with the
hot water tank, with the controller model matching both the space heating and
domestic hot water demand with the heat available in the hot water tank
and controlling the operation of the heat pump.

The simulation is configured as shown below. The inputs to the models
are handled by *‘mosaik-csv’* and the outputs are handled by *‘mosaik-hdf5’*.

.. literalinclude:: ./code/examples/scenario_time_shifted.py
   :language: python
   :lines: 5-26
   :lineno-start: 5

The parameters and/or initial values for the different models are specified.

.. literalinclude:: ./code/examples/scenario_time_shifted.py
   :language: python
   :lines: 28-67
   :lineno-start: 28

The different types of heat pumps and calculation modes that are simulated are
specified.

.. literalinclude:: ./code/examples/scenario_time_shifted.py
   :language: python
   :lines: 69-72
   :lineno-start: 28

The mosaik *'world'*, and the simulators of the different models are initialized.
The inputs required for the different models – domestic hot water demand
(*DHW Demand*); space heating demand (*SH Demand*); the heat source
temperature, which is the ambient air in this case (*T_amb*); and the
temperature of the cold water replacing the domestic hot water supplied
from the tank (*dhw_in_T*) – are available in the `‘scenario_data.csv’ <https://gitlab.com/mosaik
/components/energy/mosaik-heatpump/-/blob/10-improve-documentation/docs/code/examples/
data/scenario_data.csv?ref_type=heads>`_ file. The inputs are handled by *‘mosaik-csv’*
and the output data is handled by *‘mosaik-hdf5’* and saved in hdf5 files.

.. literalinclude:: ./code/examples/scenario_time_shifted.py
   :language: python
   :lines: 78-92
   :lineno-start: 78

The specific parameters for the different heat pump models and calculation modes are added to the
parameters.

.. literalinclude:: ./code/examples/scenario_time_shifted.py
   :language: python
   :lines: 94-102
   :lineno-start: 94

The different models are instantiated.

.. literalinclude:: ./code/examples/scenario_time_shifted.py
   :language: python
   :lines: 104-113
   :lineno-start: 104

The cyclic data flows between the different models are then set up in the time-shifted manner
and the simulation is executed.

.. literalinclude:: ./code/examples/scenario_time_shifted.py
   :language: python
   :lines: 115-156
   :lineno-start: 115


Same-time-loop resolution of cyclic dependencies
------------------------------------------------

The `second example scenario <https://gitlab.com/mosaik/
components/energy/mosaik-heatpump/-/blob/10-improve-documentation/docs/code/examples
/scenario_same_time_loop.py?ref_type=heads>`_ uses the *event-based* resolution
of the same-time-loop cycles offered by mosaik. Only the things that need to be changed
when compared to the *time-based* resolution are shown below.

While initializing the model simulators, the *'same_time_loop'* parameter has to be set to
*'True'* for all the models.

.. literalinclude:: ./code/examples/scenario_same_time_loop.py
   :language: python
   :lines: 82-86
   :lineno-start: 82

The cyclic data flows between the different models are then set up in the same-time-loop manner.

.. literalinclude:: ./code/examples/scenario_same_time_loop.py
   :language: python
   :lines: 115-144
   :lineno-start: 82

For the same-time-loop execution, it is important to set the initial event that kick-starts the
simulation, which is the simulation of the hot water tank for this scenario. The simulation is
then executed.

.. literalinclude:: ./code/examples/scenario_same_time_loop.py
   :language: python
   :lines: 146-150
   :lineno-start: 146


Postprocessing of the results
-----------------------------


Plotting the results
--------------------
