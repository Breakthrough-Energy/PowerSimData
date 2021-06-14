from powersimdata.data_access.csv_store import CsvStore, verify_hash


class ExecuteListManager(CsvStore):
    """Storage abstraction for execute list using a csv file."""

    _FILE_NAME = "ExecuteList.csv"

    def get_execute_table(self):
        """Returns execute table from server if possible, otherwise read local
        copy. Updates the local copy upon successful server connection.

        :return: (*pandas.DataFrame*) -- execute list as a data frame.
        """
        return self.get_table()

    def get_status(self, scenario_id):
        """Return the status for the scenario

        :param str/int scenario_id: the scenario id
        :raises Exception: if scenario not found in execute list.
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

        print(f"--> Setting status={status} in execute list")
        return table

    @verify_hash
    def delete_entry(self, scenario_id):
        """Deletes entry from execute list.

        :param int/str scenario_id: the id of the scenario
        :return: (*pandas.DataFrame*) -- the updated data frame
        """
        table = self.get_execute_table()
        table.drop(int(scenario_id), inplace=True)

        print("--> Deleting entry in %s" % self._FILE_NAME)
        return table
