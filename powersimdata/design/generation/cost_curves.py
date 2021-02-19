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
    old_a = gencost_before.c2
    old_b = gencost_before.c1
    old_c = gencost_before.c0

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
            x_label = "p" + str(i + 1)
            y_label = "f" + str(i + 1)
            x_data = plant.Pmin + power_step * i
            y_data = old_a * x_data ** 2 + old_b * x_data + old_c
            gencost_after.loc[dispatchable_gens, x_label] = x_data[dispatchable_gens]
            gencost_after.loc[dispatchable_gens, y_label] = y_data[dispatchable_gens]
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
        y_data = old_a * power ** 2 + old_b * power + old_c
        gencost_after.loc[nondispatchable_gens, ["c2", "c1"]] = 0
        gencost_after.loc[nondispatchable_gens, "c0"] = y_data[nondispatchable_gens]

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


def check_supply_data(data, num_segments=1):
    """Checks to make sure that the input supply data is a DataFrame and has the
    correct columns. This is especially needed for checking instances where the input
    supply data is not the DataFrame returned from get_supply_data().

    :param pandas.DataFrame data: DataFrame containing the supply curve information.
    :param int num_segments: The number of segments into which the piecewise linear
        cost curve will be split.
    :raises TypeError: if the input supply data is not a pandas.DataFrame.
    :raises ValueError: if one of the mandatory columns is missing from the input
        supply data.
    """

    # Check that the data is input as a DataFrame
    if not isinstance(data, pd.DataFrame):
        raise TypeError("Supply data must be input as a DataFrame.")

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
    miss_cols = mand_cols - set(data.columns)
    if len(miss_cols) > 0:
        raise ValueError(f'Missing columns: {", ".join(miss_cols)}')


def build_supply_curve(grid, num_segments, area, gen_type, area_type=None, plot=True):
    """Builds a supply curve for a specified area and generation type.

    :param powersimdata.input.grid.Grid grid: Grid object.
    :param int num_segments: The number of segments into which the piecewise linear
        cost curve is split.
    :param str area: Either the load zone, state name, state abbreviation, or
        interconnect.
    :param str gen_type: Generation type.
    :param str area_type: one of: *'loadzone'*, *'state'*, *'state_abbr'*,
        *'interconnect'*. Defaults to None, which allows area_to_loadzone() to infer
        the type.
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

    # Obtain the desired generator cost and plant information data
    data = get_supply_data(grid, num_segments)

    # Check the input supply data
    check_supply_data(data, num_segments)

    # Check to make sure the generator type is valid
    if gen_type not in data["type"].unique():
        raise ValueError(f"{gen_type} is not a valid generation type.")

    # Identify the load zones that correspond to the specified area and area_type
    returned_zones = area_to_loadzone(grid.get_grid_model(), area, area_type)

    # Trim the DataFrame to only be of the desired area and generation type
    data = data.loc[data.zone_name.isin(returned_zones)]
    data = data.loc[data["type"] == gen_type]

    # Remove generators that have no capacity (e.g., Maine coal generators)
    if data["slope1"].isnull().values.any():
        data.dropna(subset=["slope1"], inplace=True)

    # Check if the area contains generators of the specified type
    if data.empty:
        return [], []

    # Combine the p_diff and slope information for each cost segment
    df_cols = []
    for i in range(num_segments):
        df_cols.append(data.loc[:, ("p_diff" + str(i + 1), "slope" + str(i + 1))])
        df_cols[i].rename(
            columns={"p_diff" + str(i + 1): "p_diff", "slope" + str(i + 1): "slope"},
            inplace=True,
        )
    df = pd.concat(df_cols, axis=0)

    # Sort the trimmed DataFrame by slope
    df = df.sort_values(by="slope")
    df = df.reset_index(drop=True)

    # Determine the points that comprise the supply curve
    P = []
    F = []
    p_diff_sum = 0
    for i in df.index:
        P.append(p_diff_sum)
        F.append(df["slope"][i])
        P.append(df["p_diff"][i] + p_diff_sum)
        F.append(df["slope"][i])
        p_diff_sum += df["p_diff"][i]

    # Plot the curve
    if plot:
        plt = _check_import("matplotlib.pyplot")
        plt.figure(figsize=[20, 10])
        plt.plot(P, F)
        plt.title(f"Supply curve for {gen_type} generators in {area}", fontsize=20)
        plt.xlabel("Capacity (MW)", fontsize=20)
        plt.ylabel("Price ($/MW)", fontsize=20)
        plt.xticks(fontsize=20)
        plt.yticks(fontsize=20)
        plt.show()

    # Return the capacity and bid amounts
    return P, F


def lower_bound_index(x, l):
    """Determines the index of the lower capacity value that defines a price segment.
    Useful for accessing the prices associated with capacity values that aren't
    explicitly stated in the capacity lists that are generated by the
    build_supply_curve() function. Needed for ks_test().

    :param float/int x: Capacity value for which you want to determine the index of the
        lowest capacity value in a price segment.
    :param list l: List of capacity values used to generate a supply curve.
    :return: (*int*) -- Index of a price segment's capacity lower bound.
    """

    # Check that the list is not empty and that the capacity falls within the list range
    if not l or l[0] > x:
        return None

    # Get the index of the value that is immediately less than the provided capacity
    for i, j in enumerate(l):
        if j > x:
            return i - 1


def ks_test(P1, F1, P2, F2, area=None, gen_type=None, plot=True):
    """Runs a test that is similar to the Kolmogorov-Smirnov test. This function takes
    two supply curves as inputs and returns the greatest difference in price between
    the two supply curves. This function requires that the supply curves offer the same
    amount of capacity.

    :param list P1: List of capacity values for the first supply curve.
    :param list F1: List of price values for the first supply curve.
    :param list P2: List of capacity values for the second supply curve.
    :param list F2: List of price values for the second supply curve.
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
    if not all(isinstance(i, list) for i in [P1, F1, P2, F2]):
        raise TypeError("P1, F1, P2, and F2 must be input as lists.")

    # Check that the supply curves offer the same amount of capacity
    if max(P1) != max(P2):
        raise ValueError(
            "The two supply curves do not offer the same amount of capacity (MW)."
        )

    # Create a list that has every capacity value in which either supply curve steps up
    P_all = list(set(P1) | set(P2))
    P_all.sort()

    # For each capacity value, associate the two corresponding price values
    F_all = []
    for i in range(len(P_all)):
        # Determine the correpsonding price from the first supply curve
        if P_all[i] == P1[-1]:
            f1 = F1[-1]
        else:
            f1 = F1[lower_bound_index(P_all[i], P1)]

        # Determine the correpsonding price from the second supply curve
        if P_all[i] == P2[-1]:
            f2 = F2[-1]
        else:
            f2 = F2[lower_bound_index(P_all[i], P2)]

        # Pair the two price values
        F_all.append([f1, f2])

    # Determine the price differences for each capacity value
    F_diff = [abs(F_all[i][0] - F_all[i][1]) for i in range(len(F_all))]

    # Determine the maximum price difference
    max_diff = max(F_diff)

    # Plot the two supply curves overlaid
    if plot:
        plt = _check_import("matplotlib.pyplot")
        plt.figure(figsize=[20, 10])
        plt.plot(P1, F1)
        plt.plot(P2, F2)
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


def plot_c1_vs_c2(
    grid,
    area,
    gen_type,
    area_type=None,
    plot=True,
    zoom=False,
    num_sd=3,
    alpha=0.1,
):
    """Compares the c1 and c2 parameters from the quadratic generator cost curves.

    :param powersimdata.input.grid.Grid grid: Grid object.
    :param str area: Either the load zone, state name, state abbreviation, or
        interconnect.
    :param str gen_type: Generation type.
    :param str area_type: one of: *'loadzone'*, *'state'*, *'state_abbr'*,
        *'interconnect'*. Defaults to None, which allows area_to_loadzone() to infer
        the type.
    :param bool plot: If True, the c1 vs. c2 plot is shown. If False, the plot is not
        shown.
    :param bool zoom: If True, filters out c2 outliers to enable better visualization.
        If False, there is no filtering.
    :param float/int num_sd: The number of standard deviations used to filter out c2
        outliers.
    :param float alpha: The alpha blending value for the scatter plot; takes values
        between 0 (transparent) and 1 (opaque).
    :return: (*None*) -- The c1 vs. c2 plot is displayed according to the user.
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
    data = pd.concat(
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
    if gen_type not in data["type"].unique():
        raise ValueError(f"{gen_type} is not a valid generation type.")

    # Identify the load zones that correspond to the specified area and area_type
    returned_zones = area_to_loadzone(area, area_type)

    # Trim the DataFrame to only be of the desired area and generation type
    data = data.loc[data.zone_name.isin(returned_zones)]
    data = data.loc[data["type"] == gen_type]

    # Remove generators that have no capacity (e.g., Maine coal generators)
    data = data[data["Pmin"] != data["Pmax"]]

    # Check if the area contains generators of the specified type
    if data.empty:
        return

    # Filters out large c2 outlier values so the overall trend can be better visualized
    zoom_name = ""
    if zoom:
        # Drop values outside a specified number of standard deviations of c2
        sd_c2 = np.std(data["c2"])
        mean_c2 = np.mean(data["c2"])
        cutoff = mean_c2 + num_sd * sd_c2
        if len(data[data["c2"] > cutoff]) > 0:
            zoom = True
            data = data[data["c2"] <= cutoff]
            max_ylim = np.max(data["c2"] + 0.01)
            min_ylim = np.min(data["c2"] - 0.01)
            max_xlim = np.max(data["c1"] + 1)
            min_xlim = np.min(data["c1"] - 1)
            zoom_name = "(zoomed)"
        else:
            zoom = False

    # Plot the c1 vs. c2 comparison
    if plot:
        fig, ax = plt.subplots()
        fig.set_size_inches(20, 10)
        plt.scatter(
            data["c1"],
            data["c2"],
            s=np.sqrt(data["Pmax"]) * 10,
            alpha=alpha,
            c=data["Pmax"],
            cmap="plasma",
        )
        plt.grid()
        plt.title(
            f"c1 vs. c2 for {gen_type} generators in {area} {zoom_name}", fontsize=20
        )
        if zoom:
            plt.ylim([min_ylim, max_ylim])
            plt.xlim([min_xlim, max_xlim])
        plt.xlabel("c1", fontsize=20)
        plt.ylabel("c2", fontsize=20)
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
        *'interconnect'*. Defaults to None, which allows area_to_loadzone() to infer
        the type.
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
    data = get_supply_data(grid, num_segments)

    # Check the input supply data
    check_supply_data(data, num_segments)

    # Check to make sure the generator type is valid
    if gen_type not in data["type"].unique():
        raise ValueError(f"{gen_type} is not a valid generation type.")

    # Identify the load zones that correspond to the specified area and area_type
    returned_zones = area_to_loadzone(area, area_type)

    # Trim the DataFrame to only be of the desired area and generation type
    data = data.loc[data.zone_name.isin(returned_zones)]
    data = data.loc[data["type"] == gen_type]

    # Remove generators that have no capacity (e.g., Maine coal generators)
    if data["slope1"].isnull().values.any():
        data.dropna(subset=["slope1"], inplace=True)

    # Check if the area contains generators of the specified type
    if data.empty:
        return

    # Combine the p_diff and slope information for each cost segment
    df_cols = []
    for i in range(num_segments):
        df_cols.append(data.loc[:, ("p_diff" + str(i + 1), "slope" + str(i + 1))])
        df_cols[i].rename(
            columns={"p_diff" + str(i + 1): "p_diff", "slope" + str(i + 1): "slope"},
            inplace=True,
        )
    df = pd.concat(df_cols, axis=0)
    df = df.reset_index(drop=True)

    # Determine the average
    total_cap = df["p_diff"].sum()
    if total_cap == 0:
        data_avg = 0
    else:
        data_avg = (df["slope"] * df["p_diff"]).sum() / total_cap

    # Plot the comparison
    if plot:
        ax = df.plot.scatter(
            x="p_diff", y="slope", s=50, figsize=[20, 10], grid=True, fontsize=20
        )
        plt.title(
            f"Capacity vs. Price for {gen_type} generators in {area}", fontsize=20
        )
        plt.xlabel("Segment Capacity (MW)", fontsize=20)
        plt.ylabel("Segment Price ($/MW)", fontsize=20)
        ax.plot(df["p_diff"], [data_avg] * len(df.index), c="red")
        plt.show()
