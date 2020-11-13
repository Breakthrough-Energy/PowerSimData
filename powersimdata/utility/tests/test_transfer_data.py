import pandas as pd
import pytest
from numpy.testing import assert_array_equal
from pandas.testing import assert_frame_equal

from powersimdata.data_access.execute_list import ExecuteListManager
from powersimdata.data_access.scenario_list import ScenarioListManager
from powersimdata.utility.server_setup import get_server_user
from powersimdata.utility.transfer_data import SSHDataAccess


@pytest.fixture
def data_access():
    data_access = SSHDataAccess()
    yield data_access
    data_access.close()


@pytest.fixture
def scenario_table(data_access):
    scenario_list_manager = ScenarioListManager(data_access)
    return scenario_list_manager.get_scenario_table()


@pytest.fixture
def execute_table(data_access):
    execute_list_manager = ExecuteListManager(data_access)
    return execute_list_manager.get_execute_table()


@pytest.mark.integration
@pytest.mark.ssh
def test_setup_server_connection(data_access):
    _, stdout, _ = data_access.execute_command("whoami")
    assert stdout.read().decode("utf-8").strip() == get_server_user()


@pytest.mark.integration
@pytest.mark.ssh
def test_get_scenario_file_from_server_type(data_access, scenario_table):
    assert isinstance(scenario_table, pd.DataFrame)


@pytest.mark.integration
@pytest.mark.ssh
def test_get_scenario_file_from_server_header(data_access, scenario_table):
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
def test_get_scenario_file_local(scenario_table):
    scm = ScenarioListManager(None)
    from_local = scm.get_scenario_table()
    assert_frame_equal(from_local, scenario_table)


@pytest.mark.integration
@pytest.mark.ssh
def test_get_execute_file_local(execute_table):
    ecm = ExecuteListManager(None)
    from_local = ecm.get_execute_table()
    assert_frame_equal(from_local, execute_table)


@pytest.mark.integration
@pytest.mark.ssh
def test_get_execute_file_from_server_type(execute_table):
    assert isinstance(execute_table, pd.DataFrame)


@pytest.mark.integration
@pytest.mark.ssh
def test_get_execute_file_from_server_header(execute_table):
    header = ["id", "status"]
    assert_array_equal(execute_table.columns, header)
