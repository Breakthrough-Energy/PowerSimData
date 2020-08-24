import psycopg2
import psycopg2.extensions
import psycopg2.extras
from psycopg2.sql import SQL, Identifier, Placeholder
import sys
import os


class SqlException(Exception):
    pass


class LoggingCursor(psycopg2.extras.DictCursor):
    def execute(self, sql, args=None):
        print(self.mogrify(sql, args))

        try:
            super().execute(sql, args)
        except Exception as exc:
            print("%s: %s" % (exc.__class__.__name__, exc))
            raise


def get_connection():
    return "dbname=psd host=localhost user=postgres password=example"


def get_cursor_factory():
    if os.environ.get("DEBUG_MODE"):
        return LoggingCursor
    return psycopg2.extras.DictCursor


class SqlStore:
    def __init__(self):
        self.conn = psycopg2.connect(get_connection())

    def _table(self):
        if hasattr(self, "table"):
            return Identifier(self.table)
        raise ValueError("No table defined")

    def _columns(self, subset=None):
        if hasattr(self, "columns"):
            if subset is None:
                cols = self.columns
            else:
                cols = [c for c in self.columns if c in subset]
            return SQL(",").join([Identifier(col) for col in cols])
        raise ValueError("No columns defined")

    def select_all(self):
        return SQL("SELECT {fields} FROM {table}").format(
            fields=self._columns(), table=self._table()
        )

    def select_where(self, key):
        where_clause = SQL(" WHERE {key} = %s").format(key=Identifier(key))
        return self.select_all() + where_clause

    def insert(self, subset=None):
        n_values = len(subset) if subset is not None else len(self.columns)
        return SQL("INSERT INTO {table} ({fields}) VALUES ({values})").format(
            table=self._table(),
            fields=self._columns(subset),
            values=SQL(",").join(Placeholder() * n_values),
        )

    def delete(self, key):
        return SQL("DELETE FROM {table} WHERE {key} = %s").format(
            table=self._table(), key=Identifier(key)
        )

    def __enter__(self):
        self.conn.__enter__()
        self.cur = self.conn.cursor(cursor_factory=get_cursor_factory())
        self.cur.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.conn.__exit__(exc_type, exc_value, traceback)
        self.cur.__exit__(exc_type, exc_value, traceback)
        self.conn.close()

        if exc_type:
            raise SqlException("Exception during sql transaction.") from exc_value
