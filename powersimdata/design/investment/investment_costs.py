import warnings

import numpy as np
import pandas as pd

from powersimdata.design.compare.generation import calculate_plant_difference
from powersimdata.design.compare.transmission import (
    calculate_branch_difference,
    calculate_dcline_difference,
)
from powersimdata.design.investment import const
from powersimdata.design.investment.create_mapping_files import (
    bus_to_neem_reg,
    bus_to_reeds_reg,
)
from powersimdata.design.investment.inflation import calculate_inflation
from powersimdata.input.check import _check_grid_models_match
from powersimdata.utility.distance import haversine


def merge_keep_index(df1, df2, **kwargs):
    """Execute a pandas DataFrame merge, preserving the index of the first dataframe.

    :param pandas.DataFrame df1: first data frame, to call pandas merge from.
    :param pandas.DataFrame df2: second data frame, argument to pandas merge.
    :param \\*\\*kwargs: arbitrary keyword arguments passed to pandas merge call.
    :return: (*pandas.DataFrame*) -- df1 merged with df2 with indices preserved.
    """
    return df1.reset_index().merge(df2, **kwargs).set_index(df1.index.names)


def append_keep_index_name(df1, other, *args, **kwargs):
    """Execute a pandas DataFrame append, preserving the index name of the dataframe.

    :param pandas.DataFrame df1: first data frame, to call pandas append from.
    :param pandas.DataFrame/pandas.Series/list: first argument to pandas append method.
    :param \\*args: arbitrary positional arguments passed to pandas append call.
    :param \\*\\*kwargs: arbitrary keyword arguments passed to pandas append call.
    :return: (*pandas.DataFrame*) -- df1 appended with other with index name preserved.
    """
    original_index_name = df1.index.name
    new_df = df1.append(other, *args, **kwargs)
    new_df.index.name = original_index_name
    return new_df


def calculate_ac_inv_costs(
    scenario,
    sum_results=True,
    exclude_branches=None,
    base_grid=None,
):
    """Calculate cost of upgrading AC lines and/or transformers in a scenario.
    NEEM regions are used to find regional multipliers.

    :param powersimdata.scenario.scenario.Scenario scenario: scenario instance.
    :param bool sum_results: whether to sum data frame for each branch type. Defaults to
        True.
    :param powersimdata.input.grid.Grid base_grid: a Grid to compare against. If None,
        the grid model and interconnect from the ``scenario`` are used to instantiate a
        corresponding unmodified Grid.
    :return: (*dict*) -- keys are {'line_cost', 'transformer_cost'}, values are either
        float if ``sum_results``, or pandas Series indexed by branch ID.
        Whether summed or not, values are $USD, inflation-adjusted to today.
    """
    grid_differences = scenario.get_grid()
    if base_grid is None:
        base_grid = scenario.get_base_grid()
    else:
        _check_grid_models_match(base_grid, grid_differences)

    # find upgraded AC lines
    capacity_difference = calculate_branch_difference(
        base_grid.branch, grid_differences.branch
    )
    grid_differences.branch = grid_differences.branch.assign(
        rateA=capacity_difference["diff"].to_numpy()
    )
    grid_differences.branch = grid_differences.branch.query("rateA != 0.0")
    if exclude_branches is not None:
        present_exclude_branches = set(exclude_branches) & set(
            grid_differences.branch.index
        )
        grid_differences.branch.drop(index=present_exclude_branches, inplace=True)

    costs = _calculate_ac_inv_costs(grid_differences, sum_results)
    return costs


def _calculate_ac_inv_costs(grid_new, sum_results=True):
    """Calculate cost of upgrading AC lines and/or transformers. NEEM regions are
    used to find regional multipliers. Note that a transformer winding is considered
    as a transformer.

    :param powersimdata.input.grid.Grid grid_new: grid instance.
    :param bool sum_results: whether to sum data frame for each branch type. Defaults to
        True.
    :return: (*dict*) -- keys are {'line_cost', 'transformer_cost'}, values are either
        float if ``sum_results``, or pandas Series indexed by branch ID.
        Whether summed or not, values are $USD, inflation-adjusted to today.
    """

    def select_mw(x, cost_df):
        """Determine the closest kV/MW combination for a single branch and return
        the corresponding cost (in $/MW-mi).

        :param pandas.Series x: data for a single branch
        :param pandas.DataFrame cost_df: data frame with *'kV'*, *'MW'*, *'costMWmi'*
            as columns
        :return: (*pandas.Series*) -- series of [*'MW'*, *'costMWmi'*] to be assigned
            to branch.
        """
        underground_regions = ("NEISO", "NYISO J-K")
        filtered_cost_df = cost_df.copy()
        # Unless we are entirely within an underground region, drop this cost class
        if not (x.from_region == x.to_region and x.from_region in underground_regions):
            filtered_cost_df = filtered_cost_df.query("kV != 345 or MW != 500")
        # select corresponding cost table of selected kV
        filtered_cost_df = filtered_cost_df[filtered_cost_df["kV"] == x.kV]
        # get rid of NaN values in this kV table
        filtered_cost_df = filtered_cost_df[~filtered_cost_df["MW"].isna()]
        # find closest MW & corresponding cost
        filtered_cost_df = filtered_cost_df.iloc[
            np.argmin(np.abs(filtered_cost_df["MW"] - x.rateA))
        ]
        return filtered_cost_df.loc[["MW", "costMWmi"]]

    def get_branch_mult(x, bus_reg, ac_reg_mult, branch_lookup_alerted=set()):
        """Determine the regional multiplier based on kV and power (closest).

        :param pandas.Series x: data for a single branch.
        :param pandas.DataFrame bus_reg: data frame with bus regions.
        :param pandas.DataFrame ac_reg_mult: data frame with regional multipliers.
        :param set branch_lookup_alerted: set of (voltage, region) tuples for which
            a message has already been printed that this lookup was not found.
        :return: (*float*) -- regional multiplier.
        """
        # Select the highest voltage for transformers (branch end voltages should match)
        max_kV = bus.loc[[x.from_bus_id, x.to_bus_id], "baseKV"].max()  # noqa: N806
        # Average the multipliers for branches (transformer regions should match)
        regions = (x.from_region, x.to_region)
        region_mults = ac_reg_mult.loc[ac_reg_mult.name_abbr.isin(regions)]
        region_mults = region_mults.groupby(["kV", "MW"]).mean().reset_index()

        mult_lookup_kV = region_mults.loc[  # noqa: N806
            (region_mults.kV - max_kV).abs().idxmin()
        ].kV
        region_kV_mults = region_mults[region_mults.kV == mult_lookup_kV]  # noqa: N806
        region_kV_mults = region_kV_mults.loc[  # noqa: N806
            ~region_kV_mults.mult.isnull()
        ]
        if len(region_kV_mults) == 0:
            mult = 1
            if (mult_lookup_kV, regions) not in branch_lookup_alerted:
                print(f"No multiplier for voltage {mult_lookup_kV} in {regions}")
                branch_lookup_alerted.add((mult_lookup_kV, regions))
        else:
            mult_lookup_MW = region_kV_mults.loc[  # noqa: N806
                (region_kV_mults.MW - x.rateA).abs().idxmin(), "MW"
            ]
            mult = (
                region_kV_mults.loc[region_kV_mults.MW == mult_lookup_MW].squeeze().mult
            )
        return mult

    # import data
    ac_cost = pd.DataFrame(const.ac_line_cost)
    ac_reg_mult = pd.read_csv(const.ac_reg_mult_path)
    ac_reg_mult = ac_reg_mult.melt(
        id_vars=["kV", "MW"], var_name="name_abbr", value_name="mult"
    )
    try:
        bus_reg = pd.read_csv(const.bus_neem_regions_path, index_col="bus_id")
    except FileNotFoundError:
        bus_reg = bus_to_neem_reg(grid_new.bus)
        bus_reg.sort_index().to_csv(const.bus_neem_regions_path)
    xfmr_cost = pd.read_csv(const.transformer_cost_path, index_col=0).fillna(0)
    xfmr_cost.columns = [int(c) for c in xfmr_cost.columns]
    # Mirror across diagonal
    xfmr_cost += xfmr_cost.to_numpy().T - np.diag(np.diag(xfmr_cost.to_numpy()))

    # check that all buses included in this file and lat/long values match,
    # otherwise re-run mapping script on mis-matching buses. These buses are missing
    # in region file
    bus = grid_new.bus
    mapped_buses = bus.query("index in @bus_reg.index")
    missing_bus_indices = set(bus.index) - set(bus_reg.index)
    mapped_buses = merge_keep_index(mapped_buses, bus_reg, how="left", on="bus_id")
    # these buses have incorrect lat/lon values in the region mapping file.
    #   re-running the region mapping script on those buses only.
    misaligned_bus_indices = mapped_buses[
        ~np.isclose(mapped_buses.lat_x, mapped_buses.lat_y)
        | ~np.isclose(mapped_buses.lon_x, mapped_buses.lon_y)
    ].index
    all_buses_to_fix = set(missing_bus_indices) | set(misaligned_bus_indices)
    # fix the identified buses, if necessary
    if len(all_buses_to_fix) > 0:
        bus_fix = bus_to_neem_reg(bus.query("index in @all_buses_to_fix"))
        fix_cols = ["name_abbr", "lat", "lon"]
        corrected_bus_mappings = bus_fix.loc[misaligned_bus_indices, fix_cols]
        new_bus_mappings = bus_fix.loc[missing_bus_indices, fix_cols]
        bus_reg.loc[misaligned_bus_indices, fix_cols] = corrected_bus_mappings
        bus_reg = append_keep_index_name(bus_reg, new_bus_mappings)

    bus_reg.drop(["lat", "lon"], axis=1, inplace=True)

    # Add extra information to branch data frame
    branch = grid_new.branch
    branch.loc[:, "kV"] = bus.loc[branch.from_bus_id, "baseKV"].tolist()
    branch.loc[:, "from_region"] = bus_reg.loc[branch.from_bus_id, "name_abbr"].tolist()
    branch.loc[:, "to_region"] = bus_reg.loc[branch.to_bus_id, "name_abbr"].tolist()
    # separate transformers and lines
    t_mask = branch["branch_device_type"].isin(["Transformer", "TransformerWinding"])
    transformers = branch[t_mask].copy()
    lines = branch[~t_mask].copy()
    if len(lines) > 0:
        # Find closest kV rating
        lines.loc[:, "kV"] = lines.apply(
            lambda x: ac_cost.loc[(ac_cost["kV"] - x.kV).abs().idxmin(), "kV"],
            axis=1,
        )
        lines[["MW", "costMWmi"]] = lines.apply(lambda x: select_mw(x, ac_cost), axis=1)

        lines["mult"] = lines.apply(
            lambda x: get_branch_mult(x, bus_reg, ac_reg_mult), axis=1
        )

        # calculate MWmi
        lines.loc[:, "lengthMi"] = lines.apply(
            lambda x: haversine((x.from_lat, x.from_lon), (x.to_lat, x.to_lon)), axis=1
        )
    else:
        new_columns = ["kV", "MW", "costMWmi", "mult", "lengthMi"]
        lines = lines.reindex(columns=[*lines.columns.tolist(), *new_columns])
    lines.loc[:, "MWmi"] = lines["lengthMi"] * lines["rateA"]

    # calculate cost of each line
    lines.loc[:, "cost"] = lines["MWmi"] * lines["costMWmi"] * lines["mult"]

    # calculate transformer costs
    if len(transformers) > 0:
        transformers["per_MW_cost"] = transformers.apply(
            lambda x: xfmr_cost.iloc[
                xfmr_cost.index.get_loc(
                    bus.loc[x.from_bus_id, "baseKV"], method="nearest"
                ),
                xfmr_cost.columns.get_loc(
                    bus.loc[x.to_bus_id, "baseKV"], method="nearest"
                ),
            ],
            axis=1,
        )
        transformers["mult"] = transformers.apply(
            lambda x: get_branch_mult(x, bus_reg, ac_reg_mult), axis=1
        )
    else:
        # Properly handle case with no transformers, where apply returns wrong dims
        transformers["per_MW_cost"] = []
        transformers["mult"] = []

    transformers["cost"] = (
        transformers["rateA"] * transformers["per_MW_cost"] * transformers["mult"]
    )

    lines.cost *= calculate_inflation(2010)
    transformers.cost *= calculate_inflation(2020)
    if sum_results:
        return {
            "line_cost": lines.cost.sum(),
            "transformer_cost": transformers.cost.sum(),
        }
    else:
        return {"line_cost": lines.cost, "transformer_cost": transformers.cost}


def calculate_dc_inv_costs(scenario, sum_results=True, base_grid=None):
    """Calculate cost of upgrading HVDC lines in a scenario.

    :param powersimdata.scenario.scenario.Scenario scenario: scenario instance.
    :param bool sum_results: whether to sum series to return total cost. Defaults to
        True.
    :param powersimdata.input.grid.Grid base_grid: a Grid to compare against. If None,
        the grid model and interconnect from the ``scenario`` are used to instantiate a
        corresponding unmodified Grid.
    :return: (*pandas.Series/float*) -- cost of upgrading HVDC lines, in $USD,
        inflation-adjusted to today. If ``sum_results``, a float is returned, otherwise
        a Series.
    """
    grid_differences = scenario.get_grid()
    if base_grid is None:
        base_grid = scenario.get_base_grid()
    else:
        _check_grid_models_match(base_grid, grid_differences)

    # find upgraded DC lines
    capacity_difference = calculate_dcline_difference(
        base_grid.dcline, grid_differences.dcline
    )
    grid_differences.dcline = grid_differences.dcline.assign(
        Pmax=capacity_difference["diff"].to_numpy()
    )
    grid_differences.dcline = grid_differences.dcline.query("Pmax != 0.0")

    costs = _calculate_dc_inv_costs(grid_differences, sum_results)
    return costs


def _calculate_dc_inv_costs(grid_new, sum_results=True):
    """Calculate cost of upgrading HVDC lines.

    :param powersimdata.input.grid.Grid grid_new: grid instance.
    :param bool sum_results: whether to sum series to return total cost. Defaults to
        True.
    :return: (*pandas.Series/float*) -- cost of upgrading HVDC lines, in $USD,
        inflation-adjusted to today. If ``sum_results``, a float is returned, otherwise
        a Series.
    """

    def _calculate_single_line_cost(line, bus):
        """Calculate cost of upgrading a single HVDC line.

        :param pandas.Series line: HVDC line series featuring *'from_bus_id'*',
            *'to_bus_id'* and *'Pmax'*.
        :param pandas.Dataframe bus: bus data frame featuring *'lat'*, *'lon'*.
        :return: (*float*) -- HVDC line upgrade cost in $2015.
        """
        # Calculate distance
        from_lat = bus.loc[line.from_bus_id, "lat"]
        from_lon = bus.loc[line.from_bus_id, "lon"]
        to_lat = bus.loc[line.to_bus_id, "lat"]
        to_lon = bus.loc[line.to_bus_id, "lon"]
        miles = haversine((from_lat, from_lon), (to_lat, to_lon))
        # Calculate cost
        total_cost = line.Pmax * (
            miles * const.hvdc_line_cost["costMWmi"] * calculate_inflation(2015)
            + 2 * const.hvdc_terminal_cost_per_MW * calculate_inflation(2020)
        )
        return total_cost

    bus = grid_new.bus
    dcline = grid_new.dcline

    # if any dclines, do calculations, otherwise, return 0 costs.
    if len(dcline != 0):
        dcline_costs = dcline.apply(_calculate_single_line_cost, args=(bus,), axis=1)
        if sum_results:
            return dcline_costs.sum()
        else:
            return dcline_costs
    else:
        return 0.0


def calculate_gen_inv_costs(
    scenario,
    year,
    cost_case,
    sum_results=True,
    base_grid=None,
):
    """Calculate cost of upgrading generators in a scenario. ReEDS regions are used to
    find regional multipliers.

    :param powersimdata.scenario.scenario.Scenario scenario: scenario instance.
    :param int/str year: building year.
    :param str cost_case: ATB cost case of data. *'Moderate'*: mid cost case,
        *'Conservative'*: generally higher costs, *'Advanced'*: generally lower costs
    :param bool sum_results: whether to sum data frame for plant costs. Defaults to
        True.
    :param powersimdata.input.grid.Grid base_grid: a Grid to compare against. If None,
        the grid model and interconnect from the ``scenario`` are used to instantiate a
        corresponding unmodified Grid.
    :return: (*pandas.Series*) -- Overnight generation investment cost.
        If ``sum_results``, indices are technologies and values are total cost.
        Otherwise, indices are IDs of plants (including storage, which is given
        pseudo-plant-IDs), and values are individual generator costs.
        Whether summed or not, values are $USD, inflation-adjusted to today.

    .. todo:: it currently uses one (arbitrary) sub-technology. The rest of the costs
        are dropped. Wind and solar will need to be fixed based on the resource supply
        curves.
    """
    grid_differences = scenario.get_grid()
    if base_grid is None:
        base_grid = scenario.get_base_grid()
    else:
        _check_grid_models_match(base_grid, grid_differences)

    # Find change in generation capacity
    capacity_difference = calculate_plant_difference(
        base_grid.plant, grid_differences.plant
    )
    grid_differences.plant = grid_differences.plant.assign(
        Pmax=capacity_difference["diff"].to_numpy()
    )
    grid_differences.plant = grid_differences.plant.query("Pmax >= 0.01")
    # Find change in storage capacity
    # Reindex so that we don't get NaN when calculating upgrades for new storage
    base_grid.storage["gen"] = base_grid.storage["gen"].reindex(
        grid_differences.storage["gen"].index, fill_value=0
    )
    grid_differences.storage["gen"].Pmax = (
        grid_differences.storage["gen"].Pmax - base_grid.storage["gen"].Pmax
    )
    grid_differences.storage["gen"]["type"] = "storage"

    costs = _calculate_gen_inv_costs(grid_differences, year, cost_case, sum_results)
    return costs


def _calculate_gen_inv_costs(grid_new, year, cost_case, sum_results=True):
    """Calculate cost of upgrading generators. ReEDS regions are used to find
    regional multipliers.

    :param powersimdata.input.grid.Grid grid_new: grid instance.
    :param int/str year: year of builds.
    :param str cost_case: ATB cost case of data. *'Moderate'*: mid cost case
        *'Conservative'*: generally higher costs, *'Advanced'*: generally lower costs.
    :raises ValueError: if year not 2020 - 2050, or cost case not an allowed option.
    :raises TypeError: if year not int/str or cost_case not str.
    :param bool sum_results: whether to sum data frame for plant costs. Defaults to
        True.
    :return: (*pandas.Series*) -- Overnight generation investment cost.
        If ``sum_results``, indices are technologies and values are total cost.
        Otherwise, indices are IDs of plants (including storage, which is given
        pseudo-plant-IDs), and values are individual generator costs.
        Whether summed or not, values are $USD, inflation-adjusted to today.

    .. note:: the function computes the total capital cost as:
        CAPEX_total = overnight CAPEX ($/MW) * Power capacity (MW) * regional multiplier
    """

    def load_cost(year, cost_case):
        """Load in base costs from NREL's 2020 ATB for generation technologies (CAPEX).

        :param int/str year: year of cost projections.
        :param str cost_case: ATB cost case of data (see
        :return: (*pandas.DataFrame*) -- cost by technology/subtype in $2018.

        .. todo:: it can be adapted in the future for FOM, VOM, & CAPEX. This data is
            pulled from the ATB xlsx file summary pages. Therefore, it currently uses
            default financials, but will want to create custom financial functions in
            the future.
        """
        cost = pd.read_csv(const.gen_inv_cost_path)
        cost = cost.dropna(axis=0, how="all")

        # drop non-useful columns
        cols_drop = cost.columns[
            ~cost.columns.isin(
                [str(x) for x in cost.columns[0:6]] + ["Metric", str(year)]
            )
        ]
        cost.drop(cols_drop, axis=1, inplace=True)

        # rename year of interest column
        cost.rename(columns={str(year): "value"}, inplace=True)

        # get rid of #refs
        cost.drop(cost[cost["value"] == "#REF!"].index, inplace=True)

        # get rid of $s, commas
        cost["value"] = cost["value"].str.replace("$", "", regex=True)
        cost["value"] = cost["value"].str.replace(",", "", regex=True).astype("float64")
        # scale from $/kW to $/MW
        cost["value"] *= 1000

        cost.rename(columns={"value": "CAPEX"}, inplace=True)

        # select scenario of interest
        if cost_case != "Moderate":
            # The 2020 ATB only has "Moderate" for nuclear, so we need to make due.
            warnings.warn(
                f"No cost data available for Nuclear for {cost_case} cost case, "
                "using Moderate cost case data instead"
            )
            new_nuclear = cost.query(
                "Technology == 'Nuclear' and CostCase == 'Moderate'"
            ).copy()
            new_nuclear.CostCase = cost_case
            cost = cost.append(new_nuclear, ignore_index=True)
        cost = cost[cost["CostCase"] == cost_case]
        cost.drop(["CostCase"], axis=1, inplace=True)

        return cost

    if isinstance(year, (int, str)):
        year = int(year)
        if year not in range(2020, 2051):
            raise ValueError("year not in range.")
    else:
        raise TypeError("year must be int or str.")

    if isinstance(cost_case, str):
        if cost_case not in ["Moderate", "Conservative", "Advanced"]:
            raise ValueError("cost_case not Moderate, Conservative, or Advanced")
    else:
        raise TypeError("cost_case must be str.")

    storage_plants = grid_new.storage["gen"].set_index(
        grid_new.storage["StorageData"].UnitIdx.astype(int)
    )
    plants = append_keep_index_name(grid_new.plant, storage_plants)
    plants = plants[
        ~plants.type.isin(["dfo", "other"])
    ]  # drop these technologies, no cost data

    # BASE TECHNOLOGY COST

    # load in investment costs $/MW
    gen_costs = load_cost(year, cost_case)
    # keep only certain (arbitrary) subclasses for now
    gen_costs = gen_costs[
        gen_costs["TechDetail"].isin(const.gen_inv_cost_techdetails_to_keep)
    ]
    # rename techs to match grid object
    gen_costs.replace(const.gen_inv_cost_translation, inplace=True)
    gen_costs.drop(["Key", "FinancialCase", "CRPYears"], axis=1, inplace=True)
    # ATB technology costs merge
    plants = merge_keep_index(
        plants, gen_costs, right_on="Technology", left_on="type", how="left"
    )

    # REGIONAL COST MULTIPLIER

    # Find ReEDS regions of plants (for regional cost multipliers)
    plant_buses = plants.bus_id.unique()
    try:
        bus_reg = pd.read_csv(const.bus_reeds_regions_path, index_col="bus_id")
        if not set(plant_buses) <= set(bus_reg.index):
            missing_buses = set(plant_buses) - set(bus_reg.index)
            bus_reg = bus_reg.append(bus_to_reeds_reg(grid_new.bus.loc[missing_buses]))
            bus_reg.sort_index().to_csv(const.bus_reeds_regions_path)
    except FileNotFoundError:
        bus_reg = bus_to_reeds_reg(grid_new.bus.loc[plant_buses])
        bus_reg.sort_index().to_csv(const.bus_reeds_regions_path)
    plants = merge_keep_index(
        plants, bus_reg, left_on="bus_id", right_index=True, how="left"
    )

    # Determine one region 'r' for each plant, based on one of two mappings
    plants.loc[:, "r"] = ""
    # Some types get regional multipliers via 'wind regions' ('rs')
    wind_region_mask = plants["type"].isin(const.regional_multiplier_wind_region_types)
    plants.loc[wind_region_mask, "r"] = plants.loc[wind_region_mask, "rs"]
    # Other types get regional multipliers via 'BA regions' ('rb')
    ba_region_mask = plants["type"].isin(const.regional_multiplier_ba_region_types)
    plants.loc[ba_region_mask, "r"] = plants.loc[ba_region_mask, "rb"]
    plants.drop(["rs", "rb"], axis=1, inplace=True)

    # merge regional multipliers with plants
    region_multiplier = pd.read_csv(const.regional_multiplier_path)
    region_multiplier.replace(const.regional_multiplier_gen_translation, inplace=True)
    plants = merge_keep_index(
        plants,
        region_multiplier,
        left_on=["r", "Technology"],
        right_on=["r", "i"],
        how="left",
    )

    # multiply all together to get summed CAPEX ($)
    plants.loc[:, "cost"] = (
        plants["CAPEX"] * plants["Pmax"] * plants["reg_cap_cost_mult"]
    )

    # sum cost by technology
    plants.loc[:, "cost"] *= calculate_inflation(2018)
    if sum_results:
        return plants.groupby(["Technology"])["cost"].sum()
    else:
        return plants["cost"]
