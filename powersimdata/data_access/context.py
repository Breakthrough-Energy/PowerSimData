from powersimdata.utility import server_setup
from powersimdata.utility.transfer_data import SSHDataAccess


class Context:
    @staticmethod
    def get_data_access(data_loc=None):
        if data_loc == "disk":
            root = server_setup.BACKUP_DATA_ROOT_DIR
        else:
            root = server_setup.DATA_ROOT_DIR
        return SSHDataAccess(root)
