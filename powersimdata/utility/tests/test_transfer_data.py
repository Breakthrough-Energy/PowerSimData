from powersimdata.data_access.scenario_list import ScenarioListManager
from powersimdata.utility.const import get_server_user
from powersimdata.utility.transfer_data import (
    setup_server_connection,
    get_execute_table,
)

from numpy.testing import assert_array_equal
import pandas as pd
import pytest


@pytest.fixture
def ssh_client():
    ssh_client = setup_server_connection()
    yield ssh_client
    ssh_client.close()


@pytest.fixture
def scenario_table(ssh_client):
    scenario_list_manager = ScenarioListManager(ssh_client)
    return scenario_list_manager.get_scenario_table()


@pytest.mark.integration
def test_setup_server_connection(ssh_client):
    _, stdout, _ = ssh_client.exec_command("whoami")
    assert stdout.read().decode("utf-8").strip() == get_server_user()


@pytest.mark.integration
def test_get_scenario_file_from_server_type(ssh_client, scenario_table):
    assert isinstance(scenario_table, pd.DataFrame)


@pytest.mark.integration
def test_get_scenario_file_from_server_header(ssh_client, scenario_table):
    header = [
        "id",
        "plan",
        "name",
        "state",
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


@pytest.mark.integration
def test_get_execute_file_from_server_type(ssh_client):
    table = get_execute_table(ssh_client)
    assert isinstance(table, pd.DataFrame)


@pytest.mark.integration
def test_get_execute_file_from_server_header(ssh_client):
    header = ["id", "status"]
    table = get_execute_table(ssh_client)
    assert_array_equal(table.columns, header)
