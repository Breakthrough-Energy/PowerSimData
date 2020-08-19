from powersimdata.data_access.csv_store import CsvStore
from powersimdata.utility import server_setup

import psycopg2
import sys


def get_connection():
    return "dbname=psd user=postgres password=password1!"


class SqlStore:
    def __init__(self):
        self.conn = psycopg2.connect(get_connection())

    def __enter__(self):
        self.conn.__enter__()
        self.cur = self.conn.cursor()
        self.cur.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            print(sys.exc_info())

        self.conn.__exit__(exc_type, exc_value, traceback)
        self.cur.__exit__(exc_type, exc_value, traceback)
        self.conn.close()


class ExecuteTable(SqlStore):
    def get_status(self, scenario_id):
        self.cur.execute(
            "SELECT status from execute_list WHERE id = %s", (scenario_id,)
        )
        result = self.cur.fetchmany()
        return None if not any(result) else result[0]

    def get_execute_table(self, limit=None):
        self.cur.execute("SELECT id, status FROM execute_list")
        if limit is None:
            return self.cur.fetchall()
        return self.cur.fetchmany(limit)

    def add_entry(self, scenario_info):
        scenario_id, status = scenario_info["id"], "created"
        self.cur.execute(
            "INSERT INTO execute_list (id, status) VALUES (%s, %s)",
            (scenario_id, status),
        )

    def update_execute_list(self, status, scenario_info):
        self.cur.execute(
            "UPDATE execute_list SET status = %s WHERE id = %s",
            (status, scenario_info["id"]),
        )

    def delete_entry(self, scenario_info):
        self.cur.execute(
            "DELETE FROM execute_list WHERE id = %s", (scenario_info["id"],)
        )


class ExecuteListManager(CsvStore):
    """This class is responsible for any modifications to the execute list file.

    :param paramiko.client.SSHClient ssh_client: session with an SSH server.
    """

    def __init__(self, ssh_client):
        """Constructor

        """
        super().__init__(ssh_client)

    def get_execute_table(self):
        """Returns execute table from server if possible, otherwise read local
        copy. Updates the local copy upon successful server connection.
        :return: (*pandas.DataFrame*) -- execute list as a data frame.
        """
        return self.get_table("ExecuteList.csv", server_setup.EXECUTE_LIST)

    def add_entry(self, scenario_info):
        """Adds scenario to the execute list file on server.

        :param collections.OrderedDict scenario_info: entry to add
        """
        print("--> Adding entry in execute table on server")
        entry = "%s,created" % scenario_info["id"]
        command = "echo %s >> %s" % (entry, server_setup.EXECUTE_LIST)
        err_message = "Failed to update %s on server" % server_setup.EXECUTE_LIST
        _ = self._execute_and_check_err(command, err_message)

    def update_execute_list(self, status, scenario_info):
        """Updates status in execute list file on server.

        :param str status: execution status.
        :param collections.OrderedDict scenario_info: entry to update
        """
        print("--> Updating status in execute table on server")
        options = "-F, -v OFS=',' -v INPLACE_SUFFIX=.bak -i inplace"
        # AWK parses the file line-by-line. When the entry of the first column is equal
        # to the scenario identification number, the second column is replaced by the
        # status parameter.
        program = "'{if($1==%s) $2=\"%s\"};1'" % (scenario_info["id"], status)
        command = "awk %s %s %s" % (options, program, server_setup.EXECUTE_LIST)
        err_message = "Failed to update %s on server" % server_setup.EXECUTE_LIST
        _ = self._execute_and_check_err(command, err_message)

    def delete_entry(self, scenario_info):
        """Deletes entry from execute list on server.

        :param collections.OrderedDict scenario_info: entry to delete
        """
        print("--> Deleting entry in execute table on server")
        entry = "^%s,extracted" % scenario_info["id"]
        command = "sed -i.bak '/%s/d' %s" % (entry, server_setup.EXECUTE_LIST)
        err_message = (
            "Failed to delete entry in %s on server" % server_setup.EXECUTE_LIST
        )
        _ = self._execute_and_check_err(command, err_message)
