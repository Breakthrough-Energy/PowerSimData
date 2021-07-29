from powersimdata.data_access.data_access import LocalDataAccess
from powersimdata.scenario.ready import Ready
from powersimdata.utility import server_setup


class Delete(Ready):
    """Deletes scenario."""

    name = "delete"
    allowed = []
    exported_methods = {"delete_scenario"} | Ready.exported_methods

    def delete_scenario(self, confirm=True):
        """Deletes scenario on server.

        :param bool confirm: prompt before each batch
        """
        # Delete entry in scenario list
        scenario_id = self._scenario_info["id"]
        self._scenario_list_manager.delete_entry(scenario_id)
        self._execute_list_manager.delete_entry(scenario_id)

        print("--> Deleting scenario input data")
        target = self._data_access.join(*server_setup.INPUT_DIR, f"{scenario_id}_*")
        self._data_access.remove(target, confirm=confirm)

        print("--> Deleting scenario output data")
        target = self._data_access.join(*server_setup.OUTPUT_DIR, f"{scenario_id}_*")
        self._data_access.remove(target, confirm=confirm)

        # Delete temporary folder enclosing simulation inputs
        print("--> Deleting temporary folder")
        tmp_dir = self._data_access.tmp_folder(scenario_id)
        self._data_access.remove(f"{tmp_dir}/**", confirm=confirm)

        print("--> Deleting input and output data on local machine")
        local_data_access = LocalDataAccess()
        target = local_data_access.join("data", "**", f"{scenario_id}_*")
        local_data_access.remove(target, confirm=confirm)

        # Delete attributes
        self._clean()

    def _clean(self):
        """Clean after deletion."""
        self._scenario_info = None
