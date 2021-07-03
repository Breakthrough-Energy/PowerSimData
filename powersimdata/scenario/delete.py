from powersimdata.data_access.data_access import LocalDataAccess
from powersimdata.scenario.state import State
from powersimdata.utility import server_setup


class Delete(State):
    """Deletes scenario."""

    name = "delete"
    allowed = []
    exported_methods = {
        "delete_scenario",
    }

    def print_scenario_info(self):
        """Prints scenario information.

        :raises AttributeError: if scenario has been deleted.
        """
        print("--------------------")
        print("SCENARIO INFORMATION")
        print("--------------------")
        try:
            for key, val in self._scenario_info.items():
                print("%s: %s" % (key, val))
        except AttributeError:
            print("Scenario has been deleted")

    def delete_scenario(self, confirm=True):
        """Deletes scenario on server.

        :param bool confirm: prompt before each batch
        """

        # Delete entry in scenario list
        scenario_id = self._scenario_info["id"]
        self._scenario_list_manager.delete_entry(scenario_id)
        self._execute_list_manager.delete_entry(scenario_id)

        print("--> Deleting scenario input data")
        target = self._data_access.match_scenario_files(scenario_id, "input")
        self._data_access.remove(target, confirm=confirm)

        print("--> Deleting scenario output data")
        target = self._data_access.match_scenario_files(scenario_id, "output")
        self._data_access.remove(target, confirm=confirm)

        # Delete temporary folder enclosing simulation inputs
        print("--> Deleting temporary folder")
        tmp_dir = self._data_access.match_scenario_files(scenario_id, "tmp")
        self._data_access.remove(tmp_dir, confirm=confirm)

        print("--> Deleting input and output data on local machine")
        local_data_access = LocalDataAccess()
        target = local_data_access.join(
            server_setup.LOCAL_DIR, "data", "**", f"{scenario_id}_*"
        )
        local_data_access.remove(target, confirm=confirm)

        # Delete attributes
        self._clean()

    def _clean(self):
        """Clean after deletion."""
        self._scenario_info = None
