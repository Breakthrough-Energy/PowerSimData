from powersimdata.utility import server_setup

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
        sftp = self.ssh_client.open_sftp()

        file_object = sftp.file(server_setup.EXECUTE_LIST, "rb")
        execute_list = pd.read_csv(file_object)
        execute_list.fillna("", inplace=True)

        sftp.close()

        return execute_list.astype(str)

    def add_entry(self, scenario_info):
        """Adds scenario to the execute list file on server.

        :param collections.OrderedDict scenario_info: entry to add
        :raises IOError: if execute list file on server cannot be updated.
        """
        print("--> Adding entry in execute table on server\n")
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
        """Delete entry from execute list on server.

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
