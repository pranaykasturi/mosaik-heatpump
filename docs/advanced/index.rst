Integrating new heat pumps
==========================

.. toctree::
   :maxdepth: 1
   :hidden:

   step1
   step2
   step3

While the *hplib* heat pump model available in the package can simulate
the performance of the different heat pumps  from the `keymark data
<https://keymark.eu/en/products/heatpumps/certified-products>`_, the *tespy*
model provides fewer options. In order to simulate different heat pumps,
apart from the ones already available in this package, the heat pumps have
to be intergrated to the *tespy* model. An example of the integration of
the *“Air_30kW”* heat pump, based on `“ait-deutschland LW-300(L)” <https://
www.alpha-innotec.ch/alpha-innotec/produkte/waermepumpen/luftwasser/lw-300
-l.html>`_, shows the procedure in detail. The development of the model to
simulate the performance of this specific heat pump is described in the
steps below:

    **Step 1**: :doc:`Initial Parametrization <./step1>`

    **Step 2**: :doc:`Compressor efficiency map <./step2>`

    **Step 3**: :doc:`'fast' mode data <./step3>`

