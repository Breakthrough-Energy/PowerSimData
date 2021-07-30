from fs.copy import copy_dir
from fs.errors import FSError
from fs.walk import Walker

from powersimdata.data_access.data_access import get_ssh_fs
from powersimdata.scenario.ready import Ready
from powersimdata.utility import server_setup
from powersimdata.utility.config import DeploymentMode


class Move(Ready):
    """Moves scenario.

    :param powersimdata.scenario.scenario.Scenario scenario: scenario instance.
    """

    name = "move"
    allowed = []
    exported_methods = {"move_scenario"} | Ready.exported_methods

    def move_scenario(self, target="disk", confirm=True):
        """Move scenario.

        :param str target: optional argument specifying the backup system.
        :param bool confirm: prompt before deleting each batch of files
        :raises TypeError: if target is not a str
        :raises ValueError: if target is unknown (only "disk" is supported) or
            data not on server
        """
        if not isinstance(target, str):
            raise TypeError("string is expected for optional argument target")

        if target != "disk":
            raise ValueError("scenario data can only be backed up to disk now")

        if server_setup.DEPLOYMENT_MODE != DeploymentMode.Server:
            raise ValueError("move state only supported for scenario data on server.")

        scenario_id = self._scenario_info["id"]
        backup = BackUpDisk(self._data_access, scenario_id)
        backup.backup_scenario(confirm=confirm)

        self._execute_list_manager.set_status(scenario_id, "moved")


class BackUpDisk:
    """Back up scenario data to backup disk mounted on server.

    :param powersimdata.data_access.data_access.DataAccess data_access:
        data access object.
    :param str scenario_id: scenario id
    """

    def __init__(self, data_access, scenario_id):
        """Constructor."""
        self._data_access = data_access
        self.scenario_id = scenario_id
        self._join = data_access.join

    def backup_scenario(self, confirm=True):
        """Copy scenario data to backup disk and remove original

        :param bool confirm: prompt before deleting each batch of files
        """
        src_fs = dst_fs = get_ssh_fs()
        items = [
            (self._join(*server_setup.INPUT_DIR), f"{self.scenario_id}_*"),
            (self._join(*server_setup.OUTPUT_DIR), f"{self.scenario_id}_*"),
            (self._data_access.tmp_folder(self.scenario_id), "**"),
        ]
        for folder, pattern in items:
            print(f"--> Moving files matching {pattern} from {folder}")
            src_path = self._join(server_setup.DATA_ROOT_DIR, folder)
            dst_path = self._join(server_setup.BACKUP_DATA_ROOT_DIR, folder)
            walker = Walker(filter=[pattern])
            try:
                copy_dir(src_fs, src_path, dst_fs, dst_path, walker=walker)
            except FSError as e:
                print(f"Operation failed: {e}")

            self._data_access.remove(self._join(folder, pattern), confirm=confirm)
