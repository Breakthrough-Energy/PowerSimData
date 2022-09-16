import numpy as np
import pandas as pd
import pypsa


def get_pypsa_gen_profile(network, profile2carrier):
    """Return hydro, solar or wind profile enclosed in a PyPSA network.

    :param pypsa.Network network: the Network object.
    :param dict profile2carrier: a dictionary mapping profile type to carrier type.
        *'hydro'*, *'solar'* and *'wind'* are valid keys. Values is a corresponding
        set of carriers as found in the Network object.
    :return: (*dict*) -- keys are the same ones than in ``profile2carrier``. Values
        are profiles as data frame.
    :raises TypeError:
        if ``network`` is not a pypsa.components.Network object.
        if ``profile2carrier`` is not a dict.
        if values of ``profile2carrier`` are not an iterable.
    :raises ValueError:
        if keys of ``profile2carrier`` are invalid.
    """
    if not isinstance(network, pypsa.components.Network):
        raise TypeError("network must be a Network object")
    if not isinstance(profile2carrier, dict):
        raise TypeError("profile2carrier must be a dict")
    if not all(isinstance(v, (list, set, tuple)) for v in profile2carrier.values()):
        raise TypeError("values of profile2carrier must be an iterable")
    if not set(profile2carrier).issubset({"hydro", "solar", "wind"}):
        raise ValueError(
            "keys of profile2carrier must be a subset of ['hydro', 'solar', 'wind']"
        )

    profile = {}
    for p, c in profile2carrier.items():
        profile[p] = pd.DataFrame()
        for component in ["generators", "storage_units", "stores"]:
            if hasattr(network, component):
                carrier_in_component = getattr(network, component)
                id_carrier = set(carrier_in_component.query("carrier==list(@c)").index)
                for t in ["inflow", "p_max_pu"]:
                    if t in getattr(network, component + "_t"):
                        ts = getattr(network, component + "_t")[t]
                        if not ts.empty:
                            id_ts = set(ts.columns)
                            idx = list(id_carrier.intersection(id_ts))
                            norm = (
                                (
                                    ts[idx]
                                    .max()
                                    .combine(
                                        carrier_in_component.loc[idx, "p_nom"],
                                        np.maximum,
                                    )
                                )
                                if t == "inflow"
                                else 1
                            )
                            profile[p] = pd.concat([profile[p], ts[idx] / norm], axis=1)
                if len(set(c) - set(carrier_in_component.carrier.unique())):
                    continue
                else:
                    break
        profile[p].rename_axis(index="UTC", columns=None, inplace=True)

    return profile


def get_pypsa_demand_profile(network):
    """Return demand profile enclosed in a PyPSA network.

    :param pypsa.Network network: the Network object.
    :return: (*pandas.DataFrame*) -- demand profile.
    :raises TypeError:
        if ``network`` is not a pypsa.components.Network object.
    """
    if not isinstance(network, pypsa.components.Network):
        raise TypeError("network must be a Network object")

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
    demand.rename_axis(index="UTC", columns=None, inplace=True)

    return demand
