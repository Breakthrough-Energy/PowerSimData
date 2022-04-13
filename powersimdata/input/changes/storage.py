import copy

from powersimdata.input.changes import ordinal


def add_storage_capacity(obj, info):
    """Sets storage parameters in change table.

    :param powersimdata.input.change_table.ChangeTable obj: change table
    :param list info: each entry is a dictionary. The dictionary gathers
        the information needed to create a new storage device.
        Required keys: "bus_id", "capacity".
        "capacity" denotes the symmetric input and output power limits (MW).
        Optional keys: "duration", "min_stor", "max_stor", "energy_value", "InEff",
        "OutEff", "LossFactor", "terminal_min", "terminal_max".
        "duration" denotes the energy to power ratio (hours).
        "min_stor" denotes the minimum energy limit (unitless), e.g. 0.05 = 5%.
        "max_stor" denotes the maximum energy limit (unitless), e.g. 0.95 = 95%.
        "energy_value" denotes the value of stored energy at interval end ($/MWh).
        "InEff" denotes the input efficiency (unitless), e.g. 0.95 = 95%.
        "OutEff" denotes the output efficiency (unitless), e.g. 0.95 = 95%.
        "LossFactor" denotes the per-hour relative losses,
        e.g. 0.01 means that 1% of the current state of charge is lost per hour).
        "terminal_min" denotes the minimum state of charge at interval end,
        e.g. 0.5 means that the storage must end the interval with at least 50%.
        "terminal_max" denotes the maximum state of charge at interval end,
        e.g. 0.9 means that the storage must end the interval with no more than 90%.
    :raises TypeError: if ``info`` is not a list.
    :raises ValueError: if any of the new storages to be added have bad values.
    """
    if not isinstance(info, list):
        raise TypeError("Argument enclosing new storage(s) must be a list")

    info = copy.deepcopy(info)
    new_storages = []
    required = {"bus_id", "capacity"}
    optional = {
        "duration",
        "min_stor",
        "max_stor",
        "energy_value",
        "InEff",
        "OutEff",
        "LossFactor",
        "terminal_min",
        "terminal_max",
    }
    anticipated_bus = obj._get_transformed_df("bus")
    for i, storage in enumerate(info):
        obj._check_entry_keys(storage, i, "storage", required, None, optional)
        if storage["bus_id"] not in anticipated_bus.index:
            raise ValueError(
                f"No bus id {storage['bus_id']} available for {ordinal(i)} storage"
            )
        for o in optional:
            if o not in storage:
                storage[o] = obj.grid.storage[o]
        for k, v in storage.items():
            if not isinstance(v, (int, float)):
                err_msg = f"values must be numeric, bad type for {ordinal(i)} {k}"
                raise ValueError(err_msg)
            if v < 0:
                raise ValueError(
                    f"values must be non-negative, bad value for {ordinal(i)} {k}"
                )
        for k in {"min_stor", "max_stor", "InEff", "OutEff", "LossFactor"}:
            if storage[k] > 1:
                raise ValueError(
                    f"value for {k} must be <=1, bad value for {ordinal(i)} storage"
                )
        new_storages.append(storage)
    if "storage" not in obj.ct:
        obj.ct["storage"] = []
    obj.ct["storage"] += new_storages
