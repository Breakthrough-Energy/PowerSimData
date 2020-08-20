import psycopg2
import psycopg2.extensions
import logging
from psycopg2.sql import SQL, Identifier, Placeholder
import sys


class SqlException(Exception):
    pass


class LoggingCursor(psycopg2.extensions.cursor):
    def execute(self, sql, args=None):
        logger = logging.getLogger("sql_debug")
        logger.info(self.mogrify(sql, args))

        try:
            psycopg2.extensions.cursor.execute(self, sql, args)
        except Exception as exc:
            logger.error("%s: %s" % (exc.__class__.__name__, exc))
            raise


def get_connection():
    return "dbname=psd host=localhost user=postgres password=example"


class SqlStore:
    def __init__(self):
        self.conn = psycopg2.connect(get_connection())

    def _table(self):
        if hasattr(self, "table"):
            return Identifier(self.table)
        raise ValueError("No table defined")

    def _columns(self):
        if hasattr(self, "columns"):
            return SQL(",").join([Identifier(col) for col in self.columns])
        raise ValueError("No columns defined")

    def select_all(self):
        return SQL("SELECT {fields} FROM {table}").format(
            fields=self._columns(), table=self._table()
        )

    def select_where(self, key):
        where_clause = SQL("WHERE {key} = %s").format(key=Identifier(key))
        return self.select_all() + where_clause

    def insert(self):
        return SQL("INSERT INTO {table} ({fields}) VALUES ({values})").format(
            table=self._table(),
            fields=self._columns(),
            values=SQL(",").join(Placeholder() * len(self.columns)),
        )

    def delete(self, key):
        return SQL("DELETE FROM {table} WHERE {key} = %s").format(
            table=self._table(), key=Identifier(key)
        )

    def __enter__(self):
        self.conn.__enter__()
        self.cur = self.conn.cursor()
        self.cur.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.conn.__exit__(exc_type, exc_value, traceback)
        self.cur.__exit__(exc_type, exc_value, traceback)
        self.conn.close()

        if exc_type:
            raise SqlException("Exception during sql transaction.") from exc_value
