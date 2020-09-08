from powersimdata.data_access.csv_store import CsvStore
from powersimdata.data_access.sql_store import SqlStore, to_data_frame
from powersimdata.utility import server_setup


class ExecuteTable(SqlStore):
    """Storage abstraction for execute list using sql database."""

    table = "execute_list"
    columns = ["id", "status"]

    def get_status(self, scenario_id):
        """Get status of scenario by scenario_id

        :param str scenario_id: the scenario id
        :return: (*pandas.DataFrame*) -- results as a data frame.
        """
        query = self.select_where("id")
        self.cur.execute(query, (scenario_id,))
        result = self.cur.fetchmany()
        return to_data_frame(result)

    def get_execute_table(self, limit=None):
        """Return the execute table as a data frame

        :return: (*pandas.DataFrame*) -- execute list as a data frame.
        """
        query = self.select_all()
        self.cur.execute(query)
        if limit is None:
            result = self.cur.fetchall()
        else:
            result = self.cur.fetchmany(limit)
        return to_data_frame(result)

    def add_entry(self, scenario_info):
        """Add entry to execute list

        :param collections.OrderedDict scenario_info: entry to add
        """
        scenario_id, status = scenario_info["id"], "created"
        sql = self.insert()
        self.cur.execute(
            sql,
            (
                scenario_id,
                status,
            ),
        )

    def update_execute_list(self, status, scenario_info):
        """Updates status of scenario in execute list

        :param str status: execution status.
        :param collections.OrderedDict scenario_info: entry to update
        """
        self.cur.execute(
            "UPDATE execute_list SET status = %s WHERE id = %s",
            (status, scenario_info["id"]),
        )

    def delete_entry(self, scenario_info):
        """Deletes entry from execute list.

        :param collections.OrderedDict scenario_info: entry to delete
        """
        sql = self.delete("id")
        self.cur.execute(sql, (scenario_info["id"],))


class ExecuteListManager(CsvStore):
    """Storage abstraction for execute list using a csv file on the server.

    :param paramiko.client.SSHClient ssh_client: session with an SSH server.
    """

    def __init__(self, ssh_client):
        """Constructor"""
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
