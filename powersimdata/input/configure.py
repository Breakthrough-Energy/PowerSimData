import numpy as np
import pandas as pd


def adjust_pmin(grid):
    """Adjust plant Pmin values inplace

    :param powersimdata.input.grid.Grid grid: a grid object
    """
    mi = grid.model_immutables
    plant = grid.plant
    pmin_factor = mi.plants["pmin_as_share_of_pmax"]

    def _scale(x):
        factor = pmin_factor.get(x.type)
        return x.Pmin if factor is None else factor * x.Pmax

    plant.Pmin = plant.apply(_scale, axis=1)

    # set Pmin to 0 for generators that are off or profile based
    profile_resource = list(mi.plants["profile_resources"])
    plant.loc[plant.type.isin(profile_resource), "Pmin"] = 0
    plant.loc[plant.status == 0, "Pmin"] = 0


def adjust_ramp30(plant):
    """Adjust plant ramp_30 values inplace

    :param pandas.DataDrame plant: a plant dataframe
    """
    plant.ramp_30 = np.inf
    ramp30_points = {
        "coal": {"xs": (200, 1400), "ys": (0.4, 0.15)},
        "dfo": {"xs": (200, 1200), "ys": (0.5, 0.2)},
        "ng": {"xs": (200, 600), "ys": (0.5, 0.2)},
    }
    for fuel, points in ramp30_points.items():
        fuel_idx = plant.loc[plant.type == fuel, "Pmax"]
        slope = (points["ys"][1] - points["ys"][0]) / (
            points["xs"][1] - points["xs"][0]
        )
        intercept = points["ys"][0] - slope * points["xs"][0]
        for idx in fuel_idx.index:
            pmax = fuel_idx.at[idx]
            norm_ramp = pmax * slope + intercept
            if pmax < points["xs"][0]:
                norm_ramp = points["ys"][0]
            if pmax > points["xs"][1]:
                norm_ramp = points["ys"][1]
            plant.loc[idx, "ramp_30"] = norm_ramp * pmax


def linearize_gencost(gencost_before, plant, num_segments=1):
    """Updates the generator cost information to include piecewise linear cost curve
    information. Allows the user to specify the number of piecewise segments into which
    the cost curve should be split.

    :param pandas.DataFrame gencost_before: the original gencost
    :param pandas.DataFrame plant: the generator information containing Pmin/Pmax
    :param int num_segments: The number of segments into which the piecewise linear
        cost curve will be split.
    :return: (*pandas.DataFrame*) -- An updated DataFrame containing the piecewise
        linear cost curve parameters.
    :raises ValueError: if the generator cost curve is not of an acceptable form.
    """
    # Raise errors if the provided cost curves are not in a form that can be handled
    if len(gencost_before[gencost_before.type != 2]):
        raise ValueError("gencost currently limited to polynomial")
    if len(gencost_before[gencost_before.n != 3]):
        raise ValueError("gencost currently limited to quadratic")

    gencost_before = gencost_before.copy()
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
        gencost_after = gencost_before.copy()

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

    if "interconnect" in gencost_before.columns:
        gencost_after["interconnect"] = gencost_before["interconnect"]

    return gencost_after.fillna(0)
