Analyzing Scenario Designs
--------------------------
Analysis of Transmission Upgrades
+++++++++++++++++++++++++++++++++
Cumulative Upgrade Quantity
###########################
Using the change table of a scenario, the number of upgrades lines/transformers and
their cumulative upgraded capacity (for transformers) and cumulative upgraded
megawatt-miles (for lines) can be calculated with:

.. code-block:: python

    powersimdata.design.transmission.mwmiles.calculate_mw_miles(scenario)


where ``scenario`` is a ``Scenario`` instance.


Classify Upgrades
#################
The upgraded branches can also be classified into either interstate or intrastate
branches by calling:

.. code-block:: python

    powersimdata.design.transmission.statelines.classify_interstate_intrastate(scenario)

where ``scenario`` is a ``Scenario`` instance.


Analysis of Generation Upgrades
+++++++++++++++++++++++++++++++
Accessing and Saving Relevant Supply Information
################################################
Analyzing generator supply and cost curves requires the proper generator cost and plant
information to be accessed from a ``Grid`` object. This data can be accessed using the
following:

.. code-block:: python

     from powersimdata.design.generation.cost_curves import get_supply_data

    supply_df = get_supply_data(grid, num_segments, save)

where ``grid`` is a ``Grid`` object, ``num_segments`` is the number of linearized cost
curve segments into which the provided quadratic cost curve should be split, and
``save`` is a string representing the desired file path and file name to which the
resulting data will be saved. ``save`` defaults to ``None``. ``get_supply_data()``
returns a ``pandas.DataFrame`` that contains information about each generator's fuel
type, quadratic cost curve, and linearized cost curve, as well as the interconnect and
load zone to which the generator belongs. ``get_supply_data()`` is used within many of
the following supply and cost curve visualization and analysis functions.


Visualizing Generator Supply Curves
###################################
To obtain the supply curve for a particular fuel type and area, the following is used:

.. code-block:: python

    from powersimdata.design.generation.cost_curves import build_supply_curve

    P, F = build_supply_curve(grid, num_segments, area, gen_type, area_type, plot)

where ``grid`` is a ``Grid`` object; ``num_segments`` is the number of linearized cost
curve segments to create; ``area`` is a string describing an appropriate load zone,
interconnect, or state; ``gen_type`` is a string describing an appropriate fuel type;
``area_type`` is a string describing the type of region that is being considered; and
``plot`` is a boolean that indicates whether or not the plot is shown. ``area_type``
defaults to ``None``, which allows the area type to be inferred; there are instances
where specifying the area type can be useful (e.g., Texas can refer to both a state and
an interconnect, though they are not the same thing). ``plot`` defaults to ``True``.
``build_supply_curve()`` returns ``P`` and ``F``, the supply curve capacity and price
quantities, respectively.


Comparing Supply Curves
#######################
When updating generator cost curve information, it can be useful to see the
corresponding effect on the supply curve for a particular area and fuel type pair.
Instead of only performing a visual inspection between the original and new supply
curves, the maximum price difference between the two supply curves can be calculated.
This metric, which is similar to the Kolmogorov-Smirnov test, serves as a
goodness-of-fit test between the two supply curves, where a lower score is desired. This
metric can be calculated as follows:

.. code-block:: python

    from powersimdata.design.generation.cost_curves import ks_test

    max_diff = ks_test(P1, F1, P2, F2, area, gen_type, plot)

where ``P1`` and ``P2`` are lists containing supply curve capacity data; ``F1`` and
``F2`` are lists containing corresponding supply curve price data; ``area`` is a string
describing an appropriate load zone, interconnect, or state; ``gen_type`` is a string
describing an appropriate fuel type; and ``plot`` is a boolean that indicates whether or
not the plot is shown. The pairs of supply curve data, (``P1``, ``F1``) and (``P2``,
``F2``), can be created using ``build_supply_curve()`` or can be created manually.  It
should be noted that the two supply curves must offer the same amount of capacity (i.e.,
``max(P1) = max(P2)``). ``area`` and ``gen_type`` both default to ``None``. ``plot``
defaults to ``True``. ``ks_test()`` returns ``max_diff``, which is the maximum price
difference between the two supply curves.


Comparing Cost Curve Parameters
###############################
When designing generator cost curves, it can be instructive to visually compare the
quadratic cost curve parameters for generators in a particular area and fuel type pair.
The linear terms (``c1``) and quadratic terms (``c2``) for a given area and fuel type
can be compared in a plot using the following:

.. code-block:: python

    from powersimdata.design.generation.cost_curves import plot_linear_vs_quadratic_terms

    plot_linear_vs_quadratic_terms(grid, area, gen_type, area_type, plot, zoom, num_sd, alpha)

where ``grid`` is a ``Grid`` object; ``area`` is a string describing an appropriate load
zone, interconnect, or state; ``gen_type`` is a string describing an appropriate fuel
type; ``area_type`` is a string describing the type of region that is being considered;
``plot`` is a boolean that indicates whether or not the plot is shown; ``zoom`` is a
boolean that indicates whether or not the zoom capability that filters out quadratic
term outliers for better visualization is enabled; ``num_sd`` is the number of standard
deviations outside of which quadratic terms are filtered; and ``alpha`` is the alpha
blending parameter for the scatter plot. ``area_type`` defaults to ``None``, which
allows the area type to be inferred. ``plot`` defaults to ``True``. ``zoom`` defaults to
``False``. ``num_sd`` defaults to 3. ``alpha``, which can take values between 0 and
1, defaults to 0.1.


Comparing Generators by Capacity and Price
##########################################
When designing generator cost curves, it can be useful to visually compare the capacity
and price parameters for each generator in a specified area and fuel type pair. The
generator capacity and price parameters for a given area and fuel type can be compared
in a plot using the following:

.. code-block:: python

    from powersimdata.design.generation.cost_curves import plot_capacity_vs_price

    plot_capacity_vs_price(grid, num_segments, area, gen_type, area_type, plot)

where ``grid`` is a ``Grid`` object; ``num_segments`` is the number of linearized cost
curve segments to create; ``area`` is a string describing an appropriate load zone,
interconnect, or state; ``gen_type`` is a string describing an appropriate fuel type;
``area_type`` is a string describing the type of region that is being considered; and
``plot`` is a boolean that indicates whether or not the plot is shown. ``area_type``
defaults to ``None``, which allows the area type to be inferred. ``plot`` defaults to
``True``.
