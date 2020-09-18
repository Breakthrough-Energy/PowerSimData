import copy as cp
import os

import numpy as np
import pandas as pd

from powersimdata.design.investment.create_mapping_files import (
    bus_to_neem_reg,
    plant_to_reeds_reg,
)
from powersimdata.input.grid import Grid
from powersimdata.scenario.scenario import Scenario
from powersimdata.utility.distance import haversine


def calculate_ac_inv_costs(scenario, year):
    """Given a Scenario object, calculate the total cost of building that scenario's upgrades of
    lines and transformers.
    Currently ignores TransformerWinding.
    Currently uses NEEM regions to find regional multipliers.
    Currently ignores financials, but all values are in 2010 $-year.
    Need to test that there aren't any na values in regional multipliers (some empty parts of table)

    :param powersimdata.scenario.scenario.Scenario scenario: scenario instance.
    :param int/str year: the year of the transmission upgrades.
    :return: (*dict*) -- Total costs (line costs, transformer costs) (in $2010).
    """

    base_grid = Grid(scenario.info["interconnect"].split("_"))
    grid = scenario.state.get_grid()

    # find upgraded AC lines
    grid_new = cp.deepcopy(grid)
    grid_new.branch.rateA = grid.branch.rateA - base_grid.branch.rateA
    grid_new.branch.x = base_grid.branch.x - grid.branch.x
    grid_new.branch = grid_new.branch[grid_new.branch.rateA != 0.0]

    costs = _calculate_ac_inv_costs(grid_new, year)
    return costs


def _calculate_ac_inv_costs(grid_new, year):
    """Given a grid, calculate the total cost of building that grid's
    lines and transformers.
    This function is separate from calculate_ac_inv_costs() for testing purposes.
    Currently ignores TransformerWinding.
    Currently uses NEEM regions to find regional multipliers.
    Currently ignores financials, but all values are in 2010 $-year.

    :param powersimdata.input.grid.Grid grid_new: grid instance.
    :param int/str year: year of builds (used in financials).
    :raises ValueError: if year not 2020 - 2050.
    :raises TypeError: if year gets the wrong type.
    :return: (*dict*) -- Total costs (line costs, transformer costs) (in $2010).
    """

    def select_kv(x, cost_df):
        """Given a single branch, determine the closest kV category for cost purposes.
        :param pandas.core.series.Series x: data for a single branch.
        :param pandas.core.frame.DataFrame cost_df: DataFrame with kV, MW, cost columns.
        :return: (*numpy.int64*) -- kV_cost (closest kV) to be assigned to given branch.
        """
        return cost_df.loc[np.argmin(np.abs(cost_df["kV_cost"] - x.kV)), "kV_cost"]

    def select_mw(x, cost_df):
        """Given a single branch, determine the closest kV/MW combination and return the corresponding cost $/MW-mi.
        :param pandas.core.series.Series x: data for a single branch
        :param pandas.core.frame.DataFrame cost_df: DataFrame with kV, MW, cost columns
        :return: (*pandas.core.series.Series*) -- series of ['MW', 'costMWmi'] to be assigned to given branch
        """

        # select corresponding cost table of delected kV
        tmp = cost_df[cost_df["kV_cost"] == x.kV_cost]
        # get rid of NaN values in this kV table
        tmp = tmp[~tmp["MW"].isna()]
        # find closest MW & corresponding cost
        return tmp.iloc[np.argmin(np.abs(tmp["MW"] - x.rateA))][["MW", "costMWmi"]]

    if isinstance(year, (int, str)):
        year = int(year)
        if year not in range(2020, 2051):
            raise ValueError("year not in range.")
    else:
        raise TypeError("year must be int or str.")

    data_dir = os.path.join(os.path.dirname(__file__), "Data")

    # import data
    ac_cost = pd.read_csv(os.path.join(data_dir, "LineBase.csv"))
    ac_reg_mult = pd.read_csv(os.path.join(data_dir, "LineRegMult.csv"))
    xfmr_cost = pd.read_csv(os.path.join(data_dir, "Transformers.csv"))

    # map line kV
    bus = grid_new.bus
    branch = grid_new.branch
    branch.loc[:, "kV"] = branch.apply(
        lambda x: bus.loc[x.from_bus_id, "baseKV"], axis=1
    )

    # separate transformers and lines
    transformers = branch[
        branch["branch_device_type"].isin(["Transformer", "TransformerWinding"])
    ].copy()
    lines = branch[
        ~branch["branch_device_type"].isin(["Transformer", "TransformerWinding"])
    ].copy()

    lines.loc[:, "kV_cost"] = lines.apply(lambda x: select_kv(x, ac_cost), axis=1)
    lines[["MW", "costMWmi"]] = lines.apply(lambda x: select_mw(x, ac_cost), axis=1)

    # multiply by regional multiplier, add in when script finishes running.
    bus_reg = pd.read_csv(
        os.path.join(data_dir, "buses_NEEMregion.csv"), index_col="bus_id"
    )

    # check that all buses included in this file and lat/long values match, otherwise re-run mapping script on mis-matching buses.

    # these buses are missing in region file
    bus_fix_index = bus[~bus.index.isin(bus_reg.index)].index
    bus_mask = bus[~bus.index.isin(bus_fix_index)]
    bus_mask = bus_mask.merge(bus_reg, how="left", on="bus_id")

    # these buses have incorrect lat/lon values in the region mapping file. re-running the region mapping script on those buses only.
    bus_fix_index2 = bus_mask[
        ~np.isclose(bus_mask.lat_x, bus_mask.lat_y)
        | ~np.isclose(bus_mask.lon_x, bus_mask.lon_y)
    ].index
    bus_fix_index_all = bus_fix_index.tolist() + bus_fix_index2.tolist()
    bus_fix = bus[bus.index.isin(bus_fix_index_all)]
    bus_fix = bus_to_neem_reg(bus_fix, data_dir)  # converts index to bus_id instead

    bus_reg.loc[
        bus_reg.index.isin(bus_fix.index), ["name_abbr", "lat", "lon"]
    ] = bus_fix[["name_abbr", "lat", "lon"]]
    bus_reg.drop(["lat", "lon"], axis=1, inplace=True)

    # map region multipliers onto lines
    ac_reg_mult = ac_reg_mult.melt(
        id_vars=["kV_cost", "MW"], var_name="name_abbr", value_name="mult"
    )

    lines = lines.merge(bus_reg, left_on="to_bus_id", right_on="bus_id", how="inner")
    lines = lines.merge(ac_reg_mult, on=["name_abbr", "kV_cost", "MW"], how="left")
    lines.rename(columns={"name_abbr": "reg_to", "mult": "mult_to"}, inplace=True)

    lines = lines.merge(bus_reg, left_on="from_bus_id", right_on="bus_id", how="inner")
    lines = lines.merge(ac_reg_mult, on=["name_abbr", "kV_cost", "MW"], how="left")
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
    transformers.loc[:, "kV_cost"] = transformers.apply(
        lambda x: select_kv(x, xfmr_cost), axis=1
    )
    transformers = transformers.merge(xfmr_cost, on="kV_cost", how="left")

    # sum of all transformer costs
    transformers_sum = float(transformers.Cost.sum())

    dict1 = {"line_cost": lines_sum, "transformer_cost": transformers_sum}
    return dict1


def calculate_dc_inv_costs(scenario, year):
    """Given a Scenario object, calculate the total cost of that grid's dc line investment.
    This function is separate from calculate_dc_inv_costs() for testing purposes.
    Currently ignores financials, but all values are in 2015 $-year.

    :param powersimdata.scenario.scenario.Scenario scenario: scenario instance.
    :param int/str year: the year of the upgrade to calculate costs
    :return: (*float*) -- Total dc line costs (in $2015).
    """
    base_grid = Grid(scenario.info["interconnect"].split("_"))
    grid = scenario.state.get_grid()

    # find upgraded AC lines
    grid_new = cp.deepcopy(grid)
    grid_new.dcline.Pmax = grid.dcline.Pmax - base_grid.dcline.Pmax
    grid_new.dcline = grid_new.dcline[grid_new.dcline.Pmax != 0.0]

    costs = _calculate_dc_inv_costs(grid_new, year)
    return costs


def _calculate_dc_inv_costs(grid_new, year):
    """Given a grid, calculate the total cost of that grid's dc line investment.
    This function is separate from calculate_dc_inv_costs() for testing purposes.
    Currently ignores financials, but all values are in 2015 $-year.

    :param powersimdata.input.grid.Grid grid_new: grid instance.
    :param int/str year: year of builds (used in financials).
    :raises ValueError: if year not 2020 - 2050.
    :raises TypeError: if year gets the wrong type.
    :return: (*float*) -- Total dc line costs (in $2015).
    """

    if isinstance(year, (int, str)):
        year = int(year)
        if year not in range(2020, 2051):
            raise ValueError("year not in range.")
    else:
        raise TypeError("year must be int or str.")

    data_dir = os.path.join(os.path.dirname(__file__), "Data")

    # import data
    dc_cost = pd.read_csv(os.path.join(data_dir, "HVDC.csv"))  # .astype('float64')
    dc_term_cost = pd.read_csv(
        os.path.join(data_dir, "HVDCTerminal.csv")
    )  # .astype('float64')

    bus = grid_new.bus
    dcline = grid_new.dcline

    # if any dclines, do calculations, otherwise, return 0 costs.
    if len(dcline != 0):
        # Find line length
        dcline["from_lat"] = dcline.apply(
            lambda x: bus.loc[x.from_bus_id, "lat"], axis=1
        )
        dcline["from_lon"] = dcline.apply(
            lambda x: bus.loc[x.from_bus_id, "lon"], axis=1
        )

        dcline["to_lat"] = dcline.apply(lambda x: bus.loc[x.to_bus_id, "lat"], axis=1)
        dcline["to_lon"] = dcline.apply(lambda x: bus.loc[x.to_bus_id, "lon"], axis=1)

        dcline["lengthMi"] = dcline.apply(
            lambda x: haversine((x.from_lat, x.from_lon), (x.to_lat, x.to_lon)), axis=1
        )
        dcline = dcline[dcline["lengthMi"] != 0]

        # Calculate MWmi value
        dcline["MWmi"] = dcline["lengthMi"] * dcline["Pmax"]

        # Find $/MW-mi cost
        dcline.loc[:, "costMWmi"] = dc_cost["costMWmi"][0]

        # Find base cost (excluding terminal cost)
        dcline["Cost"] = dcline["MWmi"] * dcline["costMWmi"]

        # Add extra terminal cost for dc
        dcline["Cost"] += dc_term_cost["costTerm"][0]
        # Find sum of costs over all dclines
        costs = dcline["Cost"].sum()
    else:
        costs = 0

    return costs


def calculate_gen_inv_costs(scenario, year, cost_case):
    """Given a Scenario object, calculate the total cost of building that scenario's upgrades of generation.
    Currently only uses one (arbutrary) sub-technology. Drops the rest of the costs. Will want to fix for wind/solar (based on resource supply curves).
    Currently uses ReEDS regions to find regional multipliers.
    Currently ignores financials, but all values are in 2018 $-year.

    :param powersimdata.scenario.scenario.Scenario scenario: scenario instance.
    :param int/str year: year of builds.
    :param str cost_case: the ATB cost case of data ['Moderate': mid cost case,'Conservative': generally higher costs,'Advanced': generally lower costs]
    :return: (*pandas.DataFrame*) -- Total generation investment cost summed by technology (in $2018).
    """

    base_grid = Grid(scenario.info["interconnect"].split("_"))
    grid = scenario.state.get_grid()

    # Find change in generation capacity
    grid_new = cp.deepcopy(grid.plant)
    grid_new.plant.Pmin = grid.plant.Pmin - base_grid.plant.Pmin
    grid_new.plant.Pmax = grid.plant.Pmax - base_grid.plant.Pmax

    # Drop small changes
    grid_new.plant = grid_new.plant[grid_new.plant.Pmax > 0.01]

    costs = _calculate_gen_inv_costs(grid_new, year, cost_case)
    return costs


def _calculate_gen_inv_costs(grid_new, year, cost_case):
    """Given a grid, calculate the total cost of building that generation investment.
    Computes total capital cost as CAPEX_total = CAPEX ($/MW) * Pmax (MW) * reg_cap_cost_mult [regional cost multiplier]
    This function is separate from calculate_gen_inv_costs() for testing purposes.
    Currently only uses one (arbutrary) sub-technology. Drops the rest of the costs. Will want to fix for wind/solar (based on resource supply curves).
    Currently uses ReEDS regions to find regional multipliers.
    Currently ignores financials, but all values are in 2018 $-year.

    :param powersimdata.input.grid.Grid grid_new: grid instance.
    :param int/str year: year of builds (used in financials).
    :param str cost_case: the ATB cost case of data ['Moderate': mid cost case,'Conservative': generally higher costs,'Advanced': generally lower costs]
    :raises ValueError: if year not 2020 - 2050.
    :raises TypeError: if year gets the wrong type.
    :raises TypeError: if cost_case is not str.
    :raises ValueError: if cost_case is not in ['Moderate','Conservative','Advanced']
    :return: (*pandas.DataFrame*) -- Total generation investment cost summed by technology (in $2018).
    """

    def load_cost(file_name, year, cost_case, data_dir):
        """
        Load in base costs from NREL's 2020 ATB for generation technologies. Can be used in the future for FOM, VOM, CAPEX.
        This data is pulled from the ATB xlsx file Summary pages (saved as csv's).
        Therefore, currently uses default financials, but will want to create custom financial functions in the future.

        :param str file_name: name of file with ATB data to read in
        :param int/str year: year of cost projections.
        :param str cost_case: the ATB cost case of data ['Moderate': mid cost case,'Conservative': generally higher costs,'Advanced': generally lower costs]
        :param str data_dir: the Data directory.
        :return: (*pandas.DataFrame*) -- Cost by technology/subtype (in $2018).
        """
        pre = "2020-ATB-Summary"
        if file_name != "":
            pre = pre + "_"
        cost = pd.read_csv(os.path.join(data_dir, pre + file_name + ".csv"))
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

        # scale from $/kW to $/MW (for CAPEX + FOM)
        if file_name in ["CAPEX", "FOM"]:
            cost["value"] = 1000 * cost["value"]

        cost.rename(columns={"value": file_name}, inplace=True)

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
        if year not in ["Moderate", "Conservative", "Advanced"]:
            raise ValueError("cost_case not Moderate, Conservative, or Advanced")
    else:
        raise TypeError("cost_case must be str.")

    data_dir = os.path.join(os.path.dirname(__file__), "Data")

    plants = grid_new.plant
    plants = plants[
        ~plants.type.isin(["dfo", "other"])
    ]  # drop these technologies, no cost data

    # BASE TECHNOLOGY COST

    # load in investment costs $/MW
    gen_costs = load_cost("CAPEX", year, cost_case, data_dir)
    # keep only certain (arbutrary) subclasses for now
    gen_costs = gen_costs[
        gen_costs["TechDetail"].isin(
            [
                "HydroFlash",
                "NPD1",
                "newAvgCF",
                "Class1",
                "CCAvgCF",
                "OTRG1",
                "LTRG1",
                "4Hr Battery Storage",
                "Seattle",
            ]
        )
    ]  # only keep HydroFlash for geothermal
    # rename techs to match grid object
    gen_costs.replace(
        [
            "OffShoreWind",
            "LandbasedWind",
            "UtilityPV",
            "Battery",
            "CSP",
            "NaturalGas",
            "Hydropower",
            "Nuclear",
            "Biopower",
            "Geothermal",
            "Coal",
        ],
        [
            "wind_offshore",
            "wind",
            "solar",
            "storage",
            "csp",
            "ng",
            "hydro",
            "nuclear",
            "bio",
            "geothermal",
            "coal",
        ],
        inplace=True,
    )
    gen_costs.drop(["Key", "FinancialCase", "CRPYears"], axis=1, inplace=True)
    # ATB technology costs merge
    plants = plants.merge(gen_costs, right_on="Technology", left_on="type", how="left")

    # REGIONAL COST MULTIPLIER

    # Find ReEDS regions of plants (for regional cost multipliers)
    pts_plant = plant_to_reeds_reg(plants, data_dir)
    plants = plants.merge(pts_plant, on="plant_id", how="left")

    # keep region 'r' as wind region 'rs' if tech is wind, 'rb' ba region is tech is solar or battery
    plants.loc[:, "r"] = ""
    rs_tech = [
        "wind",
        "wind_offshore",
        "csp",
    ]  # wind regions (rs) (apply to wind and csp)
    plants.loc[plants["type"].isin(rs_tech), "r"] = plants.loc[
        plants["type"].isin(rs_tech), "rs"
    ]
    rb_tech = [
        "solar",
        "storage",
        "nuclear",
        "coal",
        "ng",
        "hydro",
        "geothermal",
    ]  # BA regions (rb) (apply to rest of techs)
    plants.loc[plants["type"].isin(rb_tech), "r"] = plants.loc[
        plants["type"].isin(rb_tech), "rb"
    ]
    plants.drop(["rs", "rb"], axis=1, inplace=True)

    # merge regional multipliers with plants
    region_multiplier = pd.read_csv("in/reg_cap_cost_mult_default.csv")
    region_multiplier = region_multiplier[
        region_multiplier["i"].isin(
            [
                "wind-ofs_1",
                "wind-ons_1",
                "upv_1",
                "battery",
                "coal-new",
                "Gas-CC",
                "Hydro",
                "Nuclear",
                "geothermal",
            ]
        )
    ]
    region_multiplier.replace(
        [
            "wind-ofs_1",
            "wind-ons_1",
            "upv_1",
            "battery",
            "Gas-CC",
            "Nuclear",
            "Hydro",
            "coal-new",
            "csp-ns",
        ],
        [
            "wind_offshore",
            "wind",
            "solar",
            "storage",
            "ng",
            "nuclear",
            "hydro",
            "coal",
            "csp",
        ],
        inplace=True,
    )
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
