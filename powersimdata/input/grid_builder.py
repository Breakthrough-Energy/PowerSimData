import pandas as pd


class _GridBuilder(object):
    """Grid Builder.

    """
    def __init__(self):
        """Constructor

        """
        self.data_loc = None
        self.interconnect = None
        self.zone2id = {}
        self.id2zone = {}
        self.type2id = {}
        self.id2type = {}
        self.type2color = {}
        self.sub = pd.DataFrame()
        self.plant = pd.DataFrame()
        self.gencost = pd.DataFrame()
        self.dcline = pd.DataFrame()
        self.bus2sub = pd.DataFrame()
        self.bus = pd.DataFrame()
        self.branch = pd.DataFrame()
        self.storage = {}
