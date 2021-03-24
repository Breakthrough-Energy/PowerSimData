import copy as cp

import numpy as np
import pandas as pd

from powersimdata.design.investment import const
from powersimdata.design.investment.create_mapping_files import (
    bus_to_neem_reg,
    bus_to_reeds_reg,
)
from powersimdata.design.investment.inflation import calculate_inflation
from powersimdata.input.grid import Grid
from powersimdata.utility.distance import haversine


def calculate_ac_inv_costs(scenario, sum_results=True, exclude_branches=None):
    """Calculate cost of upgrading AC lines and/or transformers in a scenario.
    NEEM regions are used to find regional multipliers.

    :param powersimdata.scenario.scenario.Scenario scenario: scenario instance.
    :param bool sum_results: sum data frame for each branch type.
    :return: (*dict*) -- cost of upgrading branches in $2010.
    """

    base_grid = Grid(scenario.info["interconnect"].split("_"))
    grid = scenario.state.get_grid()

    # find upgraded AC lines
    grid_new = cp.deepcopy(grid)
    # Reindex so that we don't get NaN when calculating upgrades for new branches
    base_grid.branch = base_grid.branch.reindex(grid_new.branch.index).fillna(0)
    grid_new.branch.rateA = grid.branch.rateA - base_grid.branch.rateA
    grid_new.branch = grid_new.branch[grid_new.branch.rateA != 0.0]
    if exclude_branches is not None:
        present_exclude_branches = set(exclude_branches) & set(grid_new.branch.index)
        grid_new.branch.drop(index=present_exclude_branches, inplace=True)

    costs = _calculate_ac_inv_costs(grid_new, sum_results)
    return costs


def _calculate_ac_inv_costs(grid_new, sum_results=True):
    """Calculate cost of upgrading AC lines and/or transformers. NEEM regions are
    used to find regional multipliers. Note that a transformer winding is considered
    as a transformer.

    :param powersimdata.input.grid.Grid grid_new: grid instance.
    :param bool sum_results: sum data frame for each branch type.
    :return: (*dict*) -- cost of upgrading branches in $2010.
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

        # select corresponding cost table of selected kV
        tmp = cost_df[cost_df["kV"] == x.kV]
        # get rid of NaN values in this kV table
        tmp = tmp[~tmp["MW"].isna()]
        # find closest MW & corresponding cost
        return tmp.iloc[np.argmin(np.abs(tmp["MW"] - x.rateA))][["MW", "costMWmi"]]

    def get_transformer_mult(x, bus_reg, ac_reg_mult, xfmr_lookup_alerted=set()):
        """Determine the regional multiplier based on kV and power (closest).

        :param pandas.Series x: data for a single transformer.
        :param pandas.DataFrame bus_reg: data frame with bus regions.
        :param pandas.DataFrame ac_reg_mult: data frame with regional multipliers.
        :param set xfmr_lookup_alerted: set of (voltage, region) tuples for which
            a message has already been printed that this lookup was not found.
        :return: (*float*) -- regional multiplier.
        """
        max_kV = bus.loc[[x.from_bus_id, x.to_bus_id], "baseKV"].max()  # noqa: N806
        region = bus_reg.loc[x.from_bus_id, "name_abbr"]
        region_mults = ac_reg_mult.loc[ac_reg_mult.name_abbr == region]

        mult_lookup_kV = region_mults.loc[  # noqa: N806
            (region_mults.kV - max_kV).abs().idxmin()
        ].kV
        region_kV_mults = region_mults[region_mults.kV == mult_lookup_kV]  # noqa: N806
        region_kV_mults = region_kV_mults.loc[  # noqa: N806
            ~region_kV_mults.mult.isnull()
        ]
        if len(region_kV_mults) == 0:
            mult = 1
            if (mult_lookup_kV, region) not in xfmr_lookup_alerted:
                print(f"No multiplier for voltage {mult_lookup_kV} in {region}")
                xfmr_lookup_alerted.add((mult_lookup_kV, region))
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
    try:
        bus_reg = pd.read_csv(const.bus_neem_regions_path, index_col="bus_id")
    except FileNotFoundError:
        bus_reg = bus_to_neem_reg(grid_new.bus)
        bus_reg.sort_index().to_csv(const.bus_neem_regions_path)
    xfmr_cost = pd.read_csv(const.transformer_cost_path, index_col=0).fillna(0)
    xfmr_cost.columns = [int(c) for c in xfmr_cost.columns]
    # Mirror across diagonal
    xfmr_cost += xfmr_cost.to_numpy().T - np.diag(np.diag(xfmr_cost.to_numpy()))

    # map line kV
    bus = grid_new.bus
    branch = grid_new.branch
    branch.loc[:, "kV"] = branch.apply(
        lambda x: bus.loc[x.from_bus_id, "baseKV"], axis=1
    )

    # separate transformers and lines
    t_mask = branch["branch_device_type"].isin(["Transformer", "TransformerWinding"])
    transformers = branch[t_mask].copy()
    lines = branch[~t_mask].copy()
    # Find closest kV rating
    lines.loc[:, "kV"] = lines.apply(
        lambda x: ac_cost.loc[(ac_cost["kV"] - x.kV).abs().idxmin(), "kV"],
        axis=1,
    )
    lines[["MW", "costMWmi"]] = lines.apply(lambda x: select_mw(x, ac_cost), axis=1)

    # check that all buses included in this file and lat/long values match,
    # otherwise re-run mapping script on mis-matching buses. These buses are missing
    # in region file
    bus_fix_index = bus[~bus.index.isin(bus_reg.index)].index
    bus_mask = bus[~bus.index.isin(bus_fix_index)]
    bus_mask = bus_mask.merge(bus_reg, how="left", on="bus_id")
    # these buses have incorrect lat/lon values in the region mapping file.
    #   re-running the region mapping script on those buses only.
    bus_fix_index2 = bus_mask[
        ~np.isclose(bus_mask.lat_x, bus_mask.lat_y)
        | ~np.isclose(bus_mask.lon_x, bus_mask.lon_y)
    ].index
    bus_fix_index_all = bus_fix_index.tolist() + bus_fix_index2.tolist()
    # fix the identified buses, if necessary
    if len(bus_fix_index_all) > 0:
        bus_fix = bus_to_neem_reg(bus[bus.index.isin(bus_fix_index_all)])
        fix_cols = ["name_abbr", "lat", "lon"]
        bus_reg.loc[bus_reg.index.isin(bus_fix.index), fix_cols] = bus_fix[fix_cols]

    bus_reg.drop(["lat", "lon"], axis=1, inplace=True)

    # map region multipliers onto lines
    ac_reg_mult = ac_reg_mult.melt(
        id_vars=["kV", "MW"], var_name="name_abbr", value_name="mult"
    )

    lines = lines.merge(bus_reg, left_on="to_bus_id", right_on="bus_id", how="inner")
    lines = lines.merge(ac_reg_mult, on=["name_abbr", "kV", "MW"], how="left")
    lines.rename(columns={"name_abbr": "reg_to", "mult": "mult_to"}, inplace=True)

    lines = lines.merge(bus_reg, left_on="from_bus_id", right_on="bus_id", how="inner")
    lines = lines.merge(ac_reg_mult, on=["name_abbr", "kV", "MW"], how="left")
    lines.rename(columns={"name_abbr": "reg_from", "mult": "mult_from"}, inplace=True)

    # take average between 2 buses' region multipliers
    lines.loc[:, "mult"] = (lines["mult_to"] + lines["mult_from"]) / 2.0

    # calculate MWmi
    lines.loc[:, "lengthMi"] = lines.apply(
        lambda x: haversine((x.from_lat, x.from_lon), (x.to_lat, x.to_lon)), axis=1
    )
    lines.loc[:, "MWmi"] = lines["lengthMi"] * lines["rateA"]

    # calculate cost of each line
    lines.loc[:, "Cost"] = lines["MWmi"] * lines["costMWmi"] * lines["mult"]

    # calculate transformer costs
    transformers["per_MW_cost"] = transformers.apply(
        lambda x: xfmr_cost.iloc[
            xfmr_cost.index.get_loc(bus.loc[x.from_bus_id, "baseKV"], method="nearest"),
            xfmr_cost.columns.get_loc(bus.loc[x.to_bus_id, "baseKV"], method="nearest"),
        ],
        axis=1,
    )
    transformers["mult"] = transformers.apply(
        lambda x: get_transformer_mult(x, bus_reg, ac_reg_mult), axis=1
    )

    transformers["Cost"] = (
        transformers["rateA"] * transformers["per_MW_cost"] * transformers["mult"]
    )

    lines.Cost *= calculate_inflation(2010)
    transformers.Cost *= calculate_inflation(2020)
    if sum_results:
        return {
            "line_cost": lines.Cost.sum(),
            "transformer_cost": transformers.Cost.sum(),
        }
    else:
        return {"line_cost": lines, "transformer_cost": transformers}


def calculate_dc_inv_costs(scenario, sum_results=True):
    """Calculate cost of upgrading HVDC lines in a scenario.

    :param powersimdata.scenario.scenario.Scenario scenario: scenario instance.
    :param bool sum_results: sum series to return total cost.
    :return: (*pandas.Series/float*) -- cost of upgrading HVDC lines in $2015.
    """
    base_grid = Grid(scenario.info["interconnect"].split("_"))
    grid = scenario.state.get_grid()

    grid_new = cp.deepcopy(grid)
    # Reindex so that we don't get NaN when calculating upgrades for new DC lines
    base_grid.dcline = base_grid.dcline.reindex(grid_new.dcline.index).fillna(0)
    # find upgraded DC lines
    grid_new.dcline.Pmax = grid.dcline.Pmax - base_grid.dcline.Pmax
    grid_new.dcline = grid_new.dcline[grid_new.dcline.Pmax != 0.0]

    costs = _calculate_dc_inv_costs(grid_new, sum_results)
    return costs


def _calculate_dc_inv_costs(grid_new, sum_results=True):
    """Calculate cost of upgrading HVDC lines.

    :param powersimdata.input.grid.Grid grid_new: grid instance.
    :param bool sum_results: sum series to return total cost.
    :return: (*pandas.Series/float*) -- cost of upgrading HVDC lines in $2015.
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


def calculate_gen_inv_costs(scenario, year, cost_case, sum_results=True):
    """Calculate cost of upgrading generators in a scenario. ReEDS regions are used to
    find regional multipliers.

    :param powersimdata.scenario.scenario.Scenario scenario: scenario instance.
    :param int/str year: building year.
    :param str cost_case: ATB cost case of data. *'Moderate'*: mid cost case,
        *'Conservative'*: generally higher costs, *'Advanced'*: generally lower costs
    :return: (*pandas.DataFrame*) -- total generation investment cost summed by
        technology.

    .. todo:: it currently uses one (arbitrary) sub-technology. The rest of the costs
        are dropped. Wind and solar will need to be fixed based on the resource supply
        curves.
    """

    base_grid = Grid(scenario.info["interconnect"].split("_"))
    grid = scenario.state.get_grid()

    # Find change in generation capacity
    grid_new = cp.deepcopy(grid)
    # Reindex so that we don't get NaN when calculating upgrades for new generators
    base_grid.plant = base_grid.plant.reindex(grid_new.plant.index).fillna(0)
    grid_new.plant.Pmax = grid.plant.Pmax - base_grid.plant.Pmax
    # Find change in storage capacity
    # Reindex so that we don't get NaN when calculating upgrades for new storage
    base_grid.storage["gen"] = base_grid.storage["gen"].reindex(
        grid_new.storage["gen"].index, fill_value=0
    )
    grid_new.storage["gen"].Pmax = (
        grid.storage["gen"].Pmax - base_grid.storage["gen"].Pmax
    )
    grid_new.storage["gen"]["type"] = "storage"

    # Drop small changes
    grid_new.plant = grid_new.plant[grid_new.plant.Pmax > 0.01]

    costs = _calculate_gen_inv_costs(grid_new, year, cost_case, sum_results)
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
    :return: (*pandas.Series*) -- total generation investment cost, summed by
        technology.

    .. note:: the function computes the total capital cost as:
        CAPEX_total = CAPEX ($/MW) * Pmax (MW) * regional multiplier
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

    plants = grid_new.plant.append(grid_new.storage["gen"])
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
    plants = plants.merge(gen_costs, right_on="Technology", left_on="type", how="left")

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
    plants = plants.merge(bus_reg, left_on="bus_id", right_index=True, how="left")

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
    plants = plants.merge(
        region_multiplier, left_on=["r", "Technology"], right_on=["r", "i"], how="left"
    )

    # multiply all together to get summed CAPEX ($)
    plants.loc[:, "CAPEX_total"] = (
        plants["CAPEX"] * plants["Pmax"] * plants["reg_cap_cost_mult"]
    )

    # sum cost by technology
    plants.loc[:, "CAPEX_total"] *= calculate_inflation(2018)
    if sum_results:
        return plants.groupby(["Technology"])["CAPEX_total"].sum()
    else:
        return plants
