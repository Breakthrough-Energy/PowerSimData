import copy

from powersimdata.input.transform_grid import TransformGrid
from powersimdata.utility.distance import find_closest_neighbor

_profile_resource = {"hydro", "solar", "wind", "wind_offshore"}


def add_plant(obj, info):
    """Sets parameters of new generator(s) in change table.

    :param powersimdata.input.change_table.ChangeTable obj: change table
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
        if plant["type"] in _profile_resource:
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


def scale_plant_pmin(obj, resource, zone_name=None, plant_id=None):
    """Sets plant cost scaling factor in change table.

    :param powersimdata.input.change_table.ChangeTable obj: change table
    :param str resource: type of generator to consider.
    :param dict zone_name: load zones. The key(s) is (are) the name of the
        load zone(s) and the associated value is the scaling factor for the
        minimum generation for all generators fueled by
        specified resource in the load zone.
    :param dict plant_id: identification numbers of plants. The key(s) is
        (are) the id of the plant(s) and the associated value is the
        scaling factor for the minimum generation of the generator.
    """
    obj._add_plant_entries(resource, f"{resource}_pmin", zone_name, plant_id)
    # Check for situations where Pmin would be scaled above Pmax
    candidate_grid = TransformGrid(obj.grid, obj.ct).get_grid()
    pmax_pmin_ratio = candidate_grid.plant.Pmax / candidate_grid.plant.Pmin
    to_be_clipped = pmax_pmin_ratio < 1
    num_clipped = to_be_clipped.sum()
    if num_clipped > 0:
        err_msg = (
            f"{num_clipped} plants would have Pmin > Pmax; "
            "these plants will have Pmin scaling clipped so that Pmin = Pmax"
        )
        print(err_msg)
        # Add by-plant correction factors as necessary
        for plant_id, correction in pmax_pmin_ratio[to_be_clipped].items():
            if "plant_id" not in obj.ct[f"{resource}_pmin"]:
                obj.ct[f"{resource}_pmin"]["plant_id"] = {}
            if plant_id in obj.ct[f"{resource}_pmin"]["plant_id"]:
                obj.ct[f"{resource}_pmin"]["plant_id"][plant_id] *= correction
            else:
                obj.ct[f"{resource}_pmin"]["plant_id"][plant_id] = correction


def remove_plant(obj, info):
    """Remove one or more plants.

    :param powersimdata.input.change_table.ChangeTable obj: change table
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
