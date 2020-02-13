from postreise.process.transferdata import download
from postreise.process import const
from powersimdata.input.grid import Grid

import os
import pandas as pd


class InputData(object):
    """Load input data.

    :param paramiko.client.SSHClient ssh_client: session with an SSH server.
    """

    def __init__(self, ssh_client):
        """Constructor.

        """
        if not os.path.exists(const.LOCAL_DIR):
            os.makedirs(const.LOCAL_DIR)

        self.file_extension = {'demand': 'csv',
                               'hydro': 'csv',
                               'solar': 'csv',
                               'wind': 'csv',
                               'ct': 'pkl',
                               'grid': 'mat'}
        self._ssh = ssh_client

    def _check_field(self, field_name):
        """Checks field name.

        :param str field_name: *'demand'*, *'hydro'*, *'solar'*, *'wind'*,
            *'ct'* or *'grid'*.
        :raises ValueError: if not *'demand'*, *'hydro'*, *'solar'*, *'wind'*
            *'ct'* or *'grid'*
        """
        possible = list(self.file_extension.keys())
        if field_name not in possible:
            raise ValueError("Only %s data can be loaded" %
                             " | ".join(possible))

    def get_data(self, scenario_id, field_name):
        """Returns data either from server or local directory.

        :param str scenario_id: scenario id.
        :param str field_name: *'demand'*, *'hydro'*, *'solar'*, *'wind'*,
            *'ct'* or *'grid'*.
        :return: (*pandas.DataFrame*, *dict* or *powersimdata.input.Grid*) --
            demand, hydro, solar or wind as a data frame, change table as a
            dictionary or grid instance.
        :raises FileNotFoundError: if file not found on local machine.
        """
        self._check_field(field_name)

        print("--> Loading %s" % field_name)
        ext = self.file_extension[field_name]
        file_name = scenario_id + '_' + field_name + '.' + ext

        try:
            data = _read_data(file_name)
            return data
        except FileNotFoundError:
            print('%s not found in %s on local machine' %
                  (file_name, const.LOCAL_DIR))

        try:
            download(self._ssh, file_name, const.INPUT_DIR, const.LOCAL_DIR)
            data = _read_data(file_name)
            return data
        except FileNotFoundError:
            raise


def _read_data(file_name):
    """Reads data.

    :param str file_name: file name
    :return: (*pandas.DataFrame or dict*) -- demand, hydro, solar or wind as a
        data frame or change table as a dictionary.
    """
    ext = file_name.split(".")[-1]
    if ext == 'pkl':
        data = pd.read_pickle(os.path.join(const.LOCAL_DIR, file_name))
    elif ext == 'csv':
        data = pd.read_csv(os.path.join(const.LOCAL_DIR, file_name),
                           index_col=0, parse_dates=True)
        data.columns = data.columns.astype(int)
    else:
        data = Grid([None], source=os.path.join(const.LOCAL_DIR, file_name))

    return data
