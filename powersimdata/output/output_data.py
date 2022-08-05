import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix

from powersimdata.data_access.context import Context
from powersimdata.data_access.fs_helper import get_scenario_fs
from powersimdata.input.input_data import distribute_demand_from_zones_to_buses
from powersimdata.input.transform_profile import TransformProfile
from powersimdata.utility import server_setup


class OutputData:
    """Load output data."""

    def __init__(self):
        """Constructor"""
        self._data_access = Context.get_data_access(get_scenario_fs)

    def get_data(self, scenario_id, field_name):
        """Returns data either from server or from local directory.

        :param str scenario_id: scenario id.
        :param str field_name: *'PG'*, *'PF'*, *'PF_DCLINE'*, *'LMP'*, *'CONGU'*,
            *'CONGL'*, *'AVERAGED_CONG'*, *'STORAGE_PG'*, *'STORAGE_E'*, *'LOAD_SHED'*,
            *'LOAD_SHIFT_UP'*, or *'LOAD_SHIFT_DN'*.
        :return: (*pandas.DataFrame*) -- specified field as a data frame.
        :raises FileNotFoundError: if file not found on local machine.
        :raises ValueError: if second argument is not an allowable field.
        """
        _check_field(field_name)

        print("--> Loading %s" % field_name)
        file_name = scenario_id + "_" + field_name + ".pkl"
        filepath = "/".join([*server_setup.OUTPUT_DIR, file_name])
        with self._data_access.get(filepath) as (f, _):
            return pd.read_pickle(f)


def _check_field(field_name):
    """Checks field name.

    :param str field_name: *'PG'*, *'PF'*, *'PF_DCLINE'*, *'LMP'*, *'CONGU'*,
        *'CONGL'*, *'AVERAGED_CONG'*, *'STORAGE_PG'*, *'STORAGE_E'*, *'LOAD_SHED'*,
        *'LOAD_SHIFT_UP'*, or *'LOAD_SHIFT_DN'*.
    :raises ValueError: if not *'PG'*, *'PF'*, *'PF_DCLINE'*, *'LMP'*,
        *'CONGU'*, or *'CONGL'*, *'AVERAGED_CONG'*, *'STORAGE_PG'*,
        *'STORAGE_E'*, *'LOAD_SHED'*, *'LOAD_SHIFT_UP'*, or *'LOAD_SHIFT_DN'*.
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
        "LOAD_SHIFT_UP",
        "LOAD_SHIFT_DN",
    ]
    if field_name not in possible:
        raise ValueError("Only %s data can be loaded" % " | ".join(possible))


def construct_load_shed(scenario_info, grid, ct, infeasibilities=None):
    """Constructs load_shed dataframe from relevant scenario/grid data.

    :param dict scenario_info: info attribute of Scenario object.
    :param powersimdata.input.grid.Grid grid: grid to construct load_shed for.
    :param dict ct: ChangeTable dictionary.
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
        zone_demand = TransformProfile(scenario_info, grid, ct)
        bus_demand = distribute_demand_from_zones_to_buses(zone_demand, grid.bus)
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
