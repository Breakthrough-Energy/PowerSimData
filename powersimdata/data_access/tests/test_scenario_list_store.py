from powersimdata.data_access.scenario_list import ScenarioTable
from powersimdata.data_access.sql_store import SqlException

import pytest
from collections import OrderedDict


row_id = 9000


def _get_test_row(
    name="foo", interconnect="Western", base_demand="v3", base_hydro="v2"
):
    global row_id
    row_id += 1
    return OrderedDict(
        [
            ("id", str(row_id)),
            ("plan", ""),
            ("name", name),
            ("state", "create"),
            ("interconnect", interconnect),
            ("base_demand", base_demand),
            ("base_hydro", base_hydro),
            ("base_solar", ""),
            ("base_wind", ""),
            ("change_table", False),
            ("start_date", "2016-01-01 00:00:00"),
            ("end_date", "2016-12-31 23:00:00"),
            ("interval", ""),
            ("engine", ""),
            ("runtime", ""),
            ("infeasibilities", ""),
        ]
    )


class NoEffectSqlStore(ScenarioTable):
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
    result = store.get_scenario_table()
    assert len(result) > 1


@pytest.mark.integration
def test_select_with_limit(store):
    n_rows = 6
    limit = 3
    for i in range(n_rows):
        store.add_entry(_get_test_row())
    result = store.get_scenario_table(limit)
    assert len(result) == limit


@pytest.mark.integration
def test_add_entry(store):
    info = _get_test_row(name="bar")
    store.add_entry(info)
    entry = store.get_scenario_by_id(info["id"])
    assert entry[2] == "bar"


@pytest.mark.integration
def test_add_entry_missing_required_raises(store):
    info = _get_test_row()
    del info["plan"]
    with pytest.raises(Exception):
        store.add_entry(info)


@pytest.mark.integration
def test_delete_entry(store):
    info = _get_test_row()
    store.add_entry(info)
    store.delete_entry(info)
    entry = store.get_scenario_by_id(info["id"])
    assert entry is None
