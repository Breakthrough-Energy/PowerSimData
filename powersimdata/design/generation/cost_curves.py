import copy

import numpy as np
import pandas as pd

from powersimdata.input.grid import Grid
from powersimdata.network.model import area_to_loadzone
from powersimdata.utility.helpers import _check_import


def linearize_gencost(input_grid, num_segments=1):
    """Updates the generator cost information to include piecewise linear cost curve
    information. Allows the user to specify the number of piecewise segments into which
    the cost curve should be split.

    :param powersimdata.inout.grid.Grid input_grid: Grid object.
    :param int num_segments: The number of segments into which the piecewise linear
        cost curve will be split.
    :return: (*pandas.DataFrame*) -- An updated DataFrame containing the piecewise
        linear cost curve parameters.
    :raises ValueError: if the generator cost curve is not of an acceptable form.
    """

    # Access the generator cost and plant information components
    grid = copy.deepcopy(input_grid)
    gencost_before = grid.gencost["before"]
    plant = grid.plant

    # Raise errors if the provided cost curves are not in a form that can be handled
    if len(gencost_before[gencost_before.type != 2]):
        raise ValueError("gencost currently limited to polynomial")
    if len(gencost_before[gencost_before.n != 3]):
        raise ValueError("gencost currently limited to quadratic")

    # Access the quadratic cost curve information
    quad_term = gencost_before.c2
    lin_term = gencost_before.c1
    const_term = gencost_before.c0

    # Convert dispatchable generators to piecewise segments
    dispatchable_gens = plant.Pmin != plant.Pmax
    if sum(dispatchable_gens) > 0:
        gencost_after = pd.DataFrame(
            index=gencost_before.index,
            columns=["type", "startup", "shutdown", "n", "c2", "c1", "c0"],
        )
        gencost_after.loc[dispatchable_gens, "type"] = 1
        gencost_after[["startup", "shutdown", "c2", "c1", "c0"]] = gencost_before[
            ["startup", "shutdown", "c2", "c1", "c0"]
        ]
        gencost_after.loc[dispatchable_gens, "n"] = num_segments + 1
        power_step = (plant.Pmax - plant.Pmin) / num_segments
        for i in range(num_segments + 1):
            capacity_label = "p" + str(i + 1)
            price_label = "f" + str(i + 1)
            capacity_data = plant.Pmin + power_step * i
            price_data = (
                quad_term * capacity_data**2 + lin_term * capacity_data + const_term
            )
            gencost_after.loc[dispatchable_gens, capacity_label] = capacity_data[
                dispatchable_gens
            ]
            gencost_after.loc[dispatchable_gens, price_label] = price_data[
                dispatchable_gens
            ]
    else:
        grid.gencost["after"] = gencost_before.copy()

    # Convert non-dispatchable gens to fixed values
    nondispatchable_gens = ~dispatchable_gens
    if sum(nondispatchable_gens) > 0:
        gencost_after.loc[nondispatchable_gens, "type"] = gencost_before.loc[
            nondispatchable_gens, "type"
        ]
        gencost_after.loc[nondispatchable_gens, "n"] = gencost_before.loc[
            nondispatchable_gens, "n"
        ]
        power = plant.Pmax
        price_data = quad_term * power**2 + lin_term * power + const_term
        gencost_after.loc[nondispatchable_gens, ["c2", "c1"]] = 0
        gencost_after.loc[nondispatchable_gens, "c0"] = price_data[nondispatchable_gens]

    gencost_after["interconnect"] = gencost_before["interconnect"]

    # Return the updated generator cost information
    return gencost_after


def get_supply_data(grid, num_segments=1, save=None):
    """Accesses the generator cost and plant information data from a specified Grid
    object.

    :param powersimdata.input.grid.Grid grid: Grid object.
    :param int num_segments: The number of segments into which the piecewise linear
        cost curve will be split.
    :param str save: Saves a .csv if a str representing a valid file path and file
        name is provided. If None, nothing is saved.
    :return: (*pandas.DataFrame*) -- Supply information needed to analyze cost and
        supply curves.
    :raises TypeError: if a powersimdata.input.grid.Grid object is not input, or
        if the save parameter is not input as a str.
    """

    # Check that a Grid object is input
    if not isinstance(grid, Grid):
        raise TypeError("A Grid object must be input.")

    # Obtain a copy of the Grid object
    grid = copy.deepcopy(grid)

    # Access the generator cost and plant information data
    gencost_df = linearize_gencost(grid, num_segments)
    plant_df = grid.plant

    # Create a new DataFrame with the desired columns
    supply_df = pd.concat(
        [
            plant_df[["type", "interconnect", "zone_name"]],
            gencost_df[
                gencost_df.columns.difference(
                    ["type", "startup", "shutdown", "n", "interconnect"], sort=False
                )
            ],
        ],
        axis=1,
    )

    # Add p_diff and slope according to the number of cost curve segments
    for i in range(num_segments):
        supply_df["p_diff" + str(i + 1)] = (
            supply_df["p" + str(i + 2)] - supply_df["p" + str(i + 1)]
        )
        supply_df["slope" + str(i + 1)] = (
            supply_df["f" + str(i + 2)] - supply_df["f" + str(i + 1)]
        ) / supply_df["p_diff" + str(i + 1)]

    # Save the supply data to a .csv file if desired
    if save is not None:
        if not isinstance(save, str):
            raise TypeError("The file path and file name must be input as a str.")
        else:
            supply_df.to_csv(save)

    # Return the necessary supply information
    return supply_df


def check_supply_data(supply_data, num_segments=1):
    """Checks to make sure that the input supply data is a DataFrame and has the
    correct columns. This is especially needed for checking instances where the input
    supply data is not the DataFrame returned from get_supply_data().

    :param pandas.DataFrame supply_data: DataFrame containing the supply curve
        information.
    :param int num_segments: The number of segments into which the piecewise linear
        cost curve will be split.
    :raises TypeError: if the input supply data is not a pandas.DataFrame.
    :raises ValueError: if one of the mandatory columns is missing from the input
        supply data.
    """

    # Check that the data is input as a DataFrame
    if not isinstance(supply_data, pd.DataFrame):
        raise TypeError("supply_data must be input as a DataFrame.")

    # Mandatory columns to be contained in the DataFrame
    mand_cols = {
        "type",
        "interconnect",
        "zone_name",
        "c2",
        "c1",
        "c0",
    }

    # Add mandatory columns based on the number piecewise segments
    for i in range(num_segments + 1):
        mand_cols.update(["p" + str(i + 1), "f" + str(i + 1)])

        if i > 0:
            mand_cols.update(["p_diff" + str(i), "slope" + str(i)])

    # Make sure all of the mandatory columns are contained in the input DataFrame
    miss_cols = mand_cols - set(supply_data.columns)
    if len(miss_cols) > 0:
        raise ValueError(f'Missing columns: {", ".join(miss_cols)}')


def build_supply_curve(grid, num_segments, area, gen_type, area_type=None, plot=True):
    """Builds a supply curve for a specified area and generation type.

    :param powersimdata.input.grid.Grid grid: Grid object.
    :param int num_segments: The number of segments into which the piecewise linear
        cost curve is split.
    :param str area: Either the load zone, state name, state abbreviation, or
        interconnect.
    :param str/iterable gen_type: Generation type(s).
    :param str area_type: one of: *'loadzone'*, *'state'*, *'state_abbr'*,
        *'interconnect'*. Defaults to None, which allows
        :func:`powersimdata.network.model.area_to_loadzone` to infer the type.
    :param bool plot: If True, the supply curve plot is shown. If False, the plot is
        not shown.
    :return: (*tuple*) -- First element is a list of capacity (MW) amounts needed
        to create supply curve. Second element is a list of bids ($/MW) in the supply
        curve.
    :raises TypeError: if a powersimdata.input.grid.Grid object is not input.
    :raises ValueError: if the specified area or generator type is not applicable.
    """

    # Check that a Grid object is input
    if not isinstance(grid, Grid):
        raise TypeError("A Grid object must be input.")

    # Check that the desired number of linearized cost curve segments is an int
    if not isinstance(num_segments, int):
        raise TypeError(
            "The number of linearized cost curve segments must be input as an int."
        )

    # Check that whether a single generation type is specified
    if isinstance(gen_type, str):
        gen_type = set([gen_type])

    # Obtain the desired generator cost and plant information data
    supply_data = get_supply_data(grid, num_segments)

    # Check the input supply data
    check_supply_data(supply_data, num_segments)

    # Check to make sure the generator type is valid
    if len(gen_type - set(supply_data["type"].unique())) > 0:
        raise ValueError(f"{gen_type} contains invalid generation type.")

    # Identify the load zones that correspond to the specified area and area_type
    returned_zones = area_to_loadzone(grid.grid_model, area, area_type)

    # Trim the DataFrame to only be of the desired area and generation type
    supply_data = supply_data.loc[supply_data.zone_name.isin(returned_zones)]
    supply_data = supply_data.loc[supply_data.type.isin(gen_type)]

    # Remove generators that have no capacity (e.g., Maine coal generators)
    if supply_data["slope1"].isnull().values.any():
        supply_data.dropna(subset=["slope1"], inplace=True)

    # Check if the area contains generators of the specified type
    if supply_data.empty:
        return [], []

    # Combine the p_diff and slope information for each cost segment
    supply_df_cols = []
    for i in range(num_segments):
        supply_df_cols.append(
            supply_data.loc[:, ("p_diff" + str(i + 1), "slope" + str(i + 1))]
        )
        supply_df_cols[i].rename(
            columns={"p_diff" + str(i + 1): "p_diff", "slope" + str(i + 1): "slope"},
            inplace=True,
        )
    supply_df = pd.concat(supply_df_cols, axis=0)

    # Sort the trimmed DataFrame by slope
    supply_df = supply_df.sort_values(by="slope")
    supply_df = supply_df.reset_index(drop=True)

    # Determine the points that comprise the supply curve
    capacity_data = []
    price_data = []
    capacity_diff_sum = 0
    for i in supply_df.index:
        capacity_data.append(capacity_diff_sum)
        price_data.append(supply_df["slope"][i])
        capacity_data.append(supply_df["p_diff"][i] + capacity_diff_sum)
        price_data.append(supply_df["slope"][i])
        capacity_diff_sum += supply_df["p_diff"][i]

    # Plot the curve
    if plot:
        plt = _check_import("matplotlib.pyplot")
        plt.figure(figsize=[20, 10])
        plt.plot(capacity_data, price_data)
        plt.title(f"Supply curve for selected generators in {area}", fontsize=20)
        plt.legend(
            ["Generation types:\n{}".format("\n".join(list(gen_type)))], loc="best"
        )
        plt.xlabel("Capacity (MW)", fontsize=20)
        plt.ylabel("Price ($/MW)", fontsize=20)
        plt.xticks(fontsize=20)
        plt.yticks(fontsize=20)
        plt.show()

    # Return the capacity and bid amounts
    return capacity_data, price_data


def lower_bound_index(desired_capacity, capacity_data):
    """Determines the index of the lower capacity value that defines a price segment.
    Useful for accessing the prices associated with capacity values that aren't
    explicitly stated in the capacity lists that are generated by the
    build_supply_curve() function. Needed for ks_test().

    :param float/int desired_capacity: Capacity value for which you want to determine
        the index of the lowest capacity value in a price segment.
    :param list capacity_data: List of capacity values used to generate a supply curve.
    :return: (*int*) -- Index of a price segment's capacity lower bound.
    """

    # Check that the list is not empty and that the capacity falls within the list range
    if not capacity_data or capacity_data[0] > desired_capacity:
        return None

    # Get the index of the capacity that is immediately less than the desired capacity
    for i, j in enumerate(capacity_data):
        if j > desired_capacity:
            return i - 1


def ks_test(
    capacity_data1,
    price_data1,
    capacity_data2,
    price_data2,
    area=None,
    gen_type=None,
    plot=True,
):
    """Runs a test that is similar to the Kolmogorov-Smirnov test. This function takes
    two supply curves as inputs and returns the greatest difference in price between
    the two supply curves. This function requires that the supply curves offer the same
    amount of capacity.

    :param list capacity_data1: List of capacity values for the first supply curve.
    :param list price_data1: List of price values for the first supply curve.
    :param list capacity_data2: List of capacity values for the second supply curve.
    :param list price_data2: List of price values for the second supply curve.
    :param str area: Either the load zone, state name, state abbreviation, or
        interconnect. Defaults to None because it's not essential.
    :param str gen_type: Generation type. Defaults to None because it's not essential.
    :param bool plot: If True, the supply curve plot is shown. If False, the plot is
        not shown.
    :return: (*float*) -- The maximum price difference between the two supply curves.
    :raises TypeError: if the capacity and price inputs are not provided as lists.
    :raises ValueError: if the supply curves do not offer the same amount of capacity.
    """

    # Check that input capacities and prices are provided as lists
    if not all(
        isinstance(i, list)
        for i in [capacity_data1, price_data1, capacity_data2, price_data2]
    ):
        raise TypeError("Supply curve data must be input as lists.")

    # Check that the supply curves offer the same amount of capacity
    if max(capacity_data1) != max(capacity_data2):
        raise ValueError(
            "The two supply curves do not offer the same amount of capacity (MW)."
        )

    # Create a list that has every capacity value in which either supply curve steps up
    capacity_data_all = list(set(capacity_data1) | set(capacity_data2))
    capacity_data_all.sort()

    # For each capacity value, associate the two corresponding price values
    price_data_all = []
    for i in range(len(capacity_data_all)):
        # Determine the correpsonding price from the first supply curve
        if capacity_data_all[i] == capacity_data1[-1]:
            f1 = price_data1[-1]
        else:
            f1 = price_data1[lower_bound_index(capacity_data_all[i], capacity_data1)]

        # Determine the correpsonding price from the second supply curve
        if capacity_data_all[i] == capacity_data2[-1]:
            f2 = price_data2[-1]
        else:
            f2 = price_data2[lower_bound_index(capacity_data_all[i], capacity_data2)]

        # Pair the two price values
        price_data_all.append([f1, f2])

    # Determine the price differences for each capacity value
    price_data_diff = [
        abs(price_data_all[i][0] - price_data_all[i][1])
        for i in range(len(price_data_all))
    ]

    # Determine the maximum price difference
    max_diff = max(price_data_diff)

    # Plot the two supply curves overlaid
    if plot:
        plt = _check_import("matplotlib.pyplot")
        plt.figure(figsize=[20, 10])
        plt.plot(capacity_data1, price_data1)
        plt.plot(capacity_data2, price_data2)
        if None in {area, gen_type}:
            plt.title("Supply Curve Comparison", fontsize=20)
        else:
            plt.title(
                f"Supply curve comparison for {gen_type} generators in {area}",
                fontsize=20,
            )
        plt.xlabel("Capacity (MW)", fontsize=20)
        plt.ylabel("Price ($/MW)", fontsize=20)
        plt.xticks(fontsize=20)
        plt.yticks(fontsize=20)
        plt.show()

    # Return the maximum price difference (this corresponds to the K-S statistic)
    return max_diff


def plot_linear_vs_quadratic_terms(
    grid,
    area,
    gen_type,
    area_type=None,
    plot=True,
    zoom=False,
    num_sd=3,
    alpha=0.1,
):
    """Compares the linear (c1) and quadratic (c2) parameters from the quadratic
    generator cost curves.

    :param powersimdata.input.grid.Grid grid: Grid object.
    :param str area: Either the load zone, state name, state abbreviation, or
        interconnect.
    :param str gen_type: Generation type.
    :param str area_type: one of: *'loadzone'*, *'state'*, *'state_abbr'*,
        *'interconnect'*. Defaults to None, which allows
        :func:`powersimdata.network.model.area_to_loadzone` to infer the type.
    :param bool plot: If True, the linear term vs. quadratic term plot is shown. If
        False, the plot is not shown.
    :param bool zoom: If True, filters out quadratic term outliers to enable better
        visualization. If False, there is no filtering.
    :param float/int num_sd: The number of standard deviations used to filter out
        quadratic term outliers.
    :param float alpha: The alpha blending value for the scatter plot; takes values
        between 0 (transparent) and 1 (opaque).
    :return: (*None*) -- The linear term vs. quadratic term plot is displayed according
        to the user.
    :raises TypeError: if a powersimdata.input.grid.Grid object is not input.
    :raises ValueError: if the specified area or generator type is not applicable.
    """

    plt = _check_import("matplotlib.pyplot")

    # Check that a Grid object is input
    if not isinstance(grid, Grid):
        raise TypeError("A Grid object must be input.")

    # Obtain a copy of the Grid object
    grid = copy.deepcopy(grid)

    # Access the generator cost and plant information data
    gencost_df = grid.gencost["before"]
    plant_df = grid.plant

    # Create a new DataFrame with the desired columns
    supply_data = pd.concat(
        [
            plant_df[["type", "interconnect", "zone_name", "Pmin", "Pmax"]],
            gencost_df[
                gencost_df.columns.difference(
                    ["type", "startup", "shutdown", "n", "interconnect"], sort=False
                )
            ],
        ],
        axis=1,
    )

    # Check to make sure the generator type is valid
    if gen_type not in supply_data["type"].unique():
        raise ValueError(f"{gen_type} is not a valid generation type.")

    # Identify the load zones that correspond to the specified area and area_type
    returned_zones = area_to_loadzone(grid.grid_model, area, area_type)

    # Trim the DataFrame to only be of the desired area and generation type
    supply_data = supply_data.loc[supply_data.zone_name.isin(returned_zones)]
    supply_data = supply_data.loc[supply_data["type"] == gen_type]

    # Remove generators that have no capacity (e.g., Maine coal generators)
    supply_data = supply_data[supply_data["Pmin"] != supply_data["Pmax"]]

    # Check if the area contains generators of the specified type
    if supply_data.empty:
        return

    # Filters out large c2 outlier values so the overall trend can be better visualized
    zoom_name = ""
    if zoom:
        # Drop values outside a specified number of standard deviations of c2
        quad_term_sd = np.std(supply_data["c2"])
        quad_term_mean = np.mean(supply_data["c2"])
        cutoff = quad_term_mean + num_sd * quad_term_sd
        if len(supply_data[supply_data["c2"] > cutoff]) > 0:
            zoom = True
            supply_data = supply_data[supply_data["c2"] <= cutoff]
            max_ylim = np.max(supply_data["c2"] + 0.01)
            min_ylim = np.min(supply_data["c2"] - 0.01)
            max_xlim = np.max(supply_data["c1"] + 1)
            min_xlim = np.min(supply_data["c1"] - 1)
            zoom_name = "(zoomed)"
        else:
            zoom = False

    # Plot the c1 vs. c2 comparison
    if plot:
        fig, ax = plt.subplots()
        fig.set_size_inches(20, 10)
        plt.scatter(
            supply_data["c1"],
            supply_data["c2"],
            s=np.sqrt(supply_data["Pmax"]) * 10,
            alpha=alpha,
            c=supply_data["Pmax"],
            cmap="plasma",
        )
        plt.grid()
        plt.title(
            f"Linear term vs. Quadratic term for {gen_type} generator cost curves in "
            + f"{area} {zoom_name}",
            fontsize=20,
        )
        if zoom:
            plt.ylim([min_ylim, max_ylim])
            plt.xlim([min_xlim, max_xlim])
        plt.xlabel("Linear Term", fontsize=20)
        plt.ylabel("Quadratic Term", fontsize=20)
        plt.xticks(fontsize=20)
        plt.yticks(fontsize=20)
        cbar = plt.colorbar()
        cbar.set_label("Capacity (MW)", fontsize=20)
        cbar.ax.tick_params(labelsize=20)
        plt.show()


def plot_capacity_vs_price(
    grid, num_segments, area, gen_type, area_type=None, plot=True
):
    """Plots the generator capacity vs. the generator price for a specified area
        and generation type.

    :param powersimdata.input.grid.Grid grid: Grid object.
    :param int num_segments: The number of segments into which the piecewise linear
        cost curve is split.
    :param str area: Either the load zone, state name, state abbreviation, or
        interconnect.
    :param str gen_type: Generation type.
    :param str area_type: one of: *'loadzone'*, *'state'*, *'state_abbr'*,
        *'interconnect'*. Defaults to None, which allows
        :func:`powersimdata.network.model.area_to_loadzone` to infer the type.
    :param bool plot: If True, the supply curve plot is shown. If False, the plot is
        not shown.
    :return: (*None*) -- The capacity vs. price plot is displayed according to the user.
    :raises TypeError: if a powersimdata.input.grid.Grid object is not input.
    :raises ValueError: if the specified area or generator type is not applicable.
    """

    plt = _check_import("matplotlib.pyplot")

    # Check that a Grid object is input
    if not isinstance(grid, Grid):
        raise TypeError("A Grid object must be input.")

    # Check that the desired number of linearized cost curve segments is an int
    if not isinstance(num_segments, int):
        raise TypeError(
            "The number of linearized cost curve segments must be input as an int."
        )

    # Obtain the desired generator cost and plant information data
    supply_data = get_supply_data(grid, num_segments)

    # Check the input supply data
    check_supply_data(supply_data, num_segments)

    # Check to make sure the generator type is valid
    if gen_type not in supply_data["type"].unique():
        raise ValueError(f"{gen_type} is not a valid generation type.")

    # Identify the load zones that correspond to the specified area and area_type
    returned_zones = area_to_loadzone(grid.grid_model, area, area_type)

    # Trim the DataFrame to only be of the desired area and generation type
    supply_data = supply_data.loc[supply_data.zone_name.isin(returned_zones)]
    supply_data = supply_data.loc[supply_data["type"] == gen_type]

    # Remove generators that have no capacity (e.g., Maine coal generators)
    if supply_data["slope1"].isnull().values.any():
        supply_data.dropna(subset=["slope1"], inplace=True)

    # Check if the area contains generators of the specified type
    if supply_data.empty:
        return

    # Combine the p_diff and slope information for each cost segment
    supply_df_cols = []
    for i in range(num_segments):
        supply_df_cols.append(
            supply_data.loc[:, ("p_diff" + str(i + 1), "slope" + str(i + 1))]
        )
        supply_df_cols[i].rename(
            columns={"p_diff" + str(i + 1): "p_diff", "slope" + str(i + 1): "slope"},
            inplace=True,
        )
    supply_df = pd.concat(supply_df_cols, axis=0)
    supply_df = supply_df.reset_index(drop=True)

    # Determine the average price
    total_capacity = supply_df["p_diff"].sum()
    if total_capacity == 0:
        average_price = 0
    else:
        average_price = (
            supply_df["slope"] * supply_df["p_diff"]
        ).sum() / total_capacity

    # Plot the comparison
    if plot:
        ax = supply_df.plot.scatter(
            x="p_diff", y="slope", s=50, figsize=[20, 10], grid=True, fontsize=20
        )
        plt.title(
            f"Capacity vs. Price for {gen_type} generators in {area}", fontsize=20
        )
        plt.xlabel("Segment Capacity (MW)", fontsize=20)
        plt.ylabel("Segment Price ($/MW)", fontsize=20)
        ax.plot(supply_df["p_diff"], [average_price] * len(supply_df.index), c="red")
        plt.show()
