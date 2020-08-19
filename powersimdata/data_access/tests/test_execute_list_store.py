from powersimdata.data_access.execute_list import ExecuteTable

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


@pytest.fixture
def store():
    with NoEffectSqlStore() as store:
        yield store


@pytest.mark.integration
def test_select_no_limit(store):
    store.add_entry(_get_test_row())
    store.add_entry(_get_test_row())
    result = store.get_execute_table()
    assert len(result) > 1


@pytest.mark.integration
def test_select_with_limit(store):
    result = store.get_execute_table(4)
    assert len(result) == 4


@pytest.mark.integration
def test_add_entry(store):
    info = _get_test_row()
    store.add_entry(info)
    status = store.get_status(info["id"])
    assert status[0] == "created"


@pytest.mark.integration
def test_update_entry(store):
    info = _get_test_row()
    store.add_entry(info)
    store.update_execute_list("testing", info)
    status = store.get_status(info["id"])
    assert status[0] == "testing"


@pytest.mark.integration
def test_delete_entry(store):
    info = _get_test_row()
    store.add_entry(info)
    store.delete_entry(info)
    status = store.get_status(info["id"])
    assert status is None
