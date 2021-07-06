from powersimdata.data_access.data_access import get_ssh_fs
from powersimdata.scenario.state import State
from powersimdata.utility import server_setup


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
        self._fs = get_ssh_fs()

    def _move_data(self, kind, confirm=True):
        pattern = self._data_access.join(
            server_setup.DATA_ROOT_DIR, kind, f"{self.scenario_id}_*"
        )
        for m in self._fs.glob(pattern):
            dest = self._data_access.join(
                server_setup.BACKUP_DATA_ROOT_DIR, kind, m.info.name
            )
            self._fs.copy(m.path, dest)
            self._data_access.remove(m.path, confirm=confirm)

    def move_input_data(self, confirm=True):
        """Moves input data"""
        print("--> Moving scenario input data to backup disk")
        self._move_data(kind="data/input", confirm=confirm)

    def move_output_data(self, confirm=True):
        """Moves output data"""
        print("--> Moving scenario output data to backup disk")
        self._move_data(kind="data/output", confirm=confirm)

    def move_temporary_folder(self, confirm=True):
        """Moves temporary folder."""
        print("--> Moving temporary folder to backup disk")
        folder = self._data_access.match_scenario_files(self.scenario_id, "tmp")
        pattern = self._data_access.join(server_setup.DATA_ROOT_DIR, folder)
        for m in self._fs.glob(pattern):
            dest = self._data_access.join(
                server_setup.BACKUP_DATA_ROOT_DIR, folder, m.info.name
            )
            self._fs.copy(m.path, dest)
            self._data_access.remove(m.path, confirm=confirm)
