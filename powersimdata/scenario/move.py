from powersimdata.scenario.state import State


class Move(State):
    """Moves scenario.

    :param powersimdata.scenario.scenario.Scenario scenario: scenario instance.
    """

    name = "move"
    allowed = []
    exported_methods = {
        "move_scenario",
    }

    def print_scenario_info(self):
        """Prints scenario information."""
        print("--------------------")
        print("SCENARIO INFORMATION")
        print("--------------------")
        for key, val in self._scenario_info.items():
            print("%s: %s" % (key, val))

    def move_scenario(self, target="disk", confirm=True):
        """Move scenario.

        :param str target: optional argument specifying the backup system.
        :param bool confirm: prompt before deleting each batch of files
        :raises TypeError: if target is not a str
        :raises ValueError: if target is unknown (only "disk" is supported)
        """
        if not isinstance(target, str):
            raise TypeError("string is expected for optional argument target")

        if target != "disk":
            raise ValueError("scenario data can only be backed up to disk now")

        backup = BackUpDisk(self._data_access, self._scenario_info)

        backup.move_input_data(confirm=confirm)
        backup.move_output_data(confirm=confirm)
        backup.move_temporary_folder(confirm=confirm)

        sid = self._scenario_info["id"]
        self._execute_list_manager.set_status(sid, "moved")

        # Delete attributes
        self._clean()

    def _clean(self):
        """Clean after move."""
        self._data_access.close()


class BackUpDisk:
    """Back up scenario data to backup disk mounted on server.

    :param powersimdata.data_access.data_access.DataAccess data_access:
        data access object.
    :param dict scenario_info: scenario information.
    """

    def __init__(self, data_access, scenario_info):
        """Constructor."""
        self._data_access = data_access
        self._scenario_info = scenario_info
        self.scenario_id = self._scenario_info["id"]

    def move_input_data(self, confirm=True):
        """Moves input data."""
        print("--> Moving scenario input data to backup disk")
        source = self._data_access.match_scenario_files(self.scenario_id, "input")
        target = self._data_access.get_base_dir("input", backup=True)
        self._data_access.copy(source, target)
        self._data_access.remove(source, recursive=False, confirm=confirm)

    def move_output_data(self, confirm=True):
        """Moves output data"""
        print("--> Moving scenario output data to backup disk")
        source = self._data_access.match_scenario_files(self.scenario_id, "output")
        target = self._data_access.get_base_dir("output", backup=True)
        self._data_access.copy(source, target)
        self._data_access.remove(source, recursive=False, confirm=confirm)

    def move_temporary_folder(self, confirm=True):
        """Moves temporary folder."""
        print("--> Moving temporary folder to backup disk")
        source = self._data_access.match_scenario_files(self.scenario_id, "tmp")
        target = self._data_access.get_base_dir("tmp", backup=True)
        self._data_access.copy(source, target, recursive=True)
        self._data_access.remove(source, recursive=True, confirm=confirm)
