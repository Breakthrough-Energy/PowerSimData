from collections import OrderedDict

import pytest

from powersimdata.data_access.scenario_table import ScenarioTable
from powersimdata.data_access.sql_store import SqlError

# uncomment to enable logging queries to stdout
# os.environ["DEBUG_MODE"] = "1"

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
            ("grid_model", ""),
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
@pytest.mark.db
def test_select_no_limit(store):
    store.add_entry(_get_test_row())
    store.add_entry(_get_test_row())
    result = store.get_scenario_table()
    assert result.shape[0] == 2


@pytest.mark.integration
@pytest.mark.db
def test_select_with_limit(store):
    n_rows = 6
    limit = 3
    for i in range(n_rows):
        store.add_entry(_get_test_row())
    result = store.get_scenario_table(limit)
    assert result.shape[0] == limit


@pytest.mark.integration
@pytest.mark.db
def test_add_entry(store):
    info = _get_test_row(name="bar")
    store.add_entry(info)
    entry = store.get_scenario_by_id(info["id"])
    assert entry.loc[0, "name"] == "bar"


@pytest.mark.integration
@pytest.mark.db
def test_add_entry_missing_required_raises():
    info = _get_test_row()
    del info["plan"]
    with pytest.raises(SqlError):
        # create explicitly since yield loses exception context
        with NoEffectSqlStore() as store:
            store.add_entry(info)


@pytest.mark.integration
@pytest.mark.db
def test_delete_entry(store):
    info = _get_test_row()
    sid = info["id"]
    store.add_entry(info)
    store.delete_entry(sid)
    entry = store.get_scenario_by_id(sid)
    assert entry.shape == (0, 0)
