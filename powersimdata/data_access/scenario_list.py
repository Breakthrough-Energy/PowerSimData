from powersimdata.data_access.csv_list_manager import CsvListManager
from powersimdata.utility import server_setup

import posixpath


class ScenarioListManager(CsvListManager):
    """This class is responsible for any modifications to the scenario list file.

    :param paramiko.client.SSHClient ssh_client: session with an SSH server.
    """

    def __init__(self, ssh_client):
        """Constructor

        """
        super().__init__(ssh_client)

    def get_scenario_table(self):
        """Returns scenario table from server if possible, otherwise read local
        copy. Updates the local copy upon successful server connection.

        :return: (*pandas.DataFrame*) -- scenario list as a data frame.
        """
        return self.get_table("ScenarioList.csv", server_setup.SCENARIO_LIST)

    def generate_scenario_id(self):
        """Generates scenario id.

        :return: (*str*) -- new scenario id.
        """
        print("--> Generating scenario id")
        command = (
            "(flock -e 200; \
                   id=$(awk -F',' 'END{print $1+1}' %s); \
                   echo $id, >> %s; \
                   echo $id) 200>%s"
            % (
                server_setup.SCENARIO_LIST,
                server_setup.SCENARIO_LIST,
                posixpath.join(server_setup.DATA_ROOT_DIR, "scenario.lockfile"),
            )
        )

        err_message = "Failed to generate id for new scenario"
        stdout = self._execute_and_check_err(command, err_message)
        scenario_id = stdout.readlines()[0].splitlines()[0]
        return scenario_id

    def add_entry(self, scenario_info):
        """Adds scenario to the scenario list file on server.

        :param collections.OrderedDict scenario_info: entry to add to scenario list.
        """
        print("--> Adding entry in %s on server" % server_setup.SCENARIO_LIST)
        entry = ",".join(scenario_info.values())
        options = "-F, -v INPLACE_SUFFIX=.bak -i inplace"
        # AWK parses the file line-by-line. When the entry of the first column is
        # equal to the scenario identification number, the entire line is replaced
        # by the scenaario information.
        program = "'{if($1==%s) $0=\"%s\"};1'" % (scenario_info["id"], entry,)
        command = "awk %s %s %s" % (options, program, server_setup.SCENARIO_LIST)

        err_message = "Failed to add entry in %s on server" % server_setup.SCENARIO_LIST
        _ = self._execute_and_check_err(command, err_message)

    def delete_entry(self, scenario_info):
        """Deletes entry in scenario list.

        :param collections.OrderedDict scenario_info: entry to delete from scenario list.
        """
        print("--> Deleting entry in %s on server" % server_setup.SCENARIO_LIST)
        entry = ",".join(scenario_info.values())
        command = "sed -i.bak '/%s/d' %s" % (entry, server_setup.SCENARIO_LIST)

        err_message = (
            "Failed to delete entry in %s on server" % server_setup.SCENARIO_LIST
        )
        _ = self._execute_and_check_err(command, err_messsage)
