Scenario Framework
------------------
A scenario is defined by the following objects:

- a **power grid**, an interconnected network delivering electricity from producers
  to load buses and consisting of:

  - thermal (coal, natural gas, etc.) and renewable generators (wind turbines, etc.)
    that produce electrical power
  - substations that change voltage levels (from high to low, or the reverse)
  - transmission lines that carry power from one place to the other (between two
    substations, between a substation and load bus, between a generator bus and a
    substation, etc.) - Both, high voltage AC and DC lines are used in our model
  - generator cost curve that specifies the cost as a function of power generated ($/
    MWh) - These are determined by fuel cost and generator efficiency

- **time series** for renewable generators and demand - These profiles are calculated
  in the `PreREISE <https://github.com/Breakthrough-Energy/PreREISE>`_ package

  - profile for the renewable generators consists of hourly power output
  - load profile gives the hourly demand (MW) in various load zones, which are
    geographic entities such as a state or a portion of a state

- a **change table** used to alter the grid and profiles. To illustrate:

  - generators and transmission lines (AC and DC) capacity can be scaled up and down
  - storage units, generators and transmission lines can be added

- some **simulation parameters** such as the start and end date along with the duration
  of the intervals

The ``Scenario`` class handles the following tasks:

- Build a scenario (**create** state)
- Launch the scenario and extract the output data (**execute** state)
- Retrieve the output data (**analyze** state)
- Delete a scenario (**delete** state)
- Move a scenario to a backup disk (**move** state)

When a ``Scenario`` class is instantiated, its state is set either to **create**,
**execute** or **analyze**. The initial state of the ``Scenario`` object is set in the
constructor of the class. The ``Scenario`` class can be instantiated as follows:

- no parameter will instantiate the `Scenario` class in the **create** state and a new
  scenario can then be built
- a valid scenario identification number (``str`` or ``int``) or name (``str``) - Then:

  - if the scenario has been ran and its output data have been extracted, it will be
    in the **analyze** state
  - If the scenario has only been created or ran but not extracted, it will be in the
    **execute** state

Note that instantiating a ``Scenario`` object with a string that doesn't match any
existing scenarios identification number or name will result in a printout of the list
of existing scenarios and their information.


Creating a Scenario
+++++++++++++++++++
A scenario can be created using few lines of code. This is illustrated below:

.. code-block:: python

    from powersimdata.scenario.scenario import Scenario

    scenario = Scenario()
    # print name of Scenario object state
    print(scenario.state.name)

    # Start building a scenario
    scenario.set_grid(grid_model="usa_tamu", interconnect="Western")

    # set plan and scenario names
    scenario.set_name("test", "dummy")
    # set start date, end date and interval
    scenario.set_time("2016-08-01 00:00:00", "2016-08-31 23:00:00", "24H")
    # set demand profile version
    scenario.set_base_profile("demand", "vJan2021")
    # set hydro profile version
    scenario.set_base_profile("hydro", "vJan2021")
    # set solar profile version
    scenario.set_base_profile("solar", "vJan2021")
    # set wind profile version
    scenario.set_base_profile("wind", "vJan2021")

    # scale capacity of solar plants in WA and AZ by 5 and 2.5, respectively
    scenario.change_table.scale_plant_capacity(
      "solar", zone_name={"Washington": 5, "Arizona": 2.5})
    # scale capacity of wind farms in OR and MT by 1.5 and 2, respectively
    scenario.change_table.scale_plant_capacity(
        "wind", zone_name={"Oregon": 1.5, "Montana Western": 2})
    # scale capacity of branches in NV and WY by 2
    scenario.change_table.scale_branch_capacity(
        zone_name={"Nevada": 2, "Wyoming": 2})

    # add AC lines in NM and CO
    scenario.change_table.add_branch(
        [{"capacity": 200, "from_bus_id": 2053002, "to_bus_id": 2053303},
         {"capacity": 150, "from_bus_id": 2060002, "to_bus_id": 2060046}])

    # add DC line between CO and CA (Bay Area)
    scenario.change_table.add_dcline(
        [{"capacity": 2000, "from_bus_id": 2060771, "to_bus_id": 2021598}])

    # add a solar plant in NV, a coal plant in ID and a natural gas plant in OR
    scenario.change_table.add_plant(
        [{"type": "solar", "bus_id": 2030454, "Pmax": 75},
         {"type": "coal", "bus_id": 2074334, "Pmin": 25, "Pmax": 750, "c0": 1800, "c1": 30, "c2": 0.0025},
         {"type": "ng", "bus_id": 2090018, "Pmax": 75, "c0": 900, "c1": 30, "c2": 0.0015}])

    # add a new bus, and a new one-way DC line connected to this bus
    scenario.change_table.add_bus(
    	[{"lat": 48, "lon": -125, "zone_id": 201, "baseKV": 138}])
    scenario.state.builder.change_table.add_dcline(
    	[{"from_bus_id": 2090023, "to_bus_id": 2090024, "Pmin": 0, "Pmax": 200}])

    # get grid used in scenario
    grid = scenario.get_grid()
    # get change table used to alter the base grid.
    ct = scenario.get_ct()

It can be convenient to clear the change table when creating a scenario. Let's say for
instance that a wrong scaling factor has been applied or a generator has been attached
to the wrong bus. To do so, the ``clear`` method of the ``ChangeTable`` class can be
used.

There are also a couple of more advanced methods which can selectively scale branches
based on the topology of the existing grid, or based on power flow results from a
previous scenario. These can be called as:

.. code-block:: python

    scenario.state.builder.change_table.scale_renewable_stubs()

or

.. code-block:: python

    scenario.state.builder.change_table.scale_congested_mesh_branches(ref_scenario)

where ``ref_scenario`` is a ``Scenario`` object in **analyze** state.

The final step is to run the ``create_scenario`` method:

.. code-block:: python

    # review information
    scenario.print_scenario_info()
    # create scenario
    scenario.create_scenario()
    # print name of Scenario object state
    print(scenario.state.name)
    # print status of scenario
    scenario.print_scenario_status()

Once the scenario is successfully created, a scenario id is printed on screen and the
state of the `Scenario` object is switched to **execute**. printed on screen.


Running the Scenario and Extracting Output Data
+++++++++++++++++++++++++++++++++++++++++++++++
It is possible to execute the scenario immediately right after it has been created. One
can also create a new `Scenario` object. This is the option we follow here.

The **execute** state accomplishes the three following tasks:

- Prepare simulation inputs: the scaled profiles and the MAT-file enclosing all the
  information related to the electrical grid
- Launch the simulation
- Extract output data - This operation is performed once the simulation has finished
  running.

.. code-block:: python

    from powersimdata.scenario.scenario import Scenario

    scenario = Scenario("dummy")
    # print scenario information
    scenario.print_scenario_info()

    # prepare simulation inputs
    scenario.prepare_simulation_input()

    # launch simulation
    process_run = scenario.launch_simulation()

    # Get simulation status
    scenario.print_scenario_status()

Note that the status of the simulation can be accessed using the
``print_scenario_status`` method.

As an optional parameter, the number of threads used to run the simulation can be
specified using for example:

.. code-block:: python

    process_run = scenario.state.launch_simulation(threads=8)

Extracting data from the simulation engine outputs can be a memory intensive process. If
there are resource constraints where the engine resides, it is possible to pause the
data from being extracted using an optional parameter and then manually extracting the
data at a suitable time:

.. code-block:: python

    process_run = scenario.launch_simulation(extract_data=False)
    # Extract data
    process_extract = scenario.extract_simulation_output()

Note that you will need to create a new ``Scenario`` object via the scenario id/name to
access the output data.


Retrieving Scenario Output Data
+++++++++++++++++++++++++++++++
When the ``Scenario`` object is in the **analyze** state, the user can access various
scenario information and data. The following code snippet lists the methods implemented
to do so:

.. code-block:: python

    from powersimdata.scenario.scenario import Scenario

    scenario = Scenario(600)
    # print name of Scenario object state
    print(scenario.state.name)

    # print scenario information
    scenario.print_scenario_info()

    # get change table
    ct = scenario.get_ct()
    # get grid
    grid = scenario.get_grid()

    # get demand profile
    demand = scenario.get_demand()
    # get hydro profile
    hydro = scenario.get_hydro()
    # get solar profile
    solar = scenario.get_solar()
    # get wind profile
    wind = scenario.get_wind()

    # get generation profile for generators
    pg = scenario.get_pg()
    # get generation profile for storage units (if present in scenario)
    pg_storage = scenario.get_storage_pg()
    # get energy state of charge of storage units (if present in scenario)
    e_storage = scenario.get_storage_e()
    # get power flow profile for AC lines
    pf_ac = scenario.get_pf()
    # get power flow profile for DC lines
    pf_dc = scenario.get_dcline_pf()
    # get locational marginal price profile for each bus
    lmp = scenario.get_lmp()
    # get congestion (upper power flow limit) profile for AC lines
    congu = scenario.get_congu()
    # get congestion (lower power flow limit) profile for AC lines
    congl = scenario.get_congl()
    # get time averaged congestion (lower and power flow limits) for AC lines
    avg_cong = scenario.get_averaged_cong()
    # get load shed profile for each load bus
    load_shed = scenario.get_load_shed()

If generators or AC/DC lines have been scaled or added to the grid, and/or if the demand
in one or multiple load zones has been scaled for this scenario then the change table
will enclose these changes and the retrieved grid and profiles will be modified
accordingly. Note that the analysis of the scenario using the output data is done in the
`PostREISE <https://github.com/Breakthrough-Energy/PostREISE>`_ package.


Deleting a Scenario
+++++++++++++++++++
A scenario can be deleted. All the input and output files as well as any entries in
monitoring files will be removed. The **delete** state is only accessible from the
**analyze** state.

.. code-block::python

    from powersimdata.scenario.scenario import Scenario
    from powersimdata.scenario.delete import Delete

    scenario = Scenario("dummy")
    # print name of Scenario object state
    print(scenario.state.name)
    # print list of accessible states
    print(scenario.state.allowed)

    # switch state
    scenario.change(Delete)
    # print name of Scenario object state
    print(scenario.state.name)

    # delete scenario
    scenario.delete_scenario()


Moving a Scenario to Backup disk
++++++++++++++++++++++++++++++++
A scenario can be move to a backup disk. The **move** state is only accessible from the **analyze** state. The functionality is illustrated below:

.. code-block:: python

    from powersimdata.scenario.scenario import Scenario
    from powersimdata.scenario.move import Move

    scenario = Scenario("dummy")
    # print name of Scenario object state
    print(scenario.state.name)
    # print list of accessible states
    print(scenario.state.allowed)

    # switch state
    scenario.change(Move)
    # print name of Scenario object state
    print(scenario.state.name)

    # move scenario
    scenario.move_scenario()
