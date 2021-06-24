import sys

import networkx as nx

from powersimdata.input.grid import Grid


def check_grid(grid):
    """Check whether an object is an internally-consistent Grid object.

    :param powersimdata.input.grid.Grid grid: grid or grid-like object to check.
    :raises TypeError: if ``grid`` is not a Grid object.
    :raises ValueError: if ``grid`` has any inconsistency
    """
    if not isinstance(grid, Grid):
        raise TypeError("grid must be a Grid object")
    error_messages = []
    for check in [
        _check_attributes,
        _check_for_islanded_buses,
        _check_for_undescribed_buses,
        _check_bus_against_bus2sub,
        _check_ac_interconnects,
        _check_transformer_substations,
        _check_line_voltages,
        _check_plant_against_gencost,
        _check_connected_components,
    ]:
        try:
            check(grid, error_messages)
        except Exception:
            error_messages.append(
                f"Exception during {check.__name__}: {sys.exc_info()[1]!r}"
            )
    if len(error_messages) > 0:
        collected = "\n".join(error_messages)
        raise ValueError(f"Problem(s) found with grid:\n{collected}")


def _check_attributes(grid, error_messages):
    """Check whether a Grid object has the required attributes.

    :param powersimdata.input.grid.Grid grid: grid or grid-like object to check.
    :param list error_messages: list, to be appended to with a str if:
        ``grid`` is missing one or more required attributes.
    """
    required = {
        "branch",
        "bus",
        "bus2sub",
        "dcline",
        "data_loc",
        "gencost",
        "grid_model",
        "interconnect",
        "model_immutables",
        "plant",
        "storage",
        "sub",
    }
    for r in required:
        if not hasattr(grid, r):
            error_messages.append(f"grid object must have attribute {r}.")


def _check_for_islanded_buses(grid, error_messages):
    """Check whether a transmission network (AC & DC) does not connect to one or more
    buses.

    :param powersimdata.input.grid.Grid grid: grid or grid-like object to check.
    :param list error_messages: list, to be appended to with a str if:
        branches/DC lines exist in the ``grid``, but one or more buses are islanded.
    """
    if len(grid.branch) + len(grid.dcline) > 0:
        connected_buses = set().union(
            set(grid.branch.from_bus_id),
            set(grid.branch.to_bus_id),
            set(grid.dcline.from_bus_id),
            set(grid.dcline.to_bus_id),
        )
        isolated_buses = set(grid.bus.index) - connected_buses
        if len(isolated_buses) > 0:
            error_messages.append(f"islanded buses detected: {isolated_buses}.")


def _check_for_undescribed_buses(grid, error_messages):
    """Check whether any transmission elements are connected to buses that are not
    described in the bus table.

    :param powersimdata.input.grid.Grid grid: grid or grid-like object to check.
    :param list error_messages: list, to be appended to with a str if:
        any transmission elements are connected to buses that are not described in the
        bus table of the ``grid``.
    """
    expected_buses = set().union(
        set(grid.branch.from_bus_id),
        set(grid.branch.to_bus_id),
        set(grid.dcline.from_bus_id),
        set(grid.dcline.to_bus_id),
    )
    undescribed_buses = expected_buses - set(grid.bus.index)
    if len(undescribed_buses) > 0:
        error_messages.append(
            "buses present in transmission network but missing from bus table: "
            f"{undescribed_buses}."
        )


def _check_bus_against_bus2sub(grid, error_messages):
    """Check whether indices of bus and bus2sub tables match.

    :param powersimdata.input.grid.Grid grid: grid or grid-like object to check.
    :param list error_messages: list, to be appended to with a str if:
        indices of bus and bus2sub tables of the ``grid`` don't match.
    """
    if not set(grid.bus.index) == set(grid.bus2sub.index):
        error_messages.append("indices for bus and bus2sub don't match.")


def _check_ac_interconnects(grid, error_messages):
    """Check whether any AC branches bridge across interconnections.

    :param powersimdata.input.grid.Grid grid: grid or grid-like object to check.
    :param list error_messages: list, to be appended to with a str if:
        any AC branches bridge across interconnections of the ``grid``.
    """
    from_interconnect = grid.branch.from_bus_id.map(grid.bus.interconnect)
    to_interconnect = grid.branch.to_bus_id.map(grid.bus.interconnect)
    if not all(from_interconnect == to_interconnect):
        non_matching_ids = grid.branch.index[from_interconnect != to_interconnect]
        error_messages.append(
            "branch(es) connected across multiple interconnections: "
            f"{non_matching_ids}."
        )


def _check_transformer_substations(grid, error_messages):
    """Check whether any transformers are are not within exactly one same substation.

    :param powersimdata.input.grid.Grid grid: grid or grid-like object to check.
    :param list error_messages: list, to be appended to with a str if:
        any transformers in the ``grid`` are not within exactly one same substation.
    """
    txfmr_branch_types = {"Transformer", "TransformerWinding"}
    branch = grid.branch
    transformers = branch.loc[branch.branch_device_type.isin(txfmr_branch_types)]
    from_sub = transformers.from_bus_id.map(grid.bus2sub.sub_id)
    to_sub = transformers.to_bus_id.map(grid.bus2sub.sub_id)
    if not all(from_sub == to_sub):
        non_matching_transformers = transformers.index[from_sub != to_sub]
        error_messages.append(
            "transformer(s) connected across multiple substations: "
            f"{non_matching_transformers}."
        )


def _check_line_voltages(grid, error_messages):
    """Check whether any lines connect across different voltage levels.

    :param powersimdata.input.grid.Grid grid: grid or grid-like object to check.
    :param list error_messages: list, to be appended to with a str if:
        any lines in the ``grid`` connect across different voltage levels.
    """
    lines = grid.branch.query("branch_device_type == 'Line'")
    from_kV = lines.from_bus_id.map(grid.bus.baseKV)  # noqa: N806
    to_kV = lines.to_bus_id.map(grid.bus.baseKV)  # noqa: N806
    if not all(from_kV == to_kV):
        non_matching_lines = lines.index[from_kV != to_kV]
        error_messages.append(
            f"line(s) connected across multiple voltages: {non_matching_lines}."
        )


def _check_plant_against_gencost(grid, error_messages):
    """Check whether indices of plant and gencost tables match.

    :param powersimdata.input.grid.Grid grid: grid or grid-like object to check.
    :param list error_messages: list, to be appended to with a str if:
        indices of plant and gencost tables of the ``grid`` don't match.
    """
    if not (
        set(grid.plant.index)
        == set(grid.gencost["before"].index)
        == set(grid.gencost["after"].index)
    ):
        error_messages.append("indices for plant and gencost don't match.")


def _check_connected_components(grid, error_messages):
    """Check whether connected components and listed interconnects of a grid match.

    :param powersimdata.input.grid.Grid grid: grid or grid-like object to check.
    :param list error_messages: list, to be appended to with a str if:
        connected components and listed interconnects of a ``grid`` don't match.
    """
    g = nx.from_pandas_edgelist(grid.branch, "from_bus_id", "to_bus_id")
    num_connected_components = len([c for c in nx.connected_components(g)])
    if len(grid.interconnect) == 1:
        # Check for e.g. ['USA'] interconnect, which is really three interconnects
        interconnect_aliases = grid.model_immutables.zones["interconnect_combinations"]
        if grid.interconnect[0] in interconnect_aliases:
            num_interconnects = len(interconnect_aliases[grid.interconnect[0]])
        else:
            num_interconnects = 1
    else:
        num_interconnects = len(grid.interconnect)
    if num_interconnects != num_connected_components:
        error_messages.append(
            f"This grid contains {num_connected_components} connected components, "
            f"but is specified as having {num_interconnects} interconnects: "
            f"{grid.interconnect}."
        )


def _check_grid_models_match(grid1, grid2):
    """Check whether an object is an internally-consistent Grid object.

    :param powersimdata.input.grid.Grid grid1: first Grid instance.
    :param powersimdata.input.grid.Grid grid2: second Grid instance.
    :raises ValueError: if the grid models don't match.
    """
    if not grid1.grid_model == grid2.grid_model:
        raise ValueError(
            f"Grid models don't match: {grid1.grid_model}, {grid2.grid_model}"
        )
