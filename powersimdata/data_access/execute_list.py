from powersimdata.utility import server_setup

from pathlib import Path
import pandas as pd


class ExecuteListManager:
    """This class is responsible for any modifications to the execute list file.

    :param paramiko.client.SSHClient ssh_client: session with an SSH server.
    """

    def __init__(self, ssh_client):
        """Constructor

        """
        self.ssh_client = ssh_client

    def get_execute_table(self):
        """Returns execute table from server.
        :return: (*pandas.DataFrame*) -- execute list as a data frame.
        """
        local_path = Path(server_setup.LOCAL_DIR, "ExecuteList.csv")

        try:
            execute_list = self._get_from_server()
            execute_list.to_csv(local_path, index=False)
            return execute_list
        except:
            print("Failed to download execute list from server.")
            print("Falling back to local cache...")

        if local_path.is_file():
            return self._parse_csv(local_path)

    def _get_from_server(self):
        """Return execute table from server.
        :return: (*pandas.DataFrame*) -- execute list as a data frame.
        """
        with self.ssh_client.open_sftp() as sftp:
            file_object = sftp.file(server_setup.EXECUTE_LIST, "rb")
            return self._parse_csv(file_object)

    def _parse_csv(self, file_object):
        """Read file from disk into data frame
        :param str, path object or file-like object file_object: a reference to
        the csv file
        :return: (*pandas.DataFrame*) -- execute list as a data frame.
        """
        table = pd.read_csv(file_object)
        table.fillna("", inplace=True)
        return table.astype(str)

    def add_entry(self, scenario_info):
        """Adds scenario to the execute list file on server.

        :param collections.OrderedDict scenario_info: entry to add
        """
        print("--> Adding entry in execute table on server")
        entry = "%s,created" % scenario_info["id"]
        command = "echo %s >> %s" % (entry, server_setup.EXECUTE_LIST)
        err_message = "Failed to update %s on server" % server_setup.EXECUTE_LIST
        _ = self._execute_and_check_err(command, err_message)

    def update_execute_list(self, status, scenario_info):
        """Updates status in execute list file on server.

        :param str status: execution status.
        :param collections.OrderedDict scenario_info: entry to update
        """
        print("--> Updating status in execute table on server")
        options = "-F, -v OFS=',' -v INPLACE_SUFFIX=.bak -i inplace"
        # AWK parses the file line-by-line. When the entry of the first column is equal
        # to the scenario identification number, the second column is replaced by the
        # status parameter.
        program = "'{if($1==%s) $2=\"%s\"};1'" % (scenario_info["id"], status)
        command = "awk %s %s %s" % (options, program, server_setup.EXECUTE_LIST)
        err_message = "Failed to update %s on server" % server_setup.EXECUTE_LIST
        _ = self._execute_and_check_err(command, err_message)

    def delete_entry(self, scenario_info):
        """Deletes entry from execute list on server.

        :param collections.OrderedDict scenario_info: entry to delete
        """
        print("--> Deleting entry in execute table on server")
        entry = "^%s,extracted" % scenario_info["id"]
        command = "sed -i.bak '/%s/d' %s" % (entry, server_setup.EXECUTE_LIST)
        err_message = (
            "Failed to delete entry in %s on server" % server_setup.EXECUTE_LIST
        )
        _ = self._execute_and_check_err(command, err_message)

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
