import pandas as pd
import pytest
from numpy.testing import assert_array_equal
from pandas.testing import assert_frame_equal

from powersimdata.data_access.data_access import SSHDataAccess
from powersimdata.data_access.execute_list import ExecuteListManager


@pytest.fixture
def data_access():
    data_access = SSHDataAccess()
    yield data_access
    data_access.close()


@pytest.fixture
def execute_table(data_access):
    execute_list_manager = ExecuteListManager(data_access)
    return execute_list_manager.get_execute_table()


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
    header = ["status"]
    assert_array_equal(execute_table.columns, header)
    assert "id" == execute_table.index.name
