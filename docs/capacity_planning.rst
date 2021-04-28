Capacity Planning Framework
---------------------------
The capacity planning framework is intended to estimate the amount of new capacity that
will be required to meet future clean energy goals.


Required Inputs
+++++++++++++++
At minimum, this framework requires a *reference* ``Scenario`` object--used to specify
the current capacities and capacity factors of resources which *count* towards
state-level clean energy goals (this ``Scenario`` object must be in **analyze**
state)--and a list of target areas (comprised of one or more zones) and their target
clean energy penetrations. A strategy must also be specified, either ``independent``
(each area meets it own goal) or ``collaborative`` (all areas with non-zero goals work
together to meet a shared goal, resembling REC trading).

The list of targets may be specified in either a CSV file or a data frame, as long as
the required columns are present: ``region_name`` and ``ce_target_fraction``. Optional
columns are: ``allowed_resources`` (defaulting to solar & wind),
``external_ce_addl_historical_amount`` (clean energy not modeled in our grid, defaulting
to 0), and ``solar_percentage`` (how much of the new capacity will be solar, defaulting
to the current solar:wind ratio. This input only applies to the *independent* strategy,
a shared-goal new solar fraction for *collaborative* planning is specified in the
function call to ``calculate_clean_capacity_scaling``.


Optional Inputs
+++++++++++++++
Since increasing penetration of renewable capacity is often associated with increased
curtailment, an expectation of this new curtailment can be passed as the
``addl_curtailment`` parameter. For the *collaborative* method, this must be passed as a
dictionary of ``{resource_name: value}`` pairs, for the *independent* method this must
be passed as a data frame or as a two-layer nested dictionary which can be interpreted
as a data frame. For either method, additional curtailment must be a value between 0 and
1, representing a percentage, not percentage points. For example, if the previous
capacity factor was 30%, and additional curtailment of 10% is specified, the expected
new capacity factor will be 27%, not 20%.

Another ``Scenario`` object can be passed as ``next_scenario`` to specify the magnitude
of future demand (relevant for energy goals which are expressed as a fraction of total
consumption); this `Scenario` object may be any state, as long as
``Scenario.get_demand()`` can be called successfully, i.e., if the ``Scenario`` object
is in **create** state, an interconnection must be defined. This allows calculation of
new capacity for a scenario which is being designed, using the demand scaling present in
the change table.

Finally, for the *collaborative* method, a ``solar_fraction`` may be defined, which
determines scenario-wide how much of the new capacity should be solar (the remainder
will be wind).


Example Capacity Planning Function Calls
++++++++++++++++++++++++++++++++++++++++
Basic independent call, using the demand from the reference scenario to approximate the
future demand:

.. code-block:: python

    from powersimdata.design.generation.clean_capacity_scaling import calculate_clean_capacity_scaling
    from powersimdata.scenario.scenario import Scenario

    ref_scenario = Scenario(403)
    targets_and_new_capacities_df = calculate_clean_capacity_scaling(
        ref_scenario,
        method="independent",
        targets_filename="eastern_2030_clean_energy_targets.csv"
    )


Complex collaborative call, using all optional parameters:

.. code-block:: python

    from powersimdata.design.generation.clean_capacity_scaling import calculate_clean_capacity_scaling
    from powersimdata.scenario.scenario import Scenario

    ref_scenario = Scenario(403)
    # Start building a new scenario, to plan capacity for greater demand
    new_scenario = Scenario()
    new_scenario.set_grid("Eastern")
    zone_demand_scaling = {"Massachusetts": 1.1, "New York City": 1.2}
    new_scenario.change_table.scale_demand(zone_name=zone_demand_scaling)
    # Define additional expected curtailment
    addl_curtailment = {"solar": 0.1, "wind": 0.15}

    targets_and_new_capacities_df = calculate_clean_capacity_scaling(
      ref_scenario,
      method="collaborative",
      targets_filename="eastern_2030_clean_energy_targets.csv",
      addl_curtailment=addl_curtailment,
      next_scenario=new_scenario,
      solar_fraction=0.55
    )


Creating a Change Table from Capacity Planning Results
++++++++++++++++++++++++++++++++++++++++++++++++++++++
The capacity planning framework returns a data frame of capacities by resource type and
target area, but the scenario creation process ultimately requires scaling factors by
resource type and zone or plant id. A function ``create_change_table`` exists to perform
this conversion process. Using a reference scenario, a set of scaling factors by
resource type, zone, and plant id is calculated. When applied to a base ``Grid`` object,
these scaling factors will result in capacities that are nearly identical to the
reference scenario on a per-plant basis (subject to rounding), with the exception of
solar and wind generators, which will be scaled up to meet clean energy goals.

.. code-block:: python

    from powersimdata.design.generation.clean_capacity_scaling import create_change_table

    change_table = create_change_table(targets_and_new_capacities_df, ref_scenario)
    # The change table method only accepts zone names, not zone IDs, so we have to translate
    id2zone = new_scenario.state.get_grid().id2zone
    # Plants can only be scaled one resource at a time, so we need to loop through
    for resource in change_table:
    	new_scenario.change_table.scale_plant_capacity(
    		resource=resource,
    		zone_name={
    			id2zone[id]: value
    			for id, value in change_table[resource]["zone_name"].items()
    		},
    		plant_id=change_table[resource]["zone_name"]
    	)
