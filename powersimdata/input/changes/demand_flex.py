import copy

from powersimdata.input.profile_input import ProfileInput


def add_demand_flexibility(obj, info):
    """Adds demand flexibility to the system.

    :param powersimdata.input.change_table.ChangeTable obj: change table
    :param dict info: Each key refers to a different component required to
        parameterize the demand flexibility model. Each value associated with the
        keys corresponds to the profile version of the profile in question.
        Required keys: "demand_flexibility_up", "demand_flexibility_dn".
        Optional keys: "demand_flexibility_duration", "demand_flexibility_cost_up",
        "demand_flexibility_cost_dn".
    :raises TypeError: if info is not a dict
    :raises ValueError: if duration is not a positive int, or if no profile is found
    """

    # Check inputs
    if not isinstance(info, dict):
        raise TypeError(
            "Argument enclosing new demand flexibility info must be a dictionary."
        )
    info = copy.deepcopy(info)
    required = {"demand_flexibility_up", "demand_flexibility_dn"}
    optional = {
        "demand_flexibility_duration",
        "demand_flexibility_cost_up",
        "demand_flexibility_cost_dn",
    }
    obj._check_entry_keys(info, 0, "demand_flexibility", required, None, optional)

    # Add a key for demand flexibility in the change table, if necessary
    if "demand_flexibility" not in obj.ct:
        obj.ct["demand_flexibility"] = {}

    # Access the specified demand flexibility profiles that are required
    for k in required | (optional & info.keys()):
        if k == "demand_flexibility_duration":
            # Check that demand flexibility duration is an integer and positive
            if not isinstance(info[k], int):
                raise ValueError(f"The value of {k} is not integer-valued.")
            if info[k] <= 0:
                raise ValueError(f"The value of {k} is not positive.")
            obj.ct["demand_flexibility"][k] = info[k]
        else:
            # Determine the available profile versions
            possible = ProfileInput().get_profile_version(obj.grid.grid_model, k)

            # Add the profile to the change table
            if len(possible) == 0:
                del obj.ct["demand_flexibility"]
                raise ValueError(f"No {k} profile available.")
            elif info[k] in possible:
                obj.ct["demand_flexibility"][k] = info[k]
            else:
                del obj.ct["demand_flexibility"]
                raise ValueError(f"Available {k} profiles: {', '.join(possible)}")
