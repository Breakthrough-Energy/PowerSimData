import os

import pandas as pd
import psycopg2
import psycopg2.extensions
import psycopg2.extras
from psycopg2.sql import SQL, Identifier, Placeholder


class SqlError(Exception):
    """To be raised by sql layer, enabling handling of data access errors."""

    pass


class LoggingCursor(psycopg2.extras.DictCursor):
    """Cursor that prints queries before execution. Primarily used for debugging"""

    def execute(self, sql, args=None):
        """Print sql query and delegate execution to super."""
        print(self.mogrify(sql, args))

        try:
            super().execute(sql, args)
        except Exception as exc:
            print("%s: %s" % (exc.__class__.__name__, exc))
            raise


def get_connection():
    """Temporary connection used for local development

    :return: (*str*) -- connection string for postgres db
    """
    return "dbname=psd host=localhost user=postgres password=example"


def get_cursor_factory():
    """Return cursor class to be passed to connection for executing sql.
    Default to DictCursor unless DEBUG_MODE is set.

    :returns: a cursor class callable for use by psycopg2 connection
    :rtype: psycopg2.extras.DictCursor or powersimdata.data_access.sql_store.LoggingCursor
    """
    if os.environ.get("DEBUG_MODE"):
        return LoggingCursor
    return psycopg2.extras.DictCursor


def to_data_frame(result):
    """Convert psycopg2 result set to data frame

    :param list result: list of DictRow containing query results cast to strings
    :return: (*pd.DataFrame*) -- query results as data frame
    """
    row_dicts = [{k: v for (k, v) in row.items()} for row in result]
    df = pd.DataFrame(row_dicts)
    df.fillna("", inplace=True)
    return df.astype(str)


class SqlStore:
    """Base class for objects stored in a postgres db. Implements context
    manager for connection handling and methods for generating queries based on
    convention. Derived classes should define table and columns attributes for
    this to work properly.
    """

    def __init__(self):
        self.conn = psycopg2.connect(get_connection())

    def _table(self):
        """Get table object for use in query generation.

        :return: (*psycopg2.sql.Identifier*) -- Identifier instance
        :raises ValueError: if :attr:`table` has not been defined.
        """
        if hasattr(self, "table"):
            return Identifier(self.table)
        raise ValueError("No table defined")

    def _columns(self, subset=None):
        """Get column list object for use in query generation.

        :return: (*psycopg2.sql.SQL*) -- SQL instance
        :raises ValueError: if :attr:`columns` has not been defined.
        """
        if hasattr(self, "columns"):
            if subset is None:
                cols = self.columns
            else:
                cols = [c for c in self.columns if c in subset]
            return SQL(",").join([Identifier(col) for col in cols])
        raise ValueError("No columns defined")

    def select_all(self):
        """Build SELECT query.

        :return: (*psycopg2.sql.SQL*) -- query representation
        """
        return SQL("SELECT {fields} FROM {table}").format(
            fields=self._columns(), table=self._table()
        )

    def select_where(self, key):
        """Build SELECT .. WHERE query filtered by key

        :param str key: column to use in WHERE clause
        :return: (*psycopg2.sql.SQL*) -- query representation
        """
        where_clause = SQL(" WHERE {key} = %s").format(key=Identifier(key))
        return self.select_all() + where_clause

    def insert(self, subset=None):
        """Build INSERT statement on current table for all columns, or subset if
        specified.

        :param iterable subset: collection of columns to specify in query
        :return: (*psycopg2.sql.SQL*) -- template for insert statement
        """
        n_values = len(subset) if subset is not None else len(self.columns)
        return SQL("INSERT INTO {table} ({fields}) VALUES ({values})").format(
            table=self._table(),
            fields=self._columns(subset),
            values=SQL(",").join(Placeholder() * n_values),
        )

    def delete(self, key):
        """Build DELETE .. WHERE statement on current table using key to filter.

        :param str key: column to use in WHERE clause
        :return: (*psycopg2.sql.SQL*) -- template for delete statement
        """
        return SQL("DELETE FROM {table} WHERE {key} = %s").format(
            table=self._table(), key=Identifier(key)
        )

    def __enter__(self):
        """Context manager entrypoint.

        :return: the current instance
        """
        self.conn.__enter__()
        self.cur = self.conn.cursor(cursor_factory=get_cursor_factory())
        self.cur.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Context manager teardown. Either commit or rollback transaction and
        close the connection. Reraise exception if applicable.

        :raises SqlException: If any exception occurred. Sets the original
        exception as the cause of the new one.
        """
        self.conn.__exit__(exc_type, exc_value, traceback)
        self.cur.__exit__(exc_type, exc_value, traceback)
        self.conn.close()

        if exc_type:
            raise SqlError("Exception during sql transaction.") from exc_value
