import copy as cp

import numpy as np
import pandas as pd

from powersimdata.design.investment import const
from powersimdata.design.investment.create_mapping_files import (
    bus_to_neem_reg,
    bus_to_reeds_reg,
)
from powersimdata.input.grid import Grid
from powersimdata.scenario.scenario import Scenario
from powersimdata.utility.distance import haversine


def calculate_ac_inv_costs(scenario):
    """Given a Scenario object, calculate the total cost of building that scenario's
    upgrades of lines and transformers.
    Currently uses NEEM regions to find regional multipliers.
    Currently ignores financials, but all values are in 2010 $-year.
    Need to test that there aren't any na values in regional multipliers
    (some empty parts of table)

    :param powersimdata.scenario.scenario.Scenario scenario: scenario instance.
    :return: (*dict*) -- Total costs (line costs, transformer costs) (in $2010).
    """

    base_grid = Grid(scenario.info["interconnect"].split("_"))
    grid = scenario.state.get_grid()

    # find upgraded AC lines
    grid_new = cp.deepcopy(grid)
    # Reindex so that we don't get NaN when calculating upgrades for new branches
    base_grid.branch = base_grid.branch.reindex(grid_new.branch.index).fillna(0)
    grid_new.branch.rateA = grid.branch.rateA - base_grid.branch.rateA
    grid_new.branch = grid_new.branch[grid_new.branch.rateA != 0.0]

    costs = _calculate_ac_inv_costs(grid_new)
    return costs


def _calculate_ac_inv_costs(grid_new):
    """Given a grid, calculate the total cost of building that grid's
    lines and transformers.
    This function is separate from calculate_ac_inv_costs() for testing purposes.
    Currently counts Transformer and TransformerWinding as transformers.
    Currently uses NEEM regions to find regional multipliers.
    Currently ignores financials, but all values are in 2010 $-year.

    :param powersimdata.input.grid.Grid grid_new: grid instance.
    :return: (*dict*) -- Total costs (line costs, transformer costs) (in $2010).
    """

    def select_kv(x, cost_df):
        """Given a single branch, determine the closest kV category for cost purposes.
        :param pandas.core.series.Series x: data for a single branch.
        :param pandas.core.frame.DataFrame cost_df: DataFrame with kV, MW, cost columns.
        :return: (*numpy.int64*) -- kV_cost (closest kV) to be assigned to given branch.
        """
        return cost_df.loc[np.argmin(np.abs(cost_df["kV"] - x.kV)), "kV"]

    def select_mw(x, cost_df):
        """Given a single branch, determine the closest kV/MW combination and return
        the corresponding cost $/MW-mi.

        :param pandas.core.series.Series x: data for a single branch
        :param pandas.core.frame.DataFrame cost_df: DataFrame with kV, MW, cost columns
        :return: (*pandas.core.series.Series*) -- series of ['MW', 'costMWmi'] to be
            assigned to given branch
        """

        # select corresponding cost table of selected kV
        tmp = cost_df[cost_df["kV"] == x.kV]
        # get rid of NaN values in this kV table
        tmp = tmp[~tmp["MW"].isna()]
        # find closest MW & corresponding cost
        return tmp.iloc[np.argmin(np.abs(tmp["MW"] - x.rateA))][["MW", "costMWmi"]]

    # import data
    ac_cost = pd.DataFrame(const.ac_line_cost)
    ac_reg_mult = pd.read_csv(const.ac_reg_mult_path)
    xfmr_cost = pd.DataFrame(const.transformer_cost)

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

    lines.loc[:, "kV"] = lines.apply(lambda x: select_kv(x, ac_cost), axis=1)
    lines[["MW", "costMWmi"]] = lines.apply(lambda x: select_mw(x, ac_cost), axis=1)

    # multiply by regional multiplier
    bus_reg = pd.read_csv(const.bus_neem_regions_path, index_col="bus_id")

    # check that all buses included in this file and lat/long values match,
    #   otherwise re-run mapping script on mis-matching buses.

    # these buses are missing in region file
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
    bus_fix = bus[bus.index.isin(bus_fix_index_all)]
    if len(bus_fix_index_all) > 0:
        bus_fix = bus_to_neem_reg(bus_fix)  # converts index to bus_id instead
        bus_reg.loc[
            bus_reg.index.isin(bus_fix.index), ["name_abbr", "lat", "lon"]
        ] = bus_fix[["name_abbr", "lat", "lon"]]

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

    # sum of all line costs
    lines_sum = float(lines.Cost.sum())

    # calculate transformer costs
    transformers.loc[:, "kV"] = transformers.apply(
        lambda x: select_kv(x, xfmr_cost), axis=1
    )
    transformers = transformers.merge(xfmr_cost, on="kV", how="left")

    # sum of all transformer costs
    transformers_sum = float(transformers.Cost.sum())

    dict1 = {"line_cost": lines_sum, "transformer_cost": transformers_sum}
    return dict1


def calculate_dc_inv_costs(scenario):
    """Given a Scenario object, calculate the total cost of that grid's dc line
        investment. Currently ignores financials, but all values are in 2015 $-year.

    :param powersimdata.scenario.scenario.Scenario scenario: scenario instance.
    :return: (*float*) -- Total dc line costs (in $2015).
    """
    base_grid = Grid(scenario.info["interconnect"].split("_"))
    grid = scenario.state.get_grid()

    grid_new = cp.deepcopy(grid)
    # Reindex so that we don't get NaN when calculating upgrades for new DC lines
    base_grid.dcline = base_grid.dcline.reindex(grid_new.dcline.index).fillna(0)
    # find upgraded DC lines
    grid_new.dcline.Pmax = grid.dcline.Pmax - base_grid.dcline.Pmax
    grid_new.dcline = grid_new.dcline[grid_new.dcline.Pmax != 0.0]

    costs = _calculate_dc_inv_costs(grid_new)
    return costs


def _calculate_dc_inv_costs(grid_new):
    """Given a grid, calculate the total cost of that grid's dc line investment.
    This function is separate from calculate_dc_inv_costs() for testing purposes.
    Currently ignores financials, but all values are in 2015 $-year.

    :param powersimdata.input.grid.Grid grid_new: grid instance.
    :return: (*float*) -- Total dc line costs (in $2015).
    """

    def _calculate_single_line_cost(line, bus):
        """Given a series representing a DC line upgrade/addition, and a dataframe of
        bus locations, calculate this line's upgrade cost.

        :param pandas.Series line: DC line series featuring:
            {"from_bus_id", "to_bus_id", "Pmax"}.
        :param pandas.Dataframe bus: Bus data frame featuring {"lat", "lon"}.
        :return: (*float*) -- DC line upgrade cost (in $2015).
        """
        # Calculate distance
        from_lat = bus.loc[line.from_bus_id, "lat"]
        from_lon = bus.loc[line.from_bus_id, "lon"]
        to_lat = bus.loc[line.to_bus_id, "lat"]
        to_lon = bus.loc[line.to_bus_id, "lon"]
        miles = haversine((from_lat, from_lon), (to_lat, to_lon))
        # Calculate cost
        mw_miles = miles * line.Pmax
        line_cost = mw_miles * const.hvdc_line_cost["costMWmi"]
        total_cost = line_cost + const.hvdc_terminal_cost_per_MW * line.Pmax
        return total_cost

    bus = grid_new.bus
    dcline = grid_new.dcline

    # if any dclines, do calculations, otherwise, return 0 costs.
    if len(dcline != 0):
        return dcline.apply(_calculate_single_line_cost, args=(bus,), axis=1).sum()
    else:
        return 0


def calculate_gen_inv_costs(scenario, year, cost_case):
    """Given a Scenario object, calculate the total cost of building that scenario's
        upgrades of generation.
    Currently only uses one (arbutrary) sub-technology. Drops the rest of the costs.
        Will want to fix for wind/solar (based on resource supply curves).
    Currently uses ReEDS regions to find regional multipliers.
    Currently ignores financials, but all values are in 2018 $-year.

    :param powersimdata.scenario.scenario.Scenario scenario: scenario instance.
    :param int/str year: year of builds.
    :param str cost_case: the ATB cost case of data:
        'Moderate': mid cost case,
        'Conservative': generally higher costs,
        'Advanced': generally lower costs
    :return: (*pandas.DataFrame*) -- Total generation investment cost summed by
        technology (in $2018).
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

    costs = _calculate_gen_inv_costs(grid_new, year, cost_case)
    return costs


def _calculate_gen_inv_costs(grid_new, year, cost_case):
    """Given a grid, calculate the total cost of building that generation investment.
    Computes total capital cost as CAPEX_total =
        CAPEX ($/MW) * Pmax (MW) * reg_cap_cost_mult (regional cost multiplier)
    This function is separate from calculate_gen_inv_costs() for testing purposes.
    Currently only uses one (arbutrary) sub-technology. Drops the rest of the costs.
        Will want to fix for wind/solar (based on resource supply curves).
    Currently uses ReEDS regions to find regional multipliers.
    Currently ignores financials, but all values are in 2018 $-year.

    :param powersimdata.input.grid.Grid grid_new: grid instance.
    :param int/str year: year of builds (used in financials).
    :param str cost_case: the ATB cost case of data:
        'Moderate': mid cost case
        'Conservative': generally higher costs
        'Advanced': generally lower costs
    :raises ValueError: if year not 2020 - 2050, or cost case not an allowed option.
    :raises TypeError: if year gets the wrong type, or if cost_case is not str.
    :return: (*pandas.Series*) -- Total generation investment cost,
        summed by technology (in $2018).
    """

    def load_cost(year, cost_case):
        """
        Load in base costs from NREL's 2020 ATB for generation technologies (CAPEX).
            Can be adapted in the future for FOM, VOM, & CAPEX.
        This data is pulled from the ATB xlsx file Summary pages (saved as csv's).
        Therefore, currently uses default financials, but will want to create custom
            financial functions in the future.

        :param int/str year: year of cost projections.
        :param str cost_case: the ATB cost case of data
            (see :py:func:`write_poly_shapefile` for details).
        :return: (*pandas.DataFrame*) -- Cost by technology/subtype (in $2018).
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
        cost["value"] = cost["value"].str.replace("$", "")
        cost["value"] = cost["value"].str.replace(",", "").astype("float64")
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
    tech_sum = plants.groupby(["Technology"])["CAPEX_total"].sum()
    return tech_sum
