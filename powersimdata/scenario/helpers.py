import numpy as np
import pandas as pd


def check_interconnect(interconnect):
    """Sets interconnect.

    :param list interconnect: interconnect name(s).
    :raises TypeError: if parameter has wrong type.
    :raises Exception: if interconnect not found or inappropriate combination.
    """
    possible = ["Eastern", "Texas", "Western", "USA"]
    if not isinstance(interconnect, list):
        raise TypeError("List of string(s) is expected for interconnect")

    for i in interconnect:
        if i not in possible:
            raise Exception("Wrong interconnect. Choose from %s" % " | ".join(possible))
    n = len(interconnect)
    if n > len(set(interconnect)):
        raise Exception("List of interconnects contains duplicate values")
    if "USA" in interconnect and n > 1:
        raise Exception("USA interconnect cannot be paired")


def interconnect2name(interconnect):
    """Converts list of interconnect to string used for naming files.

    :param list interconnect: List of interconnect(s).
    :return: (*str*) -- name to use.
    """
    check_interconnect(interconnect)

    n = len(interconnect)
    if n == 1:
        return interconnect[0].lower()
    elif n == 2:
        if "USA" in interconnect:
            return "usa"
        else:
            if "Western" in interconnect and "Texas" in interconnect:
                return "texaswestern"
            if "Eastern" in interconnect and "Texas" in interconnect:
                return "texaseastern"
            if "Eastern" in interconnect and "Western" in interconnect:
                return "easternwestern"
    else:
        return "usa"


def calculate_bus_demand(bus, demand):
    """Calculates bus-level demand from zone-level demand.

    :param pandas.DataFrame bus: bus data frame.
    :param pandas.DataFrame demand: demand data frame.
    :return: (*pandas.DataFrame*) -- dataframe of (hour, bus) demand.
    """
    zone_demand = bus.groupby("zone_id").sum().Pd
    bus_zone_share = bus.apply(lambda x: x.Pd / zone_demand.loc[x.zone_id], axis=1)
    bus_to_zone = np.zeros((len(zone_demand), len(bus)))
    bus_idx_lookup = {b: i for i, b in enumerate(bus.index)}
    zone_idx_lookup = {z: i for i, z in enumerate(zone_demand.index)}
    for b in bus.index:
        bus_idx = bus_idx_lookup[b]
        zone_idx = zone_idx_lookup[bus.loc[b, "zone_id"]]
        bus_to_zone[zone_idx, bus_idx] = bus_zone_share.loc[b]
    bus_demand = pd.DataFrame(
        (demand.to_numpy() @ bus_to_zone), index=demand.index, columns=bus.index
    )
    return bus_demand
