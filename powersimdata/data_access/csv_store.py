import os
from pathlib import Path

import pandas as pd

from powersimdata.utility import server_setup


class CsvStore:
    """Base class for common functionality used to manage scenario and execute
    list stored as csv files on the server

    :param paramiko.client.SSHClient ssh_client: session with an SSH server.
    """

    def __init__(self, ssh_client):
        """Constructor"""
        self.ssh_client = ssh_client
        if not os.path.exists(server_setup.LOCAL_DIR):
            os.makedirs(server_setup.LOCAL_DIR)

    def get_table(self, filename, path_on_server):
        """Read the given file from the server, falling back to local copy if
        unable to connect.

        :return: (*pandas.DataFrame*) -- the specified table as a data frame.
        """
        local_path = Path(server_setup.LOCAL_DIR, filename)

        try:
            table = self._get_from_server(path_on_server)
            table.to_csv(local_path, index=False)
        except Exception as e:
            print(f"Failed to download {filename} list from server. Error: {str(e)}")
            print("Falling back to local cache...")

        if local_path.is_file():
            return self._parse_csv(local_path)
        else:
            raise FileNotFoundError(f"{filename} does not exist locally.")

    def _get_from_server(self, path_on_server):
        """Return csv table from server.

        :return: (*pandas.DataFrame*) -- the specified file as a data frame.
        """
        with self.ssh_client.open_sftp() as sftp:
            file_object = sftp.file(path_on_server, "rb")
            return self._parse_csv(file_object)

    def _parse_csv(self, file_object):
        """Read file from disk into data frame

        :param str, path object or file-like object file_object: a reference to
        the csv file
        :return: (*pandas.DataFrame*) -- the specified file as a data frame.
        """
        table = pd.read_csv(file_object)
        table.fillna("", inplace=True)
        return table.astype(str)

    def _execute_and_check_err(self, command, err_message):
        """Executes command and checks for error.

        :param str command: command to execute over ssh.
        :param str err_message: error message to be raised.
        :raises IOError: if command is not successfully executed.
        :return: (*str*) -- standard output stream.
        """
        stdin, stdout, stderr = self.ssh_client.exec_command(command)
        if len(stderr.readlines()) != 0:
            raise IOError(err_message)
        return stdout
