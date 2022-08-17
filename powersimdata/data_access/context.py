from powersimdata.data_access.data_access import LocalDataAccess, SSHDataAccess
from powersimdata.data_access.launcher import HttpLauncher, NativeLauncher, SSHLauncher
from powersimdata.utility import server_setup
from powersimdata.utility.config import DeploymentMode


class Context:
    """Factory for data access instances"""

    @staticmethod
    def get_data_access(make_fs=None):
        """Return a data access instance appropriate for the current
        environment.

        :param callable make_fs: a function that returns a filesystem instance, or
            None to use a default
        :return: (:class:`powersimdata.data_access.data_access.DataAccess`) -- a data access
            instance
        """
        if server_setup.DEPLOYMENT_MODE == DeploymentMode.Server:
            if make_fs is None:
                make_fs = lambda: None  # noqa: E731
            return SSHDataAccess(make_fs())
        return LocalDataAccess()

    @staticmethod
    def get_launcher(scenario):
        """Return instance for interaction with simulation engine

        :param powersimdata.scenario.scenario.Scenario scenario: a scenario object
        :return: (:class:`powersimdata.data_access.launcher.Launcher`) -- a launcher instance
        """
        mode = server_setup.DEPLOYMENT_MODE
        if mode == DeploymentMode.Server:
            return SSHLauncher(scenario)
        elif mode == DeploymentMode.Container:
            return HttpLauncher(scenario)
        return NativeLauncher(scenario)
