[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
![Tests](https://github.com/Breakthrough-Energy/PowerSimData/workflows/Pytest/badge.svg)



# PowerSimData
This package has been written in order to carry out power flow study in the U.S. electrical grid. This framework allows the user to easily build extensive scenarios.

PowerSimData is part of a set of packages representing Breakthrough Energy's power system model. More information regarding the installation of the model as well as the contribution guide can be found [here](https://breakthrough-energy.github.io/docs/).


## 1. Setup/Install
Here are the instructions to install the **PowerSimData** package. We strongly recommend that you pick one of the following options.


### A. Using pipenv
If not already done, install `pipenv` (see their [webpage](https://pipenv.pypa.io/en/latest/)) and run:
```bash
pipenv sync
pipenv shell
```
in the root folder of the package. The first command will create a virtual environment and install the dependencies. The second command will activate the environment.


### B. Using the ***requirements.txt*** file
First create an environment using `venv` (more details [here](https://docs.python.org/3/library/venv.html)). Note that `venv` is included in the Python standard library and requires no additional installation. Then, activate your environment and run:
```bash
pip install -r requirements.txt
```
in the root folder of the package.


### C. Path
Whatever method you choose, if you wish to access the modules located in **PowerSimData** from anywhere on your machine, do:
```bash
pip install .
```
in the root folder of your package or alternatively, setup the `PYTHONPATH` global variable to include the folder into which you have cloned the repository.


## 2. Scenario Framework
A scenario is defined by the following objects:
* **The power grid**, an interconnected network delivering electricity from producers to load buses and consisting of:
  - Thermal (coal, natural gas, etc.) and renewable generators (wind turbines, etc.) that produce electrical power
  - Substations that change voltage levels (from high to low, or the reverse)
  - Transmission lines that carry power from one place to the other (between two substations, between a substation and load bus, between a generator bus and a substation, etc.) - Both, high voltage AC and DC lines are used in our model
  - Generator cost curve that specifies the cost as a function of power generated ($/MWh) - These are determined by fuel cost and generator efficiency
* **Time series** for renewable generators and demand - These profiles are calculated in the [PreREISE] package and the list of profiles generated can be consulted through the following links: [demand](https://github.com/Breakthrough-Energy/PreREISE/tree/develop/prereise/gather/demanddata), [hydro](https://github.com/Breakthrough-Energy/PreREISE/tree/develop/prereise/gather/hydrodata), [solar](https://github.com/Breakthrough-Energy/PreREISE/tree/develop/prereise/gather/solardata) and [wind](https://github.com/Breakthrough-Energy/PreREISE/tree/develop/prereise/gather/winddata).
  - Profile for the renewable generators consists of hourly power output
  - Load profile gives the hourly demand (MW) in various load zones, which are geographic entities such as a state or a portion of a state
* **Change table** used to alter the grid and profiles. To illustrate:
  - Generators and transmission lines (AC and DC) capacity can be scaled up and down
  - Storage units, generators and transmission lines can be added
* **Simulation parameters** such as the start and end date along with the duration of the intervals - The simulation engine can also be selected in the building phase of the scenario

The `Scenario` class handles the following tasks:
* Build a scenario (**create** state)
* Launch the scenario and extract the output data (**execute** state)
* Retrieve the output data (**analyze** state)
* Delete a scenario (**delete** state)
* Move a scenario to a backup disk (**move** state)

When a `Scenario` class is instantiated, its state is set either to **create**, **execute** or **analyze**. The initial state of the `Scenario` object is set in the constructor of the class. Only one argument is required to create a `Scenario` object:
* An empty string instantiates the `Scenario` class in the **create** state. A scenario can then be built
* If a valid scenario identification number (`str` or `int`) or name (`str`) is provided:
  - If the scenario has been ran and its output data have been extracted, the state will be set to **analyze**
  - If the scenario has only been created or ran but not extracted the state will be then set to **execute**

Note that instantiating a `Scenario` object with a string that doesn't match any existing scenarios identification number or name will result in a printout of the list of existing scenarios and their information.


### A. Retrieving Scenario Output Data
When the `Scenario` object is in the **analyze** state, the user can access various scenario information and data. The following code snippet lists the methods implemented to do so.
```python
from powersimdata.scenario.scenario import Scenario

scenario = Scenario(600)
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
If generators or AC/DC lines have been scaled or added to the grid, and/or if the demand in one or multiple load zones has been scaled for this scenario then the change table will enclose these changes and the retrieved grid and profiles will be modified accordingly. Note that the analysis of the scenario using the output data is done in the [PostREISE] package.


### B. Creating a Scenario
A scenario can be created using few lines of code. This is illustrated below:
```python
from powersimdata.scenario.scenario import Scenario

scenario = Scenario('')
# print name of Scenario object state
print(scenario.state.name)

# Start building a scenario
scenario.state.set_builder(grid_model="usa_tamu", interconnect="Western")

# set plan and scenario names
scenario.state.builder.set_name("test", "dummy")
# set start date, end date and interval
scenario.state.builder.set_time("2016-08-01 00:00:00",
                                "2016-08-31 23:00:00",
                                "24H")
# set demand profile version
scenario.state.builder.set_base_profile("demand", "vJan2021")
# set hydro profile version
scenario.state.builder.set_base_profile("hydro", "vJan2021")
# set solar profile version
scenario.state.builder.set_base_profile("solar", "vJan2021")
# set wind profile version
scenario.state.builder.set_base_profile("wind", "vJan2021")

# scale capacity of solar plants in WA and AZ by 5 and 2.5, respectively
scenario.state.builder.change_table.scale_plant_capacity(
    "solar", zone_name={"Washington": 5, "Arizona": 2.5})
# scale capacity of wind farms in OR and MT by 1.5 and 2, respectively
scenario.state.builder.change_table.scale_plant_capacity(
    "wind", zone_name={"Oregon": 1.5, "Montana Western": 2})
# scale capacity of branches in NV and WY by 2
scenario.state.builder.change_table.scale_branch_capacity(
    zone_name={"Nevada": 2, "Wyoming": 2})

# add AC lines in NM and CO
scenario.state.builder.change_table.add_branch(
    [{"capacity": 200, "from_bus_id": 2053002, "to_bus_id": 2053303},
     {"capacity": 150, "from_bus_id": 2060002, "to_bus_id": 2060046}])

# add DC line between CO and CA (Bay Area)
scenario.state.builder.change_table.add_dcline(
    [{"capacity": 2000, "from_bus_id": 2060771, "to_bus_id": 2021598}])

# add a solar plant in NV, a coal plant in ID and a natural gas plant in OR
scenario.state.builder.change_table.add_plant(
    [{"type": "solar", "bus_id": 2030454, "Pmax": 75},
     {"type": "coal", "bus_id": 2074334, "Pmin": 25, "Pmax": 750, "c0": 1800, "c1": 30, "c2": 0.0025},
     {"type": "ng", "bus_id": 2090018, "Pmax": 75, "c0": 900, "c1": 30, "c2": 0.0015}])

# add a new bus, and a new one-way DC line connected to this bus
scenario.state.builder.change_table.add_bus(
	[{"lat": 48, "lon": -125, "zone_id": 201, "baseKV": 138}])
scenario.state.builder.change_table.add_dcline(
	[{"from_bus_id": 2090023, "to_bus_id": 2090024, "Pmin": 0, "Pmax": 200}])

# get grid used in scenario
grid = scenario.state.get_grid()
# get change table used to alter the base grid.
ct = scenario.state.get_ct()
```
It can be convenient to clear the change table when creating a scenario. Let's say for instance that a wrong scaling factor has been applied or a generator has been attached to the wrong bus. To do so, the `clear` method of the `ChangeTable` class can be used.

There are also a couple of more advanced methods which can selectively scale branches based on the topology of the existing grid, or based on power flow results from a previous scenario. These can be called as:
```python
scenario.state.builder.change_table.scale_renewable_stubs()
```
or
```python
scenario.state.builder.change_table.scale_congested_mesh_branches(ref_scenario)
```
where `ref_scenario` is a `Scenario` object in **analyze** state.

The final step is to run the `create_scenario` method:
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
Once the scenario is successfully created, a scenario id is printed on screen and the state of the `Scenario` object is switched to **execute**. printed on screen.


### C. Running the Scenario and Extracting Output Data
It is possible to execute the scenario immediately right after it has been created. One can also create a new `Scenario` object. This is the option we follow here.

The **execute** state accomplishes the three following tasks:
* It prepares the simulation inputs: the scaled profiles and the MAT-file enclosing all the information related to the electrical grid
* It launches the simulation
* It extracts the output data - This operation is performed once the simulation has finished running.

```python
from powersimdata.scenario.scenario import Scenario

scenario = Scenario("dummy")
# print scenario information
scenario.print_scenario_info()

# prepare simulation inputs
scenario.state.prepare_simulation_input()

# launch simulation
process_run = scenario.state.launch_simulation()

# Get simulation status
scenario.state.print_scenario_status()
```
Note that the status of the simulation can be accessed using the `print_scenario_status` method.

As an optional parameter, the number of threads used to run the simulation can be specified using for example:
```python
process_run = scenario.state.launch_simulation(threads=8)
```
Extracting data from the simulation engine outputs can be a memory intensive process. If there are resource constraints where the engine resides, it is possible to pause the data from being extracted using an optional parameter and then manually extracting the data at a suitable time:
```python
process_run = scenario.state.launch_simulation(extract_data=False)
# Extract data
process_extract = scenario.state.extract_simulation_output()
```


### D. Deleting a Scenario
A scenario can be deleted. All the input and output files as well as any entries in monitoring files will be removed. The **delete** state is only accessible from the **analyze** state.
```python
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
scenario.state.delete_scenario()
```


### E. Moving a Scenario to Backup disk
A scenario can be move to a backup disk. The **move** state is only accessible from the **analyze** state. The functionality is illustrated below:
```python
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
scenario.state.move_scenario()
```


## 3. U.S. Electric Grid and Interconnection
A `Grid` object encapsulates all the information related to the synthetic network used in this project for a single interconnection (**Eastern**, **Texas** or **Western**), a combination of two interconnections (**Eastern** and **Texas** for example) or the full U.S. electric grid (**USA**). Only one argument is required to instantiate the `Grid` class, a `list` of interconnections (as `str`) in any order and a `str` for single interconnection or **USA**.
```python
from powersimdata.input.grid import Grid
western_texas = Grid(["Western", "Texas"])
```
The object has various attributes. These are listed below and a short description is given:
* **zone2id (id2zone)**: `dict` -- load zone name (load zone id) to load zone id (load zone name).
* **interconnect**: `str` --  interconnection name.
* **bus**: `pandas.DataFrame` -- bus id as index and bus characteristics as columns.
* **sub**: `pandas.DataFrame` -- substation id as index and substation information as columns.
* **bus2sub**: `pandas.DataFrame` -- bus id as index and substation id as column.
* **plant**: `pandas.DataFrame` -- plant id as index and plant characteristics as columns.
* **branch**: `pandas.DataFrame` -- branch id as index and branch characteristics as columns.
* **gencost**: `dict` -- has two keys: `before` and `after`. Values are `pandas.DataFrame` with plant id as index and generator cost curve information as columns. The `before` key points to the original set of cost curves (polynomials) whereas the `after` key gives the ones that has been used in the simulation (linearized or piece-wise linearized version).
* **dcline**: `pandas.DataFrame` -- DC line id as index and DC line characteristics as columns.
```python
from powersimdata.input.grid import Grid
usa = Grid("USA")
usa.plant.head()
# get all wind farm in the U.S. electrical grid
wind_farm = usa.plant.groupby("type").get_group("wind")
# get DC lines in the grid
dcline = usa.dcline
```
The synthetic U.S. network used in our simulation framework can be found at the following url: <https://electricgrids.engr.tamu.edu>. Our team has altered the original network in many ways to make it more realistic. These have been achieved by comparing our simulation results with historical generation level. Our data along with their description can be found on [zenodo].


## 4. Capacity Planning Framework
The capacity planning framework is intended to estimate the amount of new capacity that will be required to meet future clean energy goals.


### A. Required Inputs
At minimum, this framework requires a *reference* `Scenario` object--used to specify the current capacities and capacity factors of resources which *count* towards state-level clean energy goals (this `Scenario` object must be in **analyze** state)--and a list of target areas (comprised of one or more zones) and their target clean energy penetrations. A strategy must also be specified, either `independent` (each area meets it own goal) or `collaborative` (all areas with non-zero goals work together to meet a shared goal, resembling REC trading).

The list of targets may be specified in either a CSV file or a data frame, as long as the required columns are present: `region_name` and `ce_target_fraction`. Optional columns are: `allowed_resources` (defaulting to solar & wind), `external_ce_addl_historical_amount` (clean energy not modeled in our grid, defaulting to 0), and `solar_percentage` (how much of the new capacity will be solar, defaulting to the current solar:wind ratio. This input only applies to the *independent* strategy, a shared-goal new solar fraction for *collaborative* planning is specified in the function call to `calculate_clean_capacity_scaling`.


### B. Optional Inputs
Since increasing penetration of renewable capacity is often associated with increased curtailment, an expectation of this new curtailment can be passed as the `addl_curtailment` parameter. For the *collaborative* method, this must be passed as a dictionary of `{resource_name: value}` pairs, for the *independent* method this must be passed as a data frame or as a two-layer nested dictionary which can be interpreted as a data frame. For either method, additional curtailment must be a value between 0 and 1, representing a percentage, not percentage points. For example, if the previous capacity factor was 30%, and additional curtailment of 10% is specified, the expected new capacity factor will be 27%, not 20%.

Another `Scenario` object can be passed as `next_scenario` to specify the magnitude of future demand (relevant for energy goals which are expressed as a fraction of total consumption); this `Scenario` object may be any state, as long as `Scenario.state.get_demand()` can be called successfully, i.e. if the `Scenario` object is in **create** state, an interconnection must be defined. This allows calculation of new capacity for a scenario which is being designed, using the demand scaling present in the change table.

Finally, for the *collaborative* method, a `solar_fraction` may be defined, which determines scenario-wide how much of the new capacity should be solar (the remainder will be wind).


### C. Example Capacity Planning Function Calls
Basic independent call, using the demand from the reference scenario to approximate the future demand:
```python
from powersimdata.design.generation.clean_capacity_scaling import calculate_clean_capacity_scaling
from powersimdata.scenario.scenario import Scenario

ref_scenario = Scenario(403)
targets_and_new_capacities_df = calculate_clean_capacity_scaling(
    ref_scenario,
    method="independent",
    targets_filename="eastern_2030_clean_energy_targets.csv"
)
```

Complex collaborative call, using all optional parameters:
```python
from powersimdata.design.generation.clean_capacity_scaling import calculate_clean_capacity_scaling
from powersimdata.scenario.scenario import Scenario

ref_scenario = Scenario(403)
# Start building a new scenario, to plan capacity for greater demand
new_scenario = Scenario("")
new_scenario.state.set_builder(["Eastern"])
zone_demand_scaling = {"Massachusetts": 1.1, "New York City": 1.2}
new_scenario.state.builder.change_table.scale_demand(zone_name=zone_demand_scaling)
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
```


### D. Creating a Change Table from Capacity Planning Results
The capacity planning framework returns a data frame of capacities by resource type and target area, but the Scenario creation process ultimately requires scaling factors by resource type and zone or plant_id. A function `create_change_table` exists to perform this conversion process. Using a reference scenario, a set of scaling factors by resource type, zone, and plant_id is calculated. When applied to a base `Grid` object, these scaling factors will result in capacities that are nearly identical to the reference scenario on a per-plant basis (subject to rounding), with the exception of solar and wind generators, which will be scaled up to meet clean energy goals.
```python
from powersimdata.design.generation.clean_capacity_scaling import create_change_table

change_table = create_change_table(targets_and_new_capacities_df, ref_scenario)
# The change table method only accepts zone names, not zone IDs, so we have to translate
id2zone = new_scenario.state.get_grid().id2zone
# Plants can only be scaled one resource at a time, so we need to loop through
for resource in change_table:
	new_scenario.state.builder.change_table.scale_plant_capacity(
		resource=resource,
		zone_name={
			id2zone[id]: value
			for id, value in change_table[resource]["zone_name"].items()
		},
		plant_id=change_table[resource]["zone_name"]
	)
```


## 5. Analyzing Scenario Designs
### A. Analysis of Transmission Upgrades
#### I. Cumulative Upgrade Quantity
Using the change table of a scenario, the number of upgrades lines/transformers and their cumulative upgraded capacity (for transformers) and cumulative upgraded megawatt-miles (for lines) can be calculated with:
```python
powersimdata.design.transmission.mwmiles.calculate_mw_miles(scenario)
```
where `scenario` is a `Scenario` instance.


#### II. Classify Upgrades
The upgraded branches can also be classified into either interstate or intrastate branches by calling:
```python
powersimdata.design.transmission.statelines.classify_interstate_intrastate(scenario)
```
where `scenario` is a `Scenario` instance.


### B. Analysis of Generation Upgrades
#### I. Accessing and Saving Relevant Supply Information
Analyzing generator supply and cost curves requires the proper generator cost and plant information to be accessed from a Grid object. This data can be accessed using the following:
```python
from powersimdata.design.generation.cost_curves import get_supply_data

supply_df = get_supply_data(grid, num_segments, save)
```
where `grid` is a `Grid` object, `num_segments` is the number of linearized cost curve segments into which the provided quadratic cost curve should be split, and `save` is a string representing the desired file path and file name to which the resulting data will be saved. `save` defaults to `None`. `get_supply_data` returns a DataFrame that contains information about each generator's fuel type, quadratic cost curve, and linearized cost curve, as well as the interconnect and load zone to which the generator belongs. `get_supply_data` is used within many of the following supply and cost curve visualization and analysis functions.


#### II. Visualizing Generator Supply Curves
To obtain the supply curve for a particular fuel type and area, the following is used:
```python
from powersimdata.design.generation.cost_curves import build_supply_curve

P, F = build_supply_curve(grid, num_segments, area, gen_type, area_type, plot)
```
where `grid` is a `Grid` object; `num_segments` is the number of linearized cost curve segments to create; `area` is a string describing an appropriate load zone, interconnect, or state; `gen_type` is a string describing an appropriate fuel type; `area_type` is a string describing the type of region that is being considered; and `plot` is a boolean that indicates whether or not the plot is shown. `area_type` defaults to `None`, which allows the area type to be inferred; there are instances where specifying the area type can be useful (e.g., Texas can refer to both a state and an interconnect, though they are not the same thing). `plot` defaults to `True`. `build_supply_curve` returns `P` and `F`, the supply curve capacity and price quantities, respectively.


#### III. Comparing Supply Curves
When updating generator cost curve information, it can be useful to see the corresponding effect on the supply curve for a particular area and fuel type pair. Instead of only performing a visual inspection between the original and new supply curves, the maximum price difference between the two supply curves can be calculated. This metric, which is similar to the Kolmogorov-Smirnov test, serves as a goodness-of-fit test between the two supply curves, where a lower score is desired. This metric can be calculated as follows:
```python
from powersimdata.design.generation.cost_curves import ks_test

max_diff = ks_test(P1, F1, P2, F2, area, gen_type, plot)
```
where `P1` and `P2` are lists containing supply curve capacity data; `F1` and `F2` are lists containing corresponding supply curve price data; `area` is a string describing an appropriate load zone, interconnect, or state; `gen_type` is a string describing an appropriate fuel type; and `plot` is a boolean that indicates whether or not the plot is shown. The pairs of supply curve data, (`P1`, `F1`) and (`P2`, `F2`), can be created using `build_supply_curve` or can be created manually.  It should be noted that the two supply curves must offer the same amount of capacity (i.e., `max(P1) = max(P2)`). `area` and `gen_type` both default to `None`. `plot` defaults to `True`. `ks_test` returns `max_diff`, which is the maximum price difference between the two supply curves.


#### IV. Comparing Cost Curve Parameters
When designing generator cost curves, it can be instructive to visually compare the quadratic cost curve parameters for generators in a particular area and fuel type pair. The linear terms (`c1`) and quadratic terms (`c2`) for a given area and fuel type can be compared in a plot using the following:
```python
from powersimdata.design.generation.cost_curves import plot_linear_vs_quadratic_terms

plot_linear_vs_quadratic_terms(grid, area, gen_type, area_type, plot, zoom, num_sd, alpha)
```
where `grid` is a `Grid` object; `area` is a string describing an appropriate load zone, interconnect, or state; `gen_type` is a string describing an appropriate fuel type; `area_type` is a string describing the type of region that is being considered; `plot` is a boolean that indicates whether or not the plot is shown; `zoom` is a boolean that indicates whether or not the zoom capability that filters out quadratic term outliers for better visualization is enabled; `num_sd` is the number of standard deviations outside of which quadratic terms are filtered; and `alpha` is the alpha blending parameter for the scatter plot. `area_type` defaults to `None`, which allows the area type to be inferred. `plot` defaults to `True`. `zoom` defaults to `False`. `num_sd` defaults to `3`. `alpha`, which can take values between `0` and `1`, defaults to `0.1`. 


#### V. Comparing Generators by Capacity and Price
When designing generator cost curves, it can be useful to visually compare the capacity and price parameters for each generator in a specified area and fuel type pair. The generator capacity and price parameters for a given area and fuel type can be compared in a plot using the following:
```python
from powersimdata.design.generation.cost_curves import plot_capacity_vs_price

plot_capacity_vs_price(grid, num_segments, area, gen_type, area_type, plot)
```
where `grid` is a `Grid` object; `num_segments` is the number of linearized cost curve segments to create; `area` is a string describing an appropriate load zone, interconnect, or state; `gen_type` is a string describing an appropriate fuel type; `area_type` is a string describing the type of region that is being considered; and `plot` is a boolean that indicates whether or not the plot is shown. `area_type` defaults to `None`, which allows the area type to be inferred. `plot` defaults to `True`.


[PreREISE]: https://github.com/Breakthrough-Energy/PreREISE
[PostREISE]: https://github.com/Breakthrough-Energy/PostREISE
[zenodo]: https://zenodo.org/record/3530898
