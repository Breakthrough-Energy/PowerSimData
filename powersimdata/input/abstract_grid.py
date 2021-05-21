import pandas as pd


class AbstractGrid:
    """Grid Builder."""

    def __init__(self):
        """Constructor"""
        self.data_loc = None
        self.interconnect = None
        self.zone2id = {}
        self.id2zone = {}
        self.sub = pd.DataFrame()
        self.plant = pd.DataFrame()
        self.gencost = {"before": pd.DataFrame(), "after": pd.DataFrame()}
        self.dcline = pd.DataFrame()
        self.bus2sub = pd.DataFrame()
        self.bus = pd.DataFrame()
        self.branch = pd.DataFrame()
        self.storage = storage_template()


def storage_template():
    """Get storage

    :return: (*dict*) -- storage structure for MATPOWER/MOST
    """
    storage = {
        "gen": pd.DataFrame(
            columns=[
                "bus_id",
                "Pg",
                "Qg",
                "Qmax",
                "Qmin",
                "Vg",
                "mBase",
                "status",
                "Pmax",
                "Pmin",
                "Pc1",
                "Pc2",
                "Qc1min",
                "Qc1max",
                "Qc2min",
                "Qc2max",
                "ramp_agc",
                "ramp_10",
                "ramp_30",
                "ramp_q",
                "apf",
                "mu_Pmax",
                "mu_Pmin",
                "mu_Qmax",
                "mu_Qmin",
            ]
        ),
        "gencost": pd.DataFrame(
            columns=["type", "startup", "shutdown", "n", "c2", "c1", "c0"]
        ),
        "StorageData": pd.DataFrame(
            columns=[
                "UnitIdx",
                "InitialStorage",
                "InitialStorageLowerBound",
                "InitialStorageUpperBound",
                "InitialStorageCost",
                "TerminalStoragePrice",
                "MinStorageLevel",
                "MaxStorageLevel",
                "OutEff",
                "InEff",
                "LossFactor",
                "rho",
                "ExpectedTerminalStorageMax",
                "ExpectedTerminalStorageMin",
            ]
        ),
        "genfuel": [],
        "duration": None,  # hours
        "min_stor": None,  # ratio
        "max_stor": None,  # ratio
        "InEff": None,
        "OutEff": None,
        "LossFactor": None,  # stored energy fraction / hour
        "energy_price": None,  # $/MWh
        "terminal_min": None,
        "terminal_max": None,
    }
    return storage
