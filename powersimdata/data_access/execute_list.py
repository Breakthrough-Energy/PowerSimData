import posixpath

from powersimdata.data_access.csv_store import CsvStore, verify_hash
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

    def set_status(self, scenario_id, status):
        """Updates status of scenario in execute list

        :param int scenario_id: the scenario id
        :param str status: execution status.
        """
        self.cur.execute(
            "UPDATE execute_list SET status = %s WHERE id = %s",
            (status, scenario_id),
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

    _FILE_NAME = "ExecuteList.csv"

    def __init__(self, ssh_client):
        """Constructor"""
        super().__init__(ssh_client)
        self._server_path = posixpath.join(server_setup.DATA_ROOT_DIR, self._FILE_NAME)

    def get_execute_table(self):
        """Returns execute table from server if possible, otherwise read local
        copy. Updates the local copy upon successful server connection.

        :return: (*pandas.DataFrame*) -- execute list as a data frame.
        """
        return self.get_table()

    def get_status(self, scenario_id):
        """Return the status for the scenario

        :param str/int scenario_id: the scenario id
        :raises Exception: if scenario not found in execute list on server.
        :return: (*str*) -- scenario status
        """
        table = self.get_execute_table()
        try:
            return table.loc[int(scenario_id), "status"]
        except KeyError:
            raise Exception(f"Scenario not found in execute list, id = {scenario_id}")

    def add_entry(self, scenario_info):
        """Add entry to execute list

        :param collections.OrderedDict scenario_info: entry to add
        """
        scenario_id = int(scenario_info["id"])
        return self.set_status(scenario_id, "created")

    @verify_hash
    def set_status(self, scenario_id, status):
        """Set the scenario status

        :param int/str scenario_id: the scenario id
        :param str status: the new status
        :return: (*pandas.DataFrame*) -- the updated data frame
        """
        table = self.get_execute_table()
        table.loc[int(scenario_id), "status"] = status

        print(f"-->  Setting status={status} in execute table on server")
        return table

    @verify_hash
    def delete_entry(self, scenario_info):
        """Deletes entry from execute list on server.

        :param collections.OrderedDict scenario_info: entry to delete
        :return: (*pandas.DataFrame*) -- the updated data frame
        """
        table = self.get_execute_table()
        scenario_id = int(scenario_info["id"])
        table.drop(scenario_id, inplace=True)

        print("--> Deleting entry in execute table on server")
        return table
