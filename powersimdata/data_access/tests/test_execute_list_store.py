from powersimdata.data_access.execute_list import ExecuteTable
from powersimdata.data_access.sql_store import SqlException

import pytest
from collections import OrderedDict

row_id = 9000


def _get_test_row():
    global row_id
    row_id += 1
    return OrderedDict([("id", row_id)])


class NoEffectSqlStore(ExecuteTable):
    def __exit__(self, exc_type, exc_value, traceback):
        self.conn.rollback()
        super().__exit__(exc_type, exc_value, traceback)


class RaiseErrorSqlStore(ExecuteTable):
    def add_entry(self, scenario_info):
        raise Exception("Error while executing sql")


@pytest.fixture
def store():
    with NoEffectSqlStore() as store:
        yield store


@pytest.mark.integration
def test_err_handle():
    with pytest.raises(SqlException):
        with RaiseErrorSqlStore() as store:
            store.add_entry(None)


@pytest.mark.integration
def test_select_no_limit(store):
    store.add_entry(_get_test_row())
    store.add_entry(_get_test_row())
    result = store.get_execute_table()
    assert len(result) > 1


@pytest.mark.integration
def test_select_with_limit(store):
    n_rows = 6
    limit = 3
    for i in range(n_rows):
        store.add_entry(_get_test_row())
    result = store.get_execute_table(limit)
    assert len(result) == limit


@pytest.mark.integration
def test_add_entry(store):
    info = _get_test_row()
    store.add_entry(info)
    status = store.get_status(info["id"])
    assert status["status"] == "created"


@pytest.mark.integration
def test_update_entry(store):
    info = _get_test_row()
    store.add_entry(info)
    store.update_execute_list("testing", info)
    status = store.get_status(info["id"])
    assert status["status"] == "testing"


@pytest.mark.integration
def test_delete_entry(store):
    info = _get_test_row()
    store.add_entry(info)
    store.delete_entry(info)
    status = store.get_status(info["id"])
    assert status is None
