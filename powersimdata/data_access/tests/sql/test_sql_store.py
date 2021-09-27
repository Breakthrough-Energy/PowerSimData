import pytest

from powersimdata.data_access.sql_store import SqlStore


class DummySqlStore(SqlStore):
    table = "my_table"
    columns = ["id", "foo", "bar"]


@pytest.fixture
def store():
    with DummySqlStore() as store:
        yield store


@pytest.mark.integration
@pytest.mark.db
def test_select_where(store):
    query = store.select_where("id")
    sql_str = query.as_string(store.conn)
    expected = 'SELECT "id","foo","bar" FROM "my_table" WHERE "id" = %s'
    assert expected == sql_str


@pytest.mark.integration
@pytest.mark.db
def test_select_all(store):
    query = store.select_all()
    sql_str = query.as_string(store.conn)
    expected = 'SELECT "id","foo","bar" FROM "my_table"'
    assert expected == sql_str


@pytest.mark.integration
@pytest.mark.db
def test_insert(store):
    query = store.insert()
    sql_str = query.as_string(store.conn)
    expected = 'INSERT INTO "my_table" ("id","foo","bar") VALUES (%s,%s,%s)'
    assert expected == sql_str


@pytest.mark.integration
@pytest.mark.db
def test_delete(store):
    query = store.delete(key="id")
    sql_str = query.as_string(store.conn)
    expected = 'DELETE FROM "my_table" WHERE "id" = %s'
    assert expected == sql_str
