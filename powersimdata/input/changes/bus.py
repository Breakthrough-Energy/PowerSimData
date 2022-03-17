import copy


def add_bus(obj, info):
    """Sets parameters of new bus(es) in change table.

    :param powersimdata.input.change_table.ChangeTable obj: change table
    :param list info: each entry is a dictionary. The dictionary gathers
        the information needed to create a new bus.
        Required keys: "lat", "lon", ["zone_id" XOR "zone_name"].
        Optional key: "Pd", "baseKV".
    :raises TypeError: if ``info`` is not a list.
    :raises ValueError: if any new bus doesn't have appropriate keys/values.
    """
    if not isinstance(info, list):
        raise TypeError("Argument enclosing new bus(es) must be a list")

    info = copy.deepcopy(info)
    new_buses = []
    required = {"lat", "lon"}
    xor_sets = {("zone_id", "zone_name")}
    defaults = {"Pd": 0, "baseKV": 230}
    for i, new_bus in enumerate(info):
        obj._check_entry_keys(
            new_bus, i, "new_bus", required, xor_sets, defaults.keys()
        )
        for l in {"lat", "lon"}:
            if not isinstance(new_bus[l], (int, float)):
                raise ValueError(f"{l} must be numeric (int/float)")
        if abs(new_bus["lat"]) > 90:
            raise ValueError("'lat' must be between -90 and +90")
        if abs(new_bus["lon"]) > 180:
            raise ValueError("'lon' must be between -180 and +180")
        if "zone_id" in new_bus and new_bus["zone_id"] not in obj.grid.id2zone:
            zone_id = new_bus["zone_id"]
            raise ValueError(f"zone_id {zone_id} not present in Grid")
        if "zone_name" in new_bus:
            try:
                new_bus["zone_id"] = obj.grid.zone2id[new_bus["zone_name"]]
            except KeyError:
                zone_name = new_bus["zone_name"]
                raise ValueError(f"zone_name {zone_name} not present in Grid")
            del new_bus["zone_name"]
        if "Pd" in new_bus:
            if not isinstance(new_bus["Pd"], (int, float)):
                raise ValueError("Pd must be numeric (int/float)")
        else:
            new_bus["Pd"] = defaults["Pd"]
        if "baseKV" in new_bus:
            if not isinstance(new_bus["baseKV"], (int, float)):
                raise ValueError("baseKV must be numeric (int/float)")
            if new_bus["baseKV"] <= 0:
                raise ValueError("baseKV must be positive")
        else:
            new_bus["baseKV"] = defaults["baseKV"]
        new_buses.append(new_bus)
    if "new_bus" not in obj.ct:
        obj.ct["new_bus"] = []
    obj.ct["new_bus"] += new_buses


def remove_bus(obj, info):
    """Remove one or more buses.

    :param powersimdata.input.change_table.ChangeTable obj: change table
    :param int/iterable info: iterable of bus indices, or a single bus index.
    :raises ValueError: if ``info`` contains one or more entries not present in the
        bus table index.
    """
    if isinstance(info, int):
        info = {info}
    # Check whether all buses to be removed are present in the grid
    diff = set(info) - set(obj._get_transformed_df("bus").index)
    if len(diff) != 0:
        raise ValueError(f"No bus with the following id(s): {sorted(diff)}")
    # Check whether there exist any plants with non-zero capacity at these buses
    anticipated_plant = obj._get_transformed_df("plant").query("Pmax > 0")
    plants_at_removal_buses = set(info) & set(anticipated_plant.bus_id)
    if len(plants_at_removal_buses) > 0:
        raise ValueError(
            f"Generators exist at bus id(s): {sorted(plants_at_removal_buses)}"
        )
    # Check whether storage exists at these buses
    anticipated_storage = obj._get_transformed_df("storage_gen")
    storage_at_removal_buses = set(info) & set(anticipated_storage.bus_id)
    if len(storage_at_removal_buses) > 0:
        raise ValueError(
            f"Storage units exist at bus id(s): {sorted(storage_at_removal_buses)}"
        )
    # Check whether there exist branches or DC lines at these buses
    for table in ("branch", "dcline"):
        anticipated = obj._get_transformed_df(table)
        overlap = anticipated.query("from_bus_id in @info or to_bus_id in @info")
        if len(overlap) > 0:
            raise ValueError(
                f"These {table} IDs connect to a bus to be removed: {overlap.index}"
            )
    # All checks have passed, and we can add this to the change table
    if "remove_bus" not in obj.ct:
        obj.ct["remove_bus"] = set()
    obj.ct["remove_bus"] |= set(info)
