import pandas as pd
import pytest
from numpy.testing import assert_array_equal
from pandas.testing import assert_frame_equal

from powersimdata.data_access.execute_list import ExecuteListManager
from powersimdata.data_access.scenario_list import ScenarioListManager
from powersimdata.utility.server_setup import get_server_user
from powersimdata.utility.transfer_data import setup_server_connection


@pytest.fixture
def ssh_client():
    ssh_client = setup_server_connection()
    yield ssh_client
    ssh_client.close()


@pytest.fixture
def scenario_table(ssh_client):
    scenario_list_manager = ScenarioListManager(ssh_client)
    return scenario_list_manager.get_scenario_table()


@pytest.fixture
def execute_table(ssh_client):
    execute_list_manager = ExecuteListManager(ssh_client)
    return execute_list_manager.get_execute_table()


@pytest.mark.integration
@pytest.mark.ssh
def test_setup_server_connection(ssh_client):
    _, stdout, _ = ssh_client.exec_command("whoami")
    assert stdout.read().decode("utf-8").strip() == get_server_user()


@pytest.mark.integration
@pytest.mark.ssh
def test_get_scenario_file_from_server_type(ssh_client, scenario_table):
    assert isinstance(scenario_table, pd.DataFrame)


@pytest.mark.integration
@pytest.mark.ssh
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
@pytest.mark.ssh
def test_get_scenario_file_local(ssh_client, scenario_table):
    scm = ScenarioListManager(None)
    from_local = scm.get_scenario_table()
    assert_frame_equal(from_local, scenario_table)


@pytest.mark.integration
@pytest.mark.ssh
def test_get_execute_file_local(ssh_client, execute_table):
    ecm = ExecuteListManager(None)
    from_local = ecm.get_execute_table()
    assert_frame_equal(from_local, execute_table)


@pytest.mark.integration
@pytest.mark.ssh
def test_get_execute_file_from_server_type(ssh_client, execute_table):
    assert isinstance(execute_table, pd.DataFrame)


@pytest.mark.integration
@pytest.mark.ssh
def test_get_execute_file_from_server_header(ssh_client, execute_table):
    header = ["id", "status"]
    assert_array_equal(execute_table.columns, header)
