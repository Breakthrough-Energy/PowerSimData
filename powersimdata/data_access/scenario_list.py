from powersimdata.utility import const

import pandas as pd
import paramiko
import posixpath


class ScenarioListManager:
    """
    This class is responsible for any modifications to the scenario list.
    """

    def __init__(self, ssh_client):
        self.ssh_client = ssh_client

    def get_scenario_table(self):
        """Returns scenario table from server.

        :param paramiko.client.SSHClient ssh_client: session with an SSH server.
        :return: (*pandas.DataFrame*) -- scenario list as a data frame.
        """
        sftp = self.ssh_client.open_sftp()
        file_object = sftp.file(const.SCENARIO_LIST, "rb")

        scenario_list = pd.read_csv(file_object)
        scenario_list.fillna("", inplace=True)

        sftp.close()

        return scenario_list.astype(str)

    def generate_scenario_id(self):
        """Generates scenario id.
        :return: (*str*) -- New scenario id.
        """
        print("--> Generating scenario id")
        script = (
            "(flock -e 200; \
                   id=$(awk -F',' 'END{print $1+1}' %s); \
                   echo $id, >> %s; \
                   echo $id) 200>%s"
            % (
                const.SCENARIO_LIST,
                const.SCENARIO_LIST,
                posixpath.join(const.DATA_ROOT_DIR, "scenario.lockfile"),
            )
        )

        stdin, stdout, stderr = self.ssh_client.exec_command(script)
        err_message = stderr.readlines()
        if err_message:
            raise IOError(err_message[0].strip())

        scenario_id = stdout.readlines()[0].splitlines()[0]
        return scenario_id

    def add_entry(self, scenario_info):
        """Adds scenario to the scenario list file on server.

        :param (*collections.OrderedDict*) scenario_info: Entry to add to scenario list
        :raises IOError: if scenario list file on server cannot be updated.
        """
        print("--> Adding entry in scenario table on server")
        entry = ",".join(scenario_info.values())
        options = "-F, -v INPLACE_SUFFIX=.bak -i inplace"
        # AWK parses the file line-by-line. When the entry of the first column is
        # equal to the scenario identification number, the entire line is replaced
        # by the scenaario information.
        program = "'{if($1==%s) $0=\"%s\"};1'" % (scenario_info["id"], entry,)
        command = "awk %s %s %s" % (options, program, const.SCENARIO_LIST)

        self._execute_and_check_err(command)

    def delete_entry(self, scenario_info):
        """ Delete entry in scenario list
        :param (*collections.OrderedDict*) scenario_info: Entry to delete from scenario list
        :raises IOError: if scenario list file on server cannot be updated.
        """
        print("--> Deleting entry in scenario table on server")
        entry = ",".join(scenario_info.values())
        command = "sed -i.bak '/%s/d' %s" % (entry, const.SCENARIO_LIST)

        self._execute_and_check_err(command)

    def _execute_and_check_err(self, command):
        """
        :param (*str*) command: command to execute over ssh
        """
        _, _, stderr = self.ssh_client.exec_command(command)
        if len(stderr.readlines()) != 0:
            raise IOError(
                "Failed to delete entry in %s on server" % const.SCENARIO_LIST
            )
