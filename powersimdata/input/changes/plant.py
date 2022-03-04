import copy

from powersimdata.utility.distance import find_closest_neighbor

_renewable_resource = {"hydro", "solar", "wind", "wind_offshore"}


def add_plant(obj, info):
    """Sets parameters of new generator(s) in change table.

    :param list info: each entry is a dictionary. The dictionary gathers
        the information needed to create a new generator.
        Required keys: "bus_id", "Pmax", "type".
        Optional keys: "c0", "c1", "c2", "Pmin".
        "c0", "c1", and "c2" are the coefficients for the cost curve, representing
        the fixed cost ($/hour), linear cost ($/MWh), and quadratic cost ($/MW^2·h).
        These are optional for hydro, solar, and wind, and required for other types.
    :raises TypeError: if ``info`` is not a list.
    :raises ValueError: if any of the new plants to be added have bad values.
    """
    if not isinstance(info, list):
        raise TypeError("Argument enclosing new plant(s) must be a list")

    info = copy.deepcopy(info)
    anticipated_bus = obj._get_transformed_df("bus")
    new_plants = []
    required = {"bus_id", "Pmax", "type"}
    optional = {"c0", "c1", "c2", "Pmin"}
    for i, plant in enumerate(info):
        obj._check_entry_keys(plant, i, "plant", required, None, optional)
        obj._check_resource(plant["type"])
        if plant["bus_id"] not in anticipated_bus.index:
            raise ValueError(
                f"No bus id {plant['bus_id']} available for plant #{i + 1}"
            )
        if plant["Pmax"] < 0:
            raise ValueError(f"Pmax >= 0 must be satisfied for plant #{i + 1}")
        if "Pmin" not in plant.keys():
            plant["Pmin"] = 0
        if plant["Pmin"] < 0 or plant["Pmin"] > plant["Pmax"]:
            err_msg = f"0 <= Pmin <= Pmax must be satisfied for plant #{i + 1}"
            raise ValueError(err_msg)
        if plant["type"] in _renewable_resource:
            lon = anticipated_bus.loc[plant["bus_id"]].lon
            lat = anticipated_bus.loc[plant["bus_id"]].lat
            plant_same_type = obj.grid.plant.groupby("type").get_group(plant["type"])
            neighbor_id = find_closest_neighbor(
                (lon, lat), plant_same_type[["lon", "lat"]].values
            )
            plant["plant_id_neighbor"] = plant_same_type.iloc[neighbor_id].name
        else:
            for c in ["0", "1", "2"]:
                if "c" + c not in plant.keys():
                    raise ValueError(f"Missing key c{c} for plant #{i + 1}")
                elif plant["c" + c] < 0:
                    err_msg = f"c{c} >= 0 must be satisfied for plant #{i + 1}"
                    raise ValueError(err_msg)
        new_plants.append(plant)

    if "new_plant" not in obj.ct:
        obj.ct["new_plant"] = []
    obj.ct["new_plant"] += new_plants


def remove_plant(obj, info):
    """Remove one or more plants.

    :param int/iterable info: iterable of plant indices, or a single plant index.
    :raises ValueError: if ``info`` contains one or more entries not present in the
        plant table index.
    """
    if isinstance(info, int):
        info = {info}
    diff = set(info) - set(obj._get_transformed_df("plant").index)
    if len(diff) != 0:
        raise ValueError(f"No plant with the following id(s): {sorted(diff)}")
    if "remove_plant" not in obj.ct:
        obj.ct["remove_plant"] = set()
    obj.ct["remove_plant"] |= set(info)
