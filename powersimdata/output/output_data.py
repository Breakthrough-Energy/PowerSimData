from powersimdata.input.input_data import get_bus_demand
from powersimdata.utility.transfer_data import download
from powersimdata.utility import server_setup, backup

import numpy as np
import os
import pandas as pd
from scipy.sparse import coo_matrix


class OutputData(object):
    """Load output data.

    :param paramiko.client.SSHClient ssh_client: session with an SSH server.
    :param str data_loc: data location.
    """

    def __init__(self, ssh_client, data_loc=None):
        """Constructor"""
        if not os.path.exists(server_setup.LOCAL_DIR):
            os.makedirs(server_setup.LOCAL_DIR)
        self._ssh = ssh_client
        self.data_loc = data_loc

    def get_data(self, scenario_id, field_name):
        """Returns data either from server or from local directory.

        :param str scenario_id: scenario id.
        :param str field_name: *'PG'*, *'PF'*, *'LMP'*, *'CONGU'*, *'CONGL'*,
            *'AVERAGED_CONG'*, *'STORAGE_PG'* or *'STORAGE_E'*.
        :return: (*pandas.DataFrame*) -- specified field as a data frame.
        :raises FileNotFoundError: if file not found on local machine.
        :raises ValueError: if second argument is not an allowable field.
        """
        _check_field(field_name)

        print("--> Loading %s" % field_name)
        file_name = scenario_id + "_" + field_name + ".pkl"

        try:
            data = _read_data(file_name)
            return data
        except FileNotFoundError:
            print(
                "%s not found in %s on local machine"
                % (file_name, server_setup.LOCAL_DIR)
            )

        try:
            if self.data_loc == "disk":
                download(
                    self._ssh, file_name, backup.OUTPUT_DIR, server_setup.LOCAL_DIR
                )
            else:
                download(
                    self._ssh,
                    file_name,
                    server_setup.OUTPUT_DIR,
                    server_setup.LOCAL_DIR,
                )
            data = _read_data(file_name)
            return data
        except FileNotFoundError:
            raise


def _read_data(file_name):
    """Reads data.

    :param str file_name: file name
    :return: (*pandas.DataFrame*) -- specified file as a data frame.
    """
    data = pd.read_pickle(os.path.join(server_setup.LOCAL_DIR, file_name))

    return data


def _check_field(field_name):
    """Checks field name.

    :param str field_name: *'PG'*, *'PF'*, *'PF_DCLINE'*, *'LMP'*, *'CONGU'*,
        *'CONGL'*, *'AVERAGED_CONG'*, *'STORAGE_PG'*, *'STORAGE_E'*,
        or *'LOAD_SHED'*
    :raises ValueError: if not *'PG'*, *'PF'*, *'PF_DCLINE'*, *'LMP'*,
        *'CONGU'*, or *'CONGL'*, *'AVERAGED_CONG'*, *'STORAGE_PG'*,
        *'STORAGE_E'*, or *'LOAD_SHED'*.
    """
    possible = [
        "PG",
        "PF",
        "PF_DCLINE",
        "LMP",
        "CONGU",
        "CONGL",
        "AVERAGED_CONG",
        "STORAGE_PG",
        "STORAGE_E",
        "LOAD_SHED",
    ]
    if field_name not in possible:
        raise ValueError("Only %s data can be loaded" % " | ".join(possible))


def construct_load_shed(ssh_client, scenario_info, grid, infeasibilities=None):
    """Constructs load_shed dataframe from relevant scenario/grid data.

    :param paramiko.client.SSHClient ssh_client: session with an SSH server.
    :param dict scenario_info: info attribute of Scenario object.
    :param powersimdata.input.grid.Grid grid: grid to construct load_shed for.
    :param dict/None infeasibilities: dictionary of
        {interval (int): load shed percentage (int)}, or None.
    :return: (*pandas.DataFrame*) -- data frame of load_shed.
    """
    hours = pd.date_range(
        start=scenario_info["start_date"], end=scenario_info["end_date"], freq="1H"
    ).tolist()
    buses = grid.bus.index
    if infeasibilities is None:
        print("No infeasibilities, constructing DataFrame")
        load_shed_data = coo_matrix((len(hours), len(buses)))
        load_shed = pd.DataFrame.sparse.from_spmatrix(load_shed_data)
    else:
        print("Infeasibilities, constructing DataFrame")
        bus_demand = get_bus_demand(ssh_client, scenario_info["id"], grid)
        load_shed = np.zeros((len(hours), len(buses)))
        # Convert '24H' to 24
        interval = int(scenario_info["interval"][:-1])
        for i, v in infeasibilities.items():
            start = i * interval
            end = (i + 1) * interval
            base_demand = bus_demand.iloc[start:end, :].to_numpy()
            shed_demand = base_demand * (v / 100)
            load_shed[start:end, :] = shed_demand
        load_shed = pd.DataFrame(load_shed, columns=buses, index=hours)
        load_shed = load_shed.astype(pd.SparseDtype("float", 0))
    load_shed.index = hours
    load_shed.index.name = "UTC"
    load_shed.columns = buses

    return load_shed
