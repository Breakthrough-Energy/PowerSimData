import pandas as pd
import pytest
from numpy.testing import assert_array_equal
from pandas.testing import assert_frame_equal

from powersimdata.data_access.data_access import SSHDataAccess
from powersimdata.data_access.scenario_list import ScenarioListManager


@pytest.fixture
def data_access():
    data_access = SSHDataAccess()
    yield data_access
    data_access.close()


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
