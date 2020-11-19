import os
import posixpath

from powersimdata.data_access.csv_store import CsvStore
from powersimdata.data_access.sql_store import SqlStore, to_data_frame
from powersimdata.utility import server_setup


class ScenarioTable(SqlStore):
    """Storage abstraction for scenario list using sql database."""

    table = "scenario_list"
    columns = [
        "id",
        "plan",
        "name",
        "state",
        "interconnect",
        "base_demand",
        "base_hydro",
        "base_solar",
        "base_wind",
        "change_table",
        "start_date",
        "end_date",
        "interval",
        "engine",
        "runtime",
        "infeasibilities",
    ]

    def get_scenario_by_id(self, scenario_id):
        """Get entry from scenario list by id

        :param str scenario_id: scenario id
        :return: (*pandas.DataFrame*) -- results as a data frame.
        """
        query = self.select_where("id")
        self.cur.execute(query, (scenario_id,))
        result = self.cur.fetchmany()
        return to_data_frame(result)

    def get_scenario_table(self, limit=None):
        """Returns scenario table from database

        :return: (*pandas.DataFrame*) -- scenario list as a data frame.
        """
        query = self.select_all()
        self.cur.execute(query)
        if limit is None:
            result = self.cur.fetchall()
        else:
            result = self.cur.fetchmany(limit)
        return to_data_frame(result)

    def add_entry(self, scenario_info):
        """Adds scenario to the scenario list.

        :param collections.OrderedDict scenario_info: entry to add to scenario list.
        """
        sql = self.insert(subset=scenario_info.keys())
        self.cur.execute(sql, tuple(scenario_info.values()))

    def delete_entry(self, scenario_info):
        """Deletes entry in scenario list.

        :param collections.OrderedDict scenario_info: entry to delete from scenario list.
        """
        sql = self.delete("id")
        self.cur.execute(sql, (scenario_info["id"],))


class ScenarioListManager(CsvStore):
    """Storage abstraction for scenario list using a csv file on the server.

    :param paramiko.client.SSHClient ssh_client: session with an SSH server.
    """

    def __init__(self, ssh_client):
        """Constructor"""
        super().__init__(ssh_client)

    def get_scenario_table(self):
        """Returns scenario table from server if possible, otherwise read local
        copy. Updates the local copy upon successful server connection.

        :return: (*pandas.DataFrame*) -- scenario list as a data frame.
        """
        return self.get_table(os.path.basename(server_setup.SCENARIO_LIST))

    def generate_scenario_id(self):
        """Generates scenario id.

        :return: (*str*) -- new scenario id.
        """
        print("--> Generating scenario id")
        command = "(flock -e 200; \
                   id=$(awk -F',' 'END{print $1+1}' %s); \
                   echo $id, >> %s; \
                   echo $id) 200>%s" % (
            server_setup.SCENARIO_LIST,
            server_setup.SCENARIO_LIST,
            posixpath.join(server_setup.DATA_ROOT_DIR, "scenario.lockfile"),
        )

        err_message = "Failed to generate id for new scenario"
        stdout = self._execute_and_check_err(command, err_message)
        scenario_id = stdout.readlines()[0].splitlines()[0]
        return scenario_id

    def add_entry(self, scenario_info):
        """Adds scenario to the scenario list file on server.

        :param collections.OrderedDict scenario_info: entry to add to scenario list.
        """
        print("--> Adding entry in %s on server" % server_setup.SCENARIO_LIST)
        entry = ",".join(scenario_info.values())
        options = "-F, -v INPLACE_SUFFIX=.bak -i inplace"
        # AWK parses the file line-by-line. When the entry of the first column is
        # equal to the scenario identification number, the entire line is replaced
        # by the scenaario information.
        program = "'{if($1==%s) $0=\"%s\"};1'" % (
            scenario_info["id"],
            entry,
        )
        command = "awk %s %s %s" % (options, program, server_setup.SCENARIO_LIST)

        err_message = "Failed to add entry in %s on server" % server_setup.SCENARIO_LIST
        _ = self._execute_and_check_err(command, err_message)

    def delete_entry(self, scenario_info):
        """Deletes entry in scenario list.

        :param collections.OrderedDict scenario_info: entry to delete from scenario list.
        """
        print("--> Deleting entry in %s on server" % server_setup.SCENARIO_LIST)
        entry = ",".join(scenario_info.values())
        command = "sed -i.bak '/%s/d' %s" % (entry, server_setup.SCENARIO_LIST)

        err_message = (
            "Failed to delete entry in %s on server" % server_setup.SCENARIO_LIST
        )
        _ = self._execute_and_check_err(command, err_message)
