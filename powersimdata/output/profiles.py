from postreise.process.transferdata import download
from postreise.process import const

import os
import pandas as pd


class OutputData(object):
    """Load output data.

    :param paramiko.client.SSHClient ssh_client: session with an SSH server.
    """

    def __init__(self, ssh_client):
        """Constructor

        """
        if not os.path.exists(const.LOCAL_DIR):
            os.makedirs(const.LOCAL_DIR)
        self._ssh = ssh_client

    def get_data(self, scenario_id, field_name):
        """Returns data either from server or from local directory.

        :param str scenario_id: scenario id.
        :param str field_name: *'PG'* or *'PF'*.
        :return: (*pandas.DataFrame*) -- PG or PF as a data frame.
        :raises FileNotFoundError: if file not found on local machine.
        :raises ValueError: if second argument is not one of *'PG'* or *'PF'*.
        """
        _check_field(field_name)

        print("--> Loading %s" % field_name)
        file_name = scenario_id + '_' + field_name + '.pkl'

        try:
            data = _read_data(file_name)
            return data
        except FileNotFoundError:
            print("%s not found in %s on local machine" % (file_name,
                                                           const.LOCAL_DIR))

        try:
            download(self._ssh, file_name, const.OUTPUT_DIR, const.LOCAL_DIR)
            data = _read_data(file_name)
            return data
        except FileNotFoundError:
            raise


def _read_data(file_name):
    """Reads data.

    :param str file_name: file name
    :return: (*pandas.DataFrame*) -- PG or PF as a data frame.
    """
    data = pd.read_pickle(os.path.join(const.LOCAL_DIR, file_name))

    return data


def _check_field(field_name):
    """Checks field name.

    :param str field_name: *'PG'* or *'PF'*.
    :raises ValueError: if not *'PG'* or *'PF'*.
    """
    possible = ['PG', 'PF']
    if field_name not in possible:
        raise ValueError('Only %s data can be loaded' % " | ".join(possible))
