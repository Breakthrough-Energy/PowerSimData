from dataclasses import dataclass

import pandas as pd


def check_bus_id(bus_id, grid):
    valid = bus_id.isin(grid.bus.index)
    if not valid.all():
        msg = f"Invalid bus id = {list(bus_id[~valid])}"
        raise ValueError(msg)


def check_branch_voltage(branch, grid):
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
    check_branch_voltage(branch, grid)
    check_bus_id(branch.from_bus, grid)
    check_bus_id(branch.to_bus, grid)


def check_plant(plant, grid):
    check_bus_id(plant.bus_id, grid)


def check_storage(storage, grid):
    check_bus_id(storage.bus_id, grid)


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
    "storage": ("bus_id"),
}


@dataclass
class ExpansionCandidates:
    """Instantiate a data structure to hold candidates for expansion in a capacity
    expansion model.
    """

    branch: pd.DataFrame
    plant: pd.DataFrame
    storage: pd.DataFrame

    def __init__(self, grid):
        self.branch = pd.DataFrame(columns=_columns["branch"])
        self.plant = pd.DataFrame(columns=_columns["plant"])
        self.storage = pd.DataFrame(columns=_columns["storage"])
        self.grid = grid

    def _validate_df(self, name, df):
        assert name in ("branch", "plant", "storage")
        if not isinstance(df, pd.DataFrame):
            raise TypeError(f"{name} must be a data frame")
        if not set(_required_columns[name]) <= set(df.columns):
            raise TypeError(f"{name} must have columns {_required_columns[name]}")
        # setattr(self, name, df.reindex(_columns[name], axis=1))
        return df.reindex(_columns[name], axis=1)

    def set_branch(self, branch):
        branch = self._validate_df("branch", branch)
        check_branch(branch, self.grid)
        self.branch = branch

    def set_plant(self, plant):
        plant = self._validate_df("plant", plant)
        check_plant(plant, self.grid)
        self.plant = plant

    def set_storage(self, storage):
        storage = self._validate_df("storage", storage)
        check_storage(storage, self.grid)
        self.storage = storage
