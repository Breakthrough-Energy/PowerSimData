import os
import posixpath
from collections import OrderedDict

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
        "grid_model",
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

    _SCENARIO_LIST = "ScenarioList.csv"

    def __init__(self, ssh_client):
        """Constructor"""
        super().__init__(ssh_client)
        self._server_path = posixpath.join(
            server_setup.DATA_ROOT_DIR, self._SCENARIO_LIST
        )

    def get_scenario_table(self):
        """Returns scenario table from server if possible, otherwise read local
        copy. Updates the local copy upon successful server connection.

        :return: (*pandas.DataFrame*) -- scenario list as a data frame.
        """
        return self.get_table(self._SCENARIO_LIST)

    def generate_scenario_id(self):
        """Generates scenario id.

        :return: (*str*) -- new scenario id.
        """
        table = self.get_table(self._SCENARIO_LIST)
        return str(table.index.max() + 1)

    def get_scenario(self, descriptor):
        """Get information for a scenario based on id or name

        :param int/str descriptor: the id or name of the scenario
        :return: (*collections.OrderedDict*) -- matching entry as a dict, or
            None if either zero or multiple matches found
        """

        def err_message(text):
            print("------------------")
            print(text)
            print("------------------")

        table = self.get_scenario_table()
        try:
            matches = table.index.isin([int(descriptor)])
        except ValueError:
            matches = table[table.name == descriptor].index

        scenario = table.loc[matches, :]
        if scenario.shape[0] == 0:
            err_message("SCENARIO NOT FOUND")
        elif scenario.shape[0] > 1:
            err_message("MULTIPLE SCENARIO FOUND")
            dupes = ",".join(str(i) for i in scenario.index)
            print(f"Duplicate ids: {dupes}")
            print("Use id to access scenario")
        else:
            return (
                scenario.reset_index()
                .astype({"id": "str"})
                .to_dict("records", into=OrderedDict)[0]
            )

    def _save_file(self, table):
        """Save to local directory

        :param pandas.DataFrame table: the scenario list data frame
        """
        table.to_csv(os.path.join(server_setup.LOCAL_DIR, self._SCENARIO_LIST))

    def add_entry(self, scenario_info):
        """Adds scenario to the scenario list file on server.

        :param collections.OrderedDict scenario_info: entry to add to scenario list.
        """
        table = self.get_table(self._SCENARIO_LIST)
        table.reset_index()
        table.append(scenario_info)
        self._save_file(table)

        print("--> Adding entry in %s on server" % self._SCENARIO_LIST)
        self.data_access.move_to(self._SCENARIO_LIST)

    def delete_entry(self, scenario_info):
        """Deletes entry in scenario list.

        :param collections.OrderedDict scenario_info: entry to delete from scenario list.
        """
        table = self.get_table(self._SCENARIO_LIST)
        scenario_id = int(scenario_info["id"])
        table.drop(scenario_id)
        self._save_file(table)

        print("--> Deleting entry in %s on server" % self._SCENARIO_LIST)
        self.data_access.move_to(self._SCENARIO_LIST)
