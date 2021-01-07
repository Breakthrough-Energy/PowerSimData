from powersimdata.data_access.data_access import SSHDataAccess
from powersimdata.utility import server_setup


class Context:
    """Factory for data access instances"""

    @staticmethod
    def get_data_access(data_loc=None):
        """Return a data access instance appropriate for the current
        environment. Currently only supports internal client server mode.

        :param str data_loc: pass "disk" if using for backups otherwise leave
            the default and the behavior will be determined by environment
            variables
        """
        if data_loc == "disk":
            root = server_setup.BACKUP_DATA_ROOT_DIR
        else:
            root = server_setup.DATA_ROOT_DIR
        return SSHDataAccess(root)
