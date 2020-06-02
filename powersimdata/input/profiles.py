from powersimdata.utility.transfer_data import download
from powersimdata.utility import const

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
        :return: (*pandas.DataFrame*, *dict*, or *str*) --
            demand, hydro, solar or wind as a data frame, change table as a
            dictionary, or the path to a matfile with Grid data.
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

    :param str file_name: file name, extension either 'pkl', 'csv', or 'mat'.
    :return: (*pandas.DataFrame*, *dict*, or *str*) -- demand, hydro, solar or
        wind as a data frame, change table as a dict, or str containing a
        local path to a matfile of grid data.
    :raises ValueError: if extension is unknown.
    """
    ext = file_name.split(".")[-1]
    filepath = os.path.join(const.LOCAL_DIR, file_name)
    if ext == 'pkl':
        data = pd.read_pickle(filepath)
    elif ext == 'csv':
        data = pd.read_csv(filepath, index_col=0, parse_dates=True)
        data.columns = data.columns.astype(int)
    elif ext == 'mat':
        # Try to load the matfile, just to check if it exists locally
        open(filepath, 'r')
        data = filepath
    else:
        raise ValueError('Unknown extension! %s' % ext)

    return data


def get_bus_demand(ssh_client, scenario_id, grid):
    """Returns demand profiles by bus.

    :param paramiko.client.SSHClient ssh_client: session with an SSH server.
    :param str scenario_id: scenario id.
    :param powersimdata.input.grid.Grid grid: grid to construct bus demand for.
    :return: (*pandas.DataFrame*) -- data frame of demand.
    """
    input = InputData(ssh_client)
    demand = input.get_data(scenario_id, 'demand')
    bus = grid.bus
    bus['zone_Pd'] = bus.groupby('zone_id')['Pd'].transform('sum')
    bus['zone_share'] = bus['Pd'] / bus['zone_Pd']
    zone_bus_shares = pd.DataFrame({
        z: bus.groupby('zone_id').get_group(z).zone_share
        for z in demand.columns}).fillna(0)
    bus_demand = demand.dot(zone_bus_shares.T)

    return bus_demand
