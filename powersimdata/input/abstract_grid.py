import pandas as pd

from powersimdata.input.const import grid_const


class AbstractGrid:
    """Grid Builder."""

    def __init__(self):
        """Constructor"""
        self.data_loc = None
        self.interconnect = None
        self.zone2id = {}
        self.id2zone = {}
        self.sub = pd.DataFrame(columns=grid_const.col_name_sub).rename_axis(
            grid_const.indices["sub"]
        )
        self.plant = pd.DataFrame(columns=grid_const.col_name_plant).rename_axis(
            grid_const.indices["plant"]
        )
        self.gencost = {
            "before": pd.DataFrame(columns=grid_const.col_name_gencost).rename_axis(
                grid_const.indices["plant"]
            ),
            "after": pd.DataFrame(columns=grid_const.col_name_gencost).rename_axis(
                grid_const.indices["plant"]
            ),
        }
        self.dcline = pd.DataFrame(columns=grid_const.col_name_dcline).rename_axis(
            grid_const.indices["dcline"]
        )
        self.bus2sub = pd.DataFrame(columns=grid_const.col_name_bus2sub).rename_axis(
            grid_const.indices["bus2sub"]
        )
        self.bus = pd.DataFrame(columns=grid_const.col_name_bus).rename_axis(
            grid_const.indices["bus"]
        )
        self.branch = pd.DataFrame(columns=grid_const.col_name_branch).rename_axis(
            grid_const.indices["branch"]
        )
        self.storage = storage_template()
        self.grid_model = ""
        self.model_immutables = None


def storage_template():
    """Get storage

    :return: (*dict*) -- storage structure for MATPOWER/MOST
    """
    storage = {
        "gen": pd.DataFrame(columns=grid_const.col_name_plant),
        "gencost": pd.DataFrame(columns=grid_const.col_name_gencost),
        "StorageData": pd.DataFrame(columns=grid_const.col_name_storage_storagedata),
        "genfuel": [],
        "duration": None,  # hours
        "min_stor": None,  # ratio
        "max_stor": None,  # ratio
        "InEff": None,
        "OutEff": None,
        "LossFactor": None,  # stored energy fraction / hour
        "energy_value": None,  # $/MWh
        "terminal_min": None,
        "terminal_max": None,
    }
    return storage
