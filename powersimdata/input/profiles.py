from postreise.process.transferdata import download
from postreise.process import const

import os
import pandas as pd


class InputData(object):
    """Load input data.

    """

    def __init__(self):
        """Constructor.

        """
        if not os.path.exists(const.LOCAL_DIR):
            os.makedirs(const.LOCAL_DIR)

        self.file_extension = {'demand': 'csv', 'hydro': 'csv', 'solar': 'csv',
                               'wind': 'csv', 'ct': 'pkl'}

    def _check_field(self, field_name):
        """Checks field name.

        :param str field_name: *'demand'*, *'hydro'*, *'solar'* or *'wind'*.
        :raises ValueError: if not *'demand'*, *'hydro'*, *'solar'*, \
            *'wind'* or *'ct'*.
        """
        possible = list(self.file_extension.keys())
        if field_name not in possible:
            raise ValueError("Only %s data can be loaded" %
                             " | ".join(possible))

    def _read_data(self, file_name):
        """Reads data.

        :param str file_name: file name
        """
        ext = file_name.split(".")[-1]
        if ext == 'pkl':
            data = pd.read_pickle(os.path.join(const.LOCAL_DIR, file_name))
        elif ext == 'csv':
            data = pd.read_csv(os.path.join(const.LOCAL_DIR, file_name),
                               index_col=0, parse_dates=True)
            data.columns = data.columns.astype(int)

        return data

    def get_data(self, scenario_id, field_name):
        """Returns data either from server or local directory.

        :param str scenario_id: scenario id.
        :param str field_name: *'demand'*, *'hydro'*, *'solar'* or *'wind'*.
        :return: (*pandas* or *dict*) -- demand, hydro, solar or wind as a \
            data frame or changle table as a dictionary.
        :raises FileNotFoundError: if file not found on local machine.
        """
        self._check_field(field_name)

        print("--> Loading %s" % field_name)
        ext = self.file_extension[field_name]
        file_name = scenario_id + '_' + field_name + '.' + ext

        try:
            data = self._read_data(file_name)
            return data
        except FileNotFoundError:
            print("%s not found in %s on local machine" %
                  (file_name, const.LOCAL_DIR))

        try:
            download(file_name, const.INPUT_DIR, const.LOCAL_DIR)
            data = self._read_data(file_name)
            return data
        except FileNotFoundError as e:
            raise(e)
