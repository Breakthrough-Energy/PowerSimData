import os
import posixpath

from powersimdata.data_access.data_access import LocalDataAccess
from powersimdata.scenario.state import State
from powersimdata.utility import server_setup


class Delete(State):
    """Deletes scenario."""

    name = "delete"
    allowed = []
    exported_methods = {
        "delete_scenario",
        "print_scenario_info",
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

        wildcard = f"{scenario_id}_*"

        # Delete links to base profiles on server
        print("--> Deleting scenario input data on server")
        target = posixpath.join(self.path_config.input_dir(), wildcard)
        self._data_access.remove(target, recursive=False, confirm=confirm)

        # Delete output profiles
        print("--> Deleting scenario output data on server")
        target = posixpath.join(self.path_config.output_dir(), wildcard)
        self._data_access.remove(target, recursive=False, confirm=confirm)

        # Delete temporary folder enclosing simulation inputs
        print("--> Deleting temporary folder on server")
        tmp_dir = posixpath.join(
            self.path_config.execute_dir(), f"scenario_{scenario_id}"
        )
        self._data_access.remove(tmp_dir, recursive=True, confirm=confirm)

        # Delete local files
        print("--> Deleting input and output data on local machine")
        target = os.path.join(server_setup.LOCAL_DIR, "data", "**", wildcard)
        LocalDataAccess().remove(target, recursive=True, confirm=confirm)

        # Delete attributes
        self._clean()

    def _clean(self):
        """Clean after deletion."""
        self._data_access.close()
        self._scenario_info = None
