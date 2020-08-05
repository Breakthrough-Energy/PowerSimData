[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
![Pytest](https://github.com/intvenlab/PowerSimData/workflows/Run%20pytest/badge.svg)

# PowerSimData
This package has been written in order to carry out power flow study in the
U.S. electrical grid. This framework allows the user to easily build extensive
scenarios. A scenario is defined by the following objects:
* **the power grid**, an interconnected network delivering electricity
from producers to load buses and consisting of:
  - thermal (coal, natural gas, etc.) and renewable generators (wind turbines,
    etc.) that produce electrical power.
  - substations that change voltage levels (from high to low, or the reverse)
  - transmission lines that carry power from one place to the other (between
    two substations, between a substation and load bus, between a generator bus
    and a substation, etc.). Both, high voltage AC and DC lines are used in our
    model.
  - generator cost curve that specifies the cost as a function of power
  generated ($/MWh). These are determined by fuel cost and generator efficiency.
* the **time series** for renewable generators and demand. These profiles
  are calculated in the [PreREISE] package and the list of profiles generated can be
  consulted [here](https://github.com/intvenlab/PreREISE/tree/develop/docs):
  - the profile for the renewable generators consists of hourly power output.
  - the load profile gives the hourly demand (MW) in various load zones, which are
  geographic entities such as a state or a portion of a state.
* a **change table** used to alter the grid and profiles. To illustrate:
  - generators and transmission lines (AC and DC) capacity can be scaled up
  and down.
  - storage units, generators and transmission lines can be added.
* some **setup parameters** such as the start and end date along with the
duration of the intervals. The simulation engine can also be selected in the
building phase of the scenario.

The `Scenario` class handles the following tasks:
* build a scenario (**create** state);
* launch the scenario and extract the output data (**execute** state);
* retrieve the output data (**analyze** state);
* delete a scenario (**delete** state);
* move a scenario to a backup disk

When a `Scenario` class is instantiated, its state is set either to **create**,
**execute** or **analyze**. The initial state of the `Scenario` object is set in the
constructor of the class. Only one argument (type `str`) is required to create a
`Scenario` object:
* an empty string instantiates the `Scenario` class in the **create** state. A scenario
can then be built.
* If a valid scenario identification number or name is provided:
  - if the scenario has been ran and its output data have been extracted, the state
  will be set to **analyze**.
  - If the scenario has only been created or ran but not extracted the state will be
  then set to **execute**.

Note that instantiating a `Scenario` object with a string that doesn't match any
existing scenarios identification number or name will result in a printout of the list
of existing scenarios and their information.



## 1. Scenario Manipulation
This section illustrates the functionalities of the `Scenario` class.


### A. Retrieving Scenario Output Data
When the `Scenario` object is in the **analyze** state, the user can access various
scenario information and data. The following code snippet lists the methods implemented
to do so.
```python
from powersimdata.scenario.scenario import Scenario

scenario = Scenario('87')
# print name of Scenario object state
print(scenario.state.name)

# print scenario information
scenario.state.print_scenario_info()

# get change table
ct = scenario.state.get_ct()
# get grid
grid = scenario.state.get_grid()

# get demand profile
demand = scenario.state.get_demand()
# get hydro profile
hydro = scenario.state.get_hydro()
# get solar profile
solar = scenario.state.get_solar()
# get wind profile
wind = scenario.state.get_wind()

# get generation profile for generators
pg = scenario.state.get_pg()
# get generation profile for storage units (if present in scenario)
pg_storage = scenario.state.get_storage_pg()
# get energy state of charge of storage units (if present in scenario)
e_storage = scenario.state.get_storage_e()
# get power flow profile for AC lines
pf_ac = scenario.state.get_pf()
# get power flow profile for DC lines
pf_dc = scenario.state.get_dcline_pf()
# get locational marginal price profile for each bus
lmp = scenario.state.get_lmp()
# get congestion (upper power flow limit) profile for AC lines
congu = scenario.state.get_congu()
# get congestion (lower power flow limit) profile for AC lines
congl = scenario.state.get_congl()
# get time averaged congestion (lower and power flow limits) for AC lines
avg_cong = scenario.state.get_averaged_cong()
# get load shed profile for each load bus
load_shed = scenario.state.get_load_shed()
```
If generators or AC/DC lines have been scaled or added to the grid, and/or if the
demand in one or multiple load zones has been scaled for this scenario then the change
table will enclose these changes and the retrieved grid and profiles will be modified
accordingly. Note that the analysis of the scenario using the output data is done in
the [PostREISE] package.


### B. Creating a Scenario
A scenario can be created using few lines of code. This is illustrated below:
```python
from powersimdata.scenario.scenario import Scenario

scenario = Scenario('')
# print name of Scenario object state
print(scenario.state.name)

# Start building a scenario
scenario.state.set_builder(['Western'])

# set plan and scenario names
scenario.state.builder.set_name('test', 'dummy')
# set start date, end date and interval
scenario.state.builder.set_time('2016-08-01 00:00:00',
                                '2016-08-31 23:00:00',
                                '24H')
# set demand profile version
scenario.state.builder.set_base_profile('demand', 'v4')
# set hydro profile version
scenario.state.builder.set_base_profile('hydro', 'v2')
# set solar profile version
scenario.state.builder.set_base_profile('solar', 'v4.1')
# set wind profile version
scenario.state.builder.set_base_profile('wind', 'v5.2')

# scale capacity of solar plants in WA and AZ by 5 and 2.5, respectively
scenario.state.builder.change_table.scale_plant_capacity(
    'solar', zone_name={'Washington': 5, 'Arizona': 2.5})
# scale capacity of wind farms in OR and MT by 1.5 and 2, respectively
scenario.state.builder.change_table.scale_plant_capacity(
    'wind', zone_name={'Oregon': 1.5, 'Montana Western': 2})
# scale capacity of branches in NV and WY by 2
scenario.state.builder.change_table.scale_branch_capacity(
    zone_name={'Nevada': 2, 'Wyoming': 2})

# add AC lines in NM and CO
scenario.state.builder.change_table.add_branch(
    [{'capacity': 200, 'from_bus_id': 2053002, 'to_bus_id': 2053303},
     {'capacity': 150, 'from_bus_id': 2060002, 'to_bus_id': 2060046}])

# add DC line between CO and CA (Bay Area)
scenario.state.builder.change_table.add_dcline(
    [{"capacity": 2000, "from_bus_id": 2060771, "to_bus_id": 2021598}])

# add a solar plant in NV, a coal plant in ID and a natural gas plant in OR
scenario.state.builder.change_table.add_plant(
    [{'type': 'solar', 'bus_id': 2030454, 'Pmax': 75},
     {"type": "coal", "bus_id": 2074334, "Pmin": 25, "Pmax": 750, "c0": 1800, "c1": 30, "c2": 0.0025},
     {"type": "ng", "bus_id": 2090018, "Pmax": 75, "c0": 900, "c1": 30, "c2": 0.0015}])

# get grid used in scenario
grid = scenario.state.get_grid()
# get change table used to alter the base grid.
ct = scenario.state.get_ct()
```
It can be convenient to clear the change table when creating a scenario. Let's say for
instance that a wrong scaling factor has been applied or a generator has been attached
to the wrong bus. To do so, the `clear` method of the `ChangeTable` class can be used.

There are also a couple of more advanced methods which can selectively scale
branches based on the topology of the existing grid, or based on power flow
results from a previous scenario. These can be called as:
```python
scenario.state.builder.change_table.scale_renewable_stubs()
```
or
```python
scenario.state.builder.change_table.scale_congested_mesh_branches(ref_scenario)
```
where `ref_scenario` is a Scenario object in **analyze** state.

The final step is to run `create_scenario()`:
```python
# review information
scenario.state.print_scenario_info()
# create scenario
scenario.state.create_scenario()
# print name of Scenario object state
print(scenario.state.name)
# print status of scenario
scenario.state.print_scenario_status()
```
Once the scenario is successfully created, a scenario id is printed on screen
and the state of the `Scenario` object is switched to **execute**.
printed on screen.


### C. Running the Scenario and Extracting Output Data
It is possible to execute the scenario immediately right after it has been
created. One can also create a new `Scenario` object. This is the option we
follow here.

The **execute** state accomplishes the three following tasks:
* It prepares the simulation inputs: the scaled profiles and the MAT-file enclosing all the information related to the electrical grid.
* It launches the simulation. The status of the simulation can be accessed
using the `print_scenario_status` method. Once the status has switched from **running**
to **finished**, output data are ready to be extracted.
* It extracts the output data. This operation can only be done once the simulation has
finished running.

```python
from powersimdata.scenario.scenario import Scenario

scenario = Scenario('dummy')
# print scenario information
scenario.print_scenario_info()

# prepare simulation inputs
scenario.state.prepare_simulation_input()

# launch simulation
process_run = scenario.state.launch_simulation()

# Get simulation status
scenario.state.print_scenario_status()

# Extract data
process_extract = scenario.state.extract_simulation_output()
```
As an optional parameter, the number of threads used to run the simulation can
be specified using for example:
```python
process_run = scenario.state.launch_simulation(threads=8)
```


### D. Deleting a Scenario
A scenario can be deleted. All the input and output files as well as any entries
in monitoring files will be removed. The **delete** state is only accessible
from the **analyze** state.
```python
from powersimdata.scenario.scenario import Scenario
from powersimdata.scenario.delete import Delete

scenario = Scenario('dummy')
# print name of Scenario object state
print(scenario.state.name)
# print list of accessible states
print(scenario.state.allowed)

# switch state
scenario.change(Delete)
# print name of Scenario object state
print(scenario.state.name)

# delete scenario
scenario.state.delete_scenario()
```


### E. Moving a Scenario to Backup disk
A scenario can be move to a backup disk. The **move** state is only accessible from the
**analyze** state. The code snippet below shows
```python
from powersimdata.scenario.scenario import Scenario
from powersimdata.scenario.move import Move

scenario = Scenario('dummy')
# print name of Scenario object state
print(scenario.state.name)
# print list of accessible states
print(scenario.state.allowed)

# switch state
scenario.change(Move)
# print name of Scenario object state
print(scenario.state.name)

# move scenario
scenario.state.move_scenario()
```


## 2. U.S. Electric Grid and Interconnection
A `Grid` object encapsulates all the information related to the synthetic
network used in this project for a single interconnection (**Eastern**,
**Texas** or **Western**), a combination of two interconnections (**Eastern**
and **Texas** for example) or the full U.S. electric grid (**USA**). Only one
argument is required to instantiate the `Grid` class, a `list` of
interconnections (as `str`) in any order.
```python
from powersimdata.input.grid import Grid
western_texas = Grid(['Western', 'Texas'])
```
The object has various attributes. These are listed below and a short
description is given:
* **zone2id (id2zone)**: `dict` -- load zone name (load zone id) to load zone id
(load zone name).
* **type2id** (**id2type**): `dict` -- generator type (id) to generator id
(type).
* **type2color**: `dict` -- generator type to generator color as used in plots.
* **interconnect**: `str` --  interconnection name.
* **bus**: `pandas.DataFrame` -- bus id as index and bus characteristics as
columns.
* **sub**: `pandas.DataFrame` -- substation id as index and substation
information as columns.
* **bus2sub**: `pandas.DataFrame` -- bus id as index and substation id as
column.
* **plant**: `pandas.DataFrame` -- plant id as index and plant characteristics
as columns.
* **branch**: `pandas.DataFrame` -- branch id as index and branch
characteristics as columns.
* **gencost**: `dict` -- has two keys: `before` and `after`. Values are
`pandas.DataFrame` with plant id as index and generator cost curve information as
columns. The `before` key points to the original set of cost curves (polynomials)
whereas the `after` key gives the ones that has been used in the simulation
(linearized or piece-wise linearized version).
* **dcline**: `pandas.DataFrame` -- DC line id as index and DC line
characteristics as columns.
```python
from powersimdata.input.grid import Grid
usa = Grid(['USA'])
usa.plant.head()
# get all wind farm in the U.S. electrical grid
wind_farm = usa.plant.groupby('type').get_group('wind')
# get DC lines in the grid
dcline = usa.dcline
```
The synthetic U.S. network used in our simulation framework can be found at
the following url: <https://electricgrids.engr.tamu.edu>. Our team has altered
the original network in many ways to make it more realistic. These have been achieved
by comparing our simulation results with historical generation level. Our data
along with their description can be found on [zenodo].



## 3. Capacity Planning Framework
The capacity planning framework replaces an earlier spreadsheet method with a
more flexible design backed up by tests. Additionally, scenario specific
parameters are now automatically imported. More information can be found at
this Dropbox location:

Dropbox(IVL)/Results/DataAnalysis/RenewablesScalingForScenarios/Clean Energy Capacity Planning Framework.pptx

Importing the framework:
``` python
from powersimdata.design.clean_capacity_scaling import (CollaborativeStrategyManager,
                                                        IndependentStrategyManager,
                                                        TargetManager,
                                                        ResourceManager,
                                                        Resource)
import pandas as pd
```


### A. Create Strategy Object that will generate next capacities
Currently two strategies (independent and collaborative) are implemented. The first
step is create an empty strategy object:
``` python
independent_strategy_manager = IndependentStrategyManager()
collaborative_strategy_manager = CollaborativeStrategyManager()
```


### B. Use spreadsheet of external information for bulk creation of region target objects
Then we need to populate the strategy object with regional target information.
Currently target information is ingested using a specially formatted csv file.
```python
targets_info_location = 'Eastern Scenario Target Info.csv'
eastern_targets = pd.read_csv(targets_info_location)

# populate strategy objects with target info
independent_strategy_manager.targets_from_data_frame(eastern_targets)
collaborative_strategy_manager.targets_from_data_frame(eastern_targets)
```


### C. Populate region target objects with resource info
Now that we have regional target information, we need to gather regional resource information from a particular scenario run. The `ScenarioInfo` object is used to
calculate resource properties that are added to the regional target objects.
```python
from powersimdata.scenario.scenario import Scenario
from powersimdata.design.scenario_info import ScenarioInfo
# load in relevant scenario
scenario_string = '394'
scenario = Scenario(scenario_string)

# create ScenarioInfo object
scenario_info = ScenarioInfo(scenario)

# define start and end times of the simulation
start_time = '2016-01-01 00:00:00'
end_time = '2016-12-31 23:00:00'

# add resource objects to regional targets
independent_strategy_manager.populate_targets_with_resources(
    scenario_info, start_time, end_time):
collaborative_strategy_manager.populate_targets_with_resources(
    scenario_info, start_time, end_time):
```


### D. Optional step: Set additional curtailment for regional resources
Additional curtailment is a parameter to iterate from initial anchor scenario results
(defined as a scenario to manually make adjustments from to account for nonlinearities
in grid curtailment)

For Independent strategies, the interface to set these values has the form:
```python
independent_strategy_manager.set_addl_curtailment(
    {'Alabama':{'solar': 0.2}, 'Maryland': {'wind': 0.1}})
```
which sets additional curtailment for a region and particular resource type. In this
example, the value `0.2` denotes a 20% reduction of solar capacity factor compared to
the reference scenario.

For Collaborative strategies, the interface to set these values has the form:
```python
collaborative_strategy_manager.set_collab_addl_curtailment(
    {'solar': 0.2, 'wind': 0.1})
```
which sets additional curtailment for particular resource types in all regions. In this
example, the value `0.2` denotes a 20% reduction of solar capacity factor compared to
the reference scenario.


### E. Calculate Next Capacities
Once the regional target information and scenario-specific resource information, we can
calculate the next capacities.
```python
independent_next_capacities = independent_strategy_manager.data_frame_of_next_capacities()
collaborative_next_capacities = collaborative_strategy_manager.data_frame_of_next_capacities()
```


### F. Future Feature
Direct output of the new change table.


[PreREISE]: https://github.com/intvenlab/PreREISE
[PostREISE]: https://github.com/intvenlab/PostREISE
[zenodo]: https://zenodo.org/record/3753177#.XugHbS2z124
