import glob
import os
import posixpath

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

    def delete_scenario(self):
        """Deletes scenario on server."""

        # Delete entry in scenario list
        scenario_id = self._scenario_info["id"]
        self._scenario_list_manager.delete_entry(scenario_id)
        self._execute_list_manager.delete_entry(scenario_id)

        wildcard = f"{scenario_id}_*"

        # Delete links to base profiles on server
        print("--> Deleting scenario input data on server")
        target = posixpath.join(self.path_config.input_dir(), wildcard)
        _, _, stderr = self._data_access.remove(target, recursive=False, force=True)
        if len(stderr.readlines()) != 0:
            raise IOError("Failed to delete scenario input data on server")

        # Delete output profiles
        print("--> Deleting scenario output data on server")
        target = posixpath.join(self.path_config.output_dir(), wildcard)
        _, _, stderr = self._data_access.remove(target, recursive=False, force=True)
        if len(stderr.readlines()) != 0:
            raise IOError("Failed to delete scenario output data on server")

        # Delete temporary folder enclosing simulation inputs
        print("--> Deleting temporary folder on server")
        tmp_dir = posixpath.join(
            self.path_config.execute_dir(), f"scenario_{scenario_id}"
        )
        _, _, stderr = self._data_access.remove(tmp_dir, recursive=True, force=True)
        if len(stderr.readlines()) != 0:
            raise IOError("Failed to delete temporary folder on server")

        # Delete local files
        print("--> Deleting input and output data on local machine")
        local_file = glob.glob(
            os.path.join(server_setup.LOCAL_DIR, "data", "**", wildcard)
        )
        for f in local_file:
            os.remove(f)

        # Delete attributes
        self._clean()

    def _clean(self):
        """Clean after deletion."""
        self._data_access.close()
        self._scenario_info = None
