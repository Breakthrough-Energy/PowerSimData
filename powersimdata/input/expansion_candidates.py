import pandas as pd


class ExpansionCandidates:
    """Instantiate a data structure to hold candidates for expansion in a capacity
    expansion model.

    :param pandas.DataFrame branch: branch candidate information.
    :param pandas.DataFrame plant: plant candidate information.
    :param pandas.DataFrame storage: storage candidate information.
    """

    columns = {
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
    required_columns = {
        "branch": ("from_bus", "to_bus"),
        "plant": ("bus_id", "type", "marginal_cost"),
        "storage": ("bus_id"),
    }

    def __init__(self, branch=None, plant=None, storage=None):
        """Constructor."""

        if branch is None:
            self.branch = pd.DataFrame(columns=self.columns["branch"])
        else:
            if not isinstance(branch, pd.DataFrame):
                raise TypeError("branch must be a data frame")
            if not set(self.required_columns["branch"]) <= set(branch.columns):
                raise TypeError(
                    f"branch must have columns {self.required_columns['branch']}"
                )
            self.branch = branch.reindex(self.columns["branch"], axis=1)

        if plant is None:
            self.plant = pd.DataFrame(columns=self.columns["plant"])
        else:
            if not isinstance(plant, pd.DataFrame):
                raise TypeError("plant must be a data frame")
            if not set(self.required_columns["plant"]) <= set(plant.columns):
                raise TypeError(
                    f"plant must have columns {self.required_columns['plant']}"
                )
            self.plant = plant.reindex(self.columns["plant"], axis=1)

        if storage is None:
            self.storage = pd.DataFrame(columns=self.columns["storage"])
        else:
            if not isinstance(storage, pd.DataFrame):
                raise TypeError("storage must be a data frame")
            if not set(self.required_columns["storage"]) <= set(storage.columns):
                raise TypeError(
                    f"storage must have columns {self.required_columns['storage']}"
                )
            self.storage = storage.reindex(self.columns["storage"], axis=1)
