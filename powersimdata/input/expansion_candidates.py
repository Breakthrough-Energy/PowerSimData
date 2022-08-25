from dataclasses import dataclass

import pandas as pd


def check_branch(branch, grid):
    basekv = grid.bus.loc[:, "baseKV"]
    v1 = basekv[branch["from_bus"]].reset_index(drop=True)
    v2 = basekv[branch["to_bus"]].reset_index(drop=True)
    cmp = v1.compare(v2)
    if not cmp.empty:
        mismatch = list(cmp.index)
        raise ValueError(
            f"from_bus and to_bus must have the same baseKV. rows={mismatch}"
        )


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

    def __init__(self):
        self.branch = pd.DataFrame(columns=_columns["branch"])
        self.plant = pd.DataFrame(columns=_columns["plant"])
        self.storage = pd.DataFrame(columns=_columns["storage"])

    def _assign(self, name, df):
        assert name in ("branch", "plant", "storage")
        if not isinstance(df, pd.DataFrame):
            raise TypeError(f"{name} must be a data frame")
        if not set(_required_columns[name]) <= set(df.columns):
            raise TypeError(f"{name} must have columns {_required_columns[name]}")
        setattr(self, name, df.reindex(_columns[name], axis=1))

    def set_branch(self, branch):
        self._assign("branch", branch)

    def set_plant(self, plant):
        self._assign("plant", plant)

    def set_storage(self, storage):
        self._assign("storage", storage)
