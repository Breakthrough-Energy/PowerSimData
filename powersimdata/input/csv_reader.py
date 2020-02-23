import pandas as pd

from powersimdata.input.helpers import csv_to_data_frame


class CSVReader(object):
    """MPC files reader

    """
    def __init__(self, data_loc):
        """Constructor

        :param str data_loc: path to data.
        """
        self.bus = csv_to_data_frame(data_loc, 'bus.csv')
        self.plant = csv_to_data_frame(data_loc, 'plant.csv')
        self.gencost = csv_to_data_frame(data_loc, 'gencost.csv')
        self.branch = csv_to_data_frame(data_loc, 'branch.csv')
        self.dcline = csv_to_data_frame(data_loc, 'dcline.csv')
