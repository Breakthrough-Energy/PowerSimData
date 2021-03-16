from powersimdata.network.usa_tamu.constants.zones import id2abv


def classify_interstate_intrastate(scenario):
    """Classifies branches in a change_table as interstate or intrastate.

    :param powersimdata.scenario.scenario.Scenario scenario: scenario instance.
    :return: (*dict*) -- keys are *'interstate'*, *'intrastate'*. Values are
        list of branch ids.
    """

    ct = scenario.state.get_ct()
    grid = scenario.state.get_grid()
    upgraded_branches = _classify_interstate_intrastate(ct, grid)
    return upgraded_branches


def _classify_interstate_intrastate(ct, grid):
    """Classifies branches in a change_table as interstate or intrastate.
    This function is separate from classify_interstate_intrastate() for testing
    purposes.

    :param dict ct: change_table dictionary.
    :param powersimdata.input.grid.Grid grid: Grid instance.
    :return: (*dict*) -- keys are *'interstate'*, *'intrastate'*. Values are
        list of branch ids.
    """

    branch = grid.branch
    upgraded_branches = {"interstate": [], "intrastate": []}

    if "branch" not in ct or "branch_id" not in ct["branch"]:
        return upgraded_branches

    all_upgraded_branches = ct["branch"]["branch_id"].keys()
    for b in all_upgraded_branches:
        # Alternatively: bus.loc[branch.loc[b, 'from_bus_id'], 'from_zone_id']
        try:
            from_zone = branch.loc[b, "from_zone_id"]
            to_zone = branch.loc[b, "to_zone_id"]
        except KeyError:
            raise ValueError(f"ct entry not found in branch: {b}")
        try:
            from_state = id2abv[from_zone]
        except KeyError:
            raise ValueError(f"zone not found in id2abv: {from_zone}")
        try:
            to_state = id2abv[to_zone]
        except KeyError:
            raise ValueError(f"zone not found in id2abv: {to_zone}")
        if from_state == to_state:
            upgraded_branches["intrastate"].append(b)
        else:
            upgraded_branches["interstate"].append(b)

    return upgraded_branches
