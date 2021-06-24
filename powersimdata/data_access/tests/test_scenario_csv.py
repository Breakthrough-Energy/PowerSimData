import os
import shutil
from collections import OrderedDict

import pandas as pd
import pytest
from numpy.testing import assert_array_equal
from pandas.testing import assert_frame_equal

from powersimdata.data_access.data_access import LocalDataAccess, SSHDataAccess
from powersimdata.data_access.scenario_list import ScenarioListManager
from powersimdata.utility import server_setup, templates


@pytest.fixture
def data_access():
    return SSHDataAccess()


@pytest.fixture
def scenario_table(data_access):
    scenario_list_manager = ScenarioListManager(data_access)
    return scenario_list_manager.get_scenario_table()


@pytest.mark.integration
@pytest.mark.ssh
def test_get_scenario_file_from_server_type(data_access, scenario_table):
    assert isinstance(scenario_table, pd.DataFrame)


@pytest.mark.integration
@pytest.mark.ssh
def test_get_scenario_file_from_server_header(data_access, scenario_table):
    header = [
        "plan",
        "name",
        "state",
        "grid_model",
        "interconnect",
        "base_demand",
        "base_hydro",
        "base_solar",
        "base_wind",
        "change_table",
        "start_date",
        "end_date",
        "interval",
        "engine",
        "runtime",
        "infeasibilities",
    ]
    assert_array_equal(scenario_table.columns, header)
    assert "id" == scenario_table.index.name


@pytest.mark.integration
@pytest.mark.ssh
def test_get_scenario_file_local(scenario_table):
    scm = ScenarioListManager(None)
    from_local = scm.get_scenario_table()
    assert_frame_equal(from_local, scenario_table)


def clone_template():
    orig = os.path.join(templates.__path__[0], "ScenarioList.csv")
    dest = os.path.join(server_setup.LOCAL_DIR, "ScenarioList.csv.test")
    shutil.copy(orig, dest)
    return dest


@pytest.fixture
def manager():
    test_csv = clone_template()
    data_access = LocalDataAccess()
    manager = ScenarioListManager(data_access)
    manager._FILE_NAME = "ScenarioList.csv.test"
    yield manager
    os.remove(test_csv)


def mock_row():
    return OrderedDict(
        [
            ("plan", "test"),
            ("name", "dummy"),
            ("state", "create"),
            ("grid_model", ""),
            ("interconnect", "Western"),
            ("base_demand", ""),
            ("base_hydro", ""),
            ("base_solar", ""),
            ("base_wind", ""),
            ("change_table", ""),
            ("start_date", ""),
            ("end_date", ""),
            ("interval", ""),
            ("engine", ""),
        ]
    )


def test_blank_csv_append(manager):
    entry = mock_row()
    table = manager.add_entry(entry)
    assert entry["id"] == "1"
    assert table.shape == (1, 16)


def test_get_scenario(manager):
    manager.add_entry(mock_row())
    manager.add_entry(mock_row())
    manager.add_entry(mock_row())
    entry = manager.get_scenario(2)
    assert entry["id"] == "2"
    entry = manager.get_scenario("2")
    assert entry["id"] == "2"


def test_delete_entry(manager):
    manager.add_entry(mock_row())
    manager.add_entry(mock_row())
    manager.add_entry(mock_row())
    table = manager.delete_entry(2)
    assert table.shape == (2, 16)
