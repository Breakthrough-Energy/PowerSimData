import pandas as pd
from pypsa.descriptors import get_switchable_as_dense


def get_pypsa_gen_profile(network, kind):
    """Return hydro, solar or wind profile enclosed in a PyPSA network.

    :param pypsa.Network network: the Network object.
    :param str kind: either *'hydro'*, *'solar'*, *'wind'*.
    :return: (*pandas.DataFrame*) -- profile.
    """
    p_max_pu = get_switchable_as_dense(network, "Generator", "p_max_pu")
    p_max_pu.columns = pd.to_numeric(p_max_pu.columns, errors="ignore")
    p_max_pu.columns.name = None
    p_max_pu.index.name = "UTC"

    all_gen = network.generators.copy()
    all_gen.index = pd.to_numeric(all_gen.index, errors="ignore")
    all_gen.index.name = None

    gen = all_gen.query("@kind in carrier").index
    return p_max_pu[gen] * all_gen.p_nom[gen]


def get_pypsa_demand_profile(network):
    """Return demand profile enclosed in a PyPSA network.

    :param pypsa.Network network: the Network object.
    :return: (*pandas.DataFrame*) -- profile.
    """
    if not network.loads_t.p.empty:
        demand = network.loads_t.p.copy()
    else:
        demand = network.loads_t.p_set.copy()
    if "zone_id" in network.buses:
        # Assume this is a PyPSA network originally created from powersimdata
        demand = demand.groupby(
            network.buses.zone_id.dropna().astype(int), axis=1
        ).sum()
    demand.columns = pd.to_numeric(demand.columns, errors="ignore")
    demand.columns.name = None
    demand.index.name = "UTC"

    return demand
