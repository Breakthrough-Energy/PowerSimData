from collections import OrderedDict

import pandas as pd

from powersimdata.data_access.csv_store import CsvStore, verify_hash


class ScenarioListManager(CsvStore):
    """Storage abstraction for scenario list using a csv file."""

    _FILE_NAME = "ScenarioList.csv"

    def get_scenario_table(self):
        """Returns scenario table from server if possible, otherwise read local
        copy. Updates the local copy upon successful server connection.

        :return: (*pandas.DataFrame*) -- scenario list as a data frame.
        """
        return self.get_table()

    def _generate_scenario_id(self, table):
        """Generates scenario id.

        :param pandas.DataFrame table: the current scenario list
        :return: (*str*) -- new scenario id.
        """
        max_value = table.index.max()
        result = 1 if pd.isna(max_value) else max_value + 1
        return str(result)

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

    @verify_hash
    def add_entry(self, scenario_info):
        """Adds scenario to the scenario list file.

        :param collections.OrderedDict scenario_info: entry to add to scenario list.
        :return: (*pandas.DataFrame*) -- the updated data frame
        """
        table = self.get_scenario_table()
        scenario_id = self._generate_scenario_id(table)
        scenario_info["id"] = scenario_id
        scenario_info.move_to_end("id", last=False)
        table.reset_index(inplace=True)
        entry = pd.DataFrame({k: [v] for k, v in scenario_info.items()})
        table = table.append(entry)
        table.set_index("id", inplace=True)

        print("--> Adding entry in %s" % self._FILE_NAME)
        return table

    @verify_hash
    def delete_entry(self, scenario_id):
        """Deletes entry in scenario list.

        :param int/str scenario_id: the id of the scenario
        :return: (*pandas.DataFrame*) -- the updated data frame
        """
        table = self.get_scenario_table()
        table.drop(int(scenario_id), inplace=True)

        print("--> Deleting entry in %s" % self._FILE_NAME)
        return table
