import posixpath

from powersimdata.scenario.helpers import interconnect2name
from powersimdata.scenario.state import State
from powersimdata.utility import server_setup


class Move(State):
    """Moves scenario.

    :param powersimdata.scenario.scenario.Scenario scenario: scenario instance.
    """

    name = "move"
    allowed = []

    def print_scenario_info(self):
        """Prints scenario information."""
        print("--------------------")
        print("SCENARIO INFORMATION")
        print("--------------------")
        for key, val in self._scenario_info.items():
            print("%s: %s" % (key, val))

    def move_scenario(self, target="disk"):
        """Move scenario.

        :param str target: optional argument specifying the backup system.
        """
        if not isinstance(target, str):
            raise TypeError("string is expected for optional argument target")

        if target != "disk":
            raise ValueError("scenario data can only be backed up to disk now")

        backup = BackUpDisk(self._data_access, self._scenario_info)

        backup.move_input_data()
        backup.copy_base_profile()
        backup.move_output_data()
        backup.move_temporary_folder()

        self._execute_list_manager.update_execute_list("moved", self._scenario_info)

        # Delete attributes
        self._clean()

    def _clean(self):
        """Clean after move."""
        self._data_access.close()


class BackUpDisk(object):
    """Back up scenario data to backup disk mounted on server.

    :param powersimdata.data_access.data_access.DataAccess data_access:
        data access object.
    :param dict scenario: scenario information.
    """

    def __init__(self, data_access, scenario_info):
        """Constructor."""
        self._data_access = data_access
        self._scenario_info = scenario_info
        self.backup_config = server_setup.PathConfig(server_setup.BACKUP_DATA_ROOT_DIR)
        self.server_config = server_setup.PathConfig(server_setup.DATA_ROOT_DIR)

    def move_input_data(self):
        """Moves input data."""
        print("--> Moving scenario input data to backup disk")
        source = posixpath.join(
            self.server_config.input_dir(),
            self._scenario_info["id"] + "_*",
        )
        target = self.backup_config.input_dir()
        self._data_access.copy(source, target, update=True)
        self._data_access.remove(source, recursive=True, force=True)

    def copy_base_profile(self):
        """Copies base profile"""
        print("--> Copying base profiles to backup disk")
        for kind in ["demand", "hydro", "solar", "wind"]:
            interconnect = interconnect2name(
                self._scenario_info["interconnect"].split("_")
            )
            version = self._scenario_info["base_" + kind]
            source = interconnect + "_" + kind + "_" + version + ".csv"

            src = posixpath.join(self.server_config.base_profile_dir(), source)
            dest = self.backup_config.base_profile_dir()
            _, stdout, stderr = self._data_access.copy(src, dest, update=True)
            print(stdout.readlines())
            print(stderr.readlines())

    def move_output_data(self):
        """Moves output data"""
        print("--> Moving scenario output data to backup disk")
        source = posixpath.join(
            self.server_config.output_dir(),
            self._scenario_info["id"] + "_*",
        )
        target = self.backup_config.output_dir()
        self._data_access.copy(source, target, update=True)
        self._data_access.remove(source, recursive=True, force=True)

    def move_temporary_folder(self):
        """Moves temporary folder."""
        print("--> Moving temporary folder to backup disk")
        source = posixpath.join(
            self.server_config.execute_dir(),
            "scenario_" + self._scenario_info["id"],
        )
        target = self.backup_config.execute_dir()
        self._data_access.copy(source, target, recursive=True, update=True)
        self._data_access.remove(source, recursive=True, force=True)
