mosaik-heatpump
===============

Introduction
------------

This package contains an an adapter to connect a heat pump model, based
on the `TESPy <https://github.com/oemof/tespy>`_ library, to *mosaik*.

Installation & Tests
--------------------

You can install mosaik-heatpump with pip:

.. code-block:: bash

You can run the tests with:

.. code-block:: bash

Heat Pump Model
---------------

TESPy
^^^^^
TESPy (Thermal Engineering Systems in Python) provides a powerful simulation package for thermal processes 
like power plants, district heating systems, heat pumps etc. For more information about the library, please 
refer to its `documentation <https://tespy.readthedocs.io/en/master/>`_.

Model
^^^^^
The heat pump model provided in this package is based on the model used in TESPy's 
`heat pump tutorial <https://tespy.readthedocs.io/en/master/tutorials_examples.html#heat-pump-tutorial>`_.

Basic
"""""

In the package, the following two heat pump models have been provided:
1) Water/Water Heat Pump-
For this model, the heat source is underground water and the fluid on the consumer side is also water. This model can be chosen by specifying
the parameter *heat_source* as *water*.
2) Air/Water Heat Pump: 
For this model, the heat source is ambient air and the fluid on the consumer side is water. This model can be chosen by specifying
the parameter *heat_source* as *air*.

**Range of Operation of the models to be mentioned?**

Inputs

For each time step of the simulation, the following two inputs can be provided to the model, in a csv file or from another simulation model:
1) Consumer Heat Load, via the *cons_q* parameter 
2) Ambient Temperature, via the *amb_T* parameter

Outputs

The model gives the following outputs for each time step:
1) Coefficient of Performance (COP) of the heat pump
2) Power requirement (W) of the heat pump

Advanced
""""""""
The heat pump model available in TESPy's library was modified and the new schematic of the system is shown below.

**Insert Image**

**Breifly describe the changes made to the components**
The consumer system and the expansion valve are unchanged. In the evaporator system, the superheater has been eliminated.
The compressor system consists only of a single compression stage and intercooling is no longer required.

Following the tutorial, the parametrization, for the heat pump models provided in this package, has been done to match the manufacturer's 
datasheets.
1) Water/Water Heat Pump- This model is based on Daikin's Water/Water Heat Pump 
(` Model EWWP014KBW1N <https://www.daikin.eu/en_us/products/EWWP-KBW1N.table.html>`_).
2) Air/Water Heat Pump- This model is based on Daikin's Air/Water Heat Pump 
(` Model  ERLQ016CAV3 <https://www.daikin.eu/en_us/products/EHBH-CB---ERLQ-CV3.table.html>`_).


*Componet Parametrization*
The parametrization of the components of the system was only slightly modified when compared to the tutorial.
In the consumer system, for the water/water heat pump, the parameter 'ttd_u' wasn't specified for the condenser as an additional parameter in
the evaporator system was available from the datasheet. However, for the air/water heat pump, such data was not available and therefore the 'ttd_u'
of the condenser was adjusted to get an output close to the expected value. 

In the evaporator system, the same parametrization as in the tutorials is used, with only the 'ttd_l' of the evaporator specified as 2 instead of 5.
The parametrization of the newly added ambient pump is the same as that of the other pumps in the tutorial.

For the off-design calculations, the default characteristic lines provided by TESPy for the components (condenser, evaporator, pumps, compressor)
were used. However, it is possible to use other charactersitic line/maps through TESPy. Please refer to TESPy's documentation for further details
on this.

For the compressor, the parameters are same as those used in the tutorial.

*Connection Parametrization*
While the parameters specficed for the components match those in the tutorial, the values of the parameters vary considerably.
In the consumer system, the condenser outlet temperature, consumer return temperature & the consumer heat load have been taken from the datasheets.
For the evaporator system connections, again the values from the datasheets are used for the parameters. For the water/water heat pump, the flowrate
of the evaporator cold side fluid was datasheet. However, the same wasn't available for the air/water heat pump and only the temperature
values were specified as per the datasheet. 

Moreover, in the *fluids* parameter, the refrigerant used in the system was changed from 'NH3' to 'R407c' & 'R410a' for the water & 
air heat pumps respectively.

*Starting Values*
For the different connections, specifying appropriate starting values for parameters like pressure or enthalpy is crucial to obtain the right results. 
Especially for the phase change processes, based on the expected temperature range of the refrigerant in the condenser and evaporator systems,
the values of enthalpy and pressure have to be obtained from the fluid property diagrams. Not specifying appropriate starting values may lead to 
incorrect results or even errors in some cases.

**Advice for other models** 
* Always have a look at a fluid proprety diagram when checking different refrigerants to find appropriate starting values. There are various
tools, e.g. CoolProp(fluid property database of TESPy)or FluProDia(https://fluprodia.readthedocs.io/).
* Build up your model step by step and make a drawing of the process marking where you specify which parameter.
* Use starting values if necessary. Also, if you build up your model step by step you will see, where starting values are useful and where you can 
skip on them.

** design parameters - 'v' (constant part load pumping in comment') & 'T', do they impact the result? Are they the reason for divergent results for 
high temp water & air heat pumps?**

Getting help
------------
 


