from dataclasses import dataclass

import pandas as pd


def check_bus_id(bus_id, grid):
    """Check that buses are within the given grid

    :param pd.Series bus_id: the bus ids to check
    :param powersimdata.input.grid.Grid grid: reference grid
    :raises ValueError: if any buses are not in the grid
    """
    valid = bus_id.isin(grid.bus.index)
    if not valid.all():
        msg = f"Invalid bus id = {list(bus_id[~valid])}"
        raise ValueError(msg)


def check_branch_voltage(branch, grid):
    """Check that branches are attached to buses with the same voltage

    :param pd.DataFrame branch: dataframe with from_bus and to_bus columns
    :param powersimdata.input.grid.Grid grid: reference grid
    :raises ValueError: if any branches have mismatched voltage
    """
    basekv = grid.bus.loc[:, "baseKV"]
    v1 = basekv[branch["from_bus"]].reset_index(drop=True)
    v2 = basekv[branch["to_bus"]].reset_index(drop=True)
    cmp = v1.compare(v2)
    if not cmp.empty:
        mismatch = list(cmp.index)
        raise ValueError(
            f"from_bus and to_bus must have the same baseKV. rows={mismatch}"
        )


def check_branch(branch, grid):
    """Check branch expansion candidates relative to a specific grid

    :param pd.DataFrame branch: dataframe of branch candidates
    :param powersimdata.input.grid.Grid grid: reference grid
    """
    check_bus_id(branch.from_bus, grid)
    check_bus_id(branch.to_bus, grid)
    check_branch_voltage(branch, grid)


def check_plant(plant, grid):
    """Check plant expansion candidates relative to a specific grid

    :param pd.DataFrame plant: dataframe of plant candidates
    :param powersimdata.input.grid.Grid grid: reference grid
    """
    check_bus_id(plant.bus_id, grid)


def check_storage(storage, grid):
    """Check storage expansion candidates relative to a specific grid

    :param pd.DataFrame storage: dataframe of storage candidates
    :param powersimdata.input.grid.Grid grid: reference grid
    """
    check_bus_id(storage.bus_id, grid)


def _validate_df(name, df):
    assert name in ("branch", "plant", "storage")
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"{name} must be a data frame")
    if not set(_required_columns[name]) <= set(df.columns):
        raise ValueError(f"{name} must have columns {_required_columns[name]}")
    return df.reindex(_columns[name], axis=1)


_columns = {
    "branch": ("from_bus", "to_bus", "inv_cost", "max_capacity"),
    "plant": ("bus_id", "type", "marginal_cost", "inv_cost", "max_capacity"),
    "storage": (
        "bus_id",
        "inv_cost_power",
        "inv_cost_energy",
        "max_capacity_energy",
        "max_capacity_power",
    ),
}
_required_columns = {
    "branch": ("from_bus", "to_bus"),
    "plant": ("bus_id", "type", "marginal_cost"),
    "storage": ("bus_id",),
}


@dataclass
class ExpansionCandidates:
    """Instantiate a data structure to hold candidates for expansion in a capacity
    expansion model.

    :param powersimdata.input.grid.Grid grid: reference grid
    """

    branch: pd.DataFrame
    plant: pd.DataFrame
    storage: pd.DataFrame

    def __init__(self, grid):
        self.branch = pd.DataFrame(columns=_columns["branch"])
        self.plant = pd.DataFrame(columns=_columns["plant"])
        self.storage = pd.DataFrame(columns=_columns["storage"])
        self.grid = grid

    def __repr__(self):
        name = self.__class__.__name__

        def _short_description(df, name):
            return f"{name}: cols={list(df.columns)}, rows={df.shape[0]}"

        branch = _short_description(self.branch, "branch")
        plant = _short_description(self.plant, "plant")
        storage = _short_description(self.storage, "storage")
        return f"{name}({branch}\n{plant}\n{storage})"

    def set_branch(self, branch):
        """Validate and assign branch candidates

        :param pd.DataFrame branch: branch dataframe
        """
        branch = _validate_df("branch", branch)
        check_branch(branch, self.grid)
        self.branch = branch

    def set_plant(self, plant):
        """Validate and assign plant candidates

        :param pd.DataFrame plant: plant dataframe
        """
        plant = _validate_df("plant", plant)
        check_plant(plant, self.grid)
        self.plant = plant

    def set_storage(self, storage):
        """Validate and assign storage candidates

        :param pd.DataFrame storage: storage dataframe
        """
        storage = _validate_df("storage", storage)
        check_storage(storage, self.grid)
        self.storage = storage
