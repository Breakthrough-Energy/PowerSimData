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
        scenario_id = self._scenario_info["id"]
        _join = self._data_access.join

        input_dir = _join(*server_setup.INPUT_DIR, f"{scenario_id}_*")
        output_dir = _join(*server_setup.OUTPUT_DIR, f"{scenario_id}_*")
        tmp_dir = self._data_access.tmp_folder(scenario_id)

        proceed = True
        for target in (input_dir, output_dir, f"{ tmp_dir }/**"):
            if proceed:
                proceed = self._data_access.remove(target, confirm=confirm)

        if not proceed:
            print("Cancelling deletion.")
            return

        print("--> Deleting entries in scenario and execute list")
        self._scenario_list_manager.delete_entry(scenario_id)
        self._execute_list_manager.delete_entry(scenario_id)

        # Delete attributes
        self._clean()

    def _clean(self):
        """Clean after deletion."""
        self._scenario_info = None
