import pandas as pd


class AbstractGrid(object):
    """Grid Builder.

    """
    def __init__(self):
        """Constructor

        """
        self.data_loc = None
        self.interconnect = None
        self.zone2id = {}
        self.id2zone = {}
        self.sub = pd.DataFrame()
        self.plant = pd.DataFrame()
        self.gencost = {'before': pd.DataFrame(), 'after': pd.DataFrame()}
        self.dcline = pd.DataFrame()
        self.bus2sub = pd.DataFrame()
        self.bus = pd.DataFrame()
        self.branch = pd.DataFrame()
        self.storage = {}
