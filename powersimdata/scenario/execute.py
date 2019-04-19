from postreise.process import const
from postreise.process.transferdata import setup_server_connection
from postreise.process.transferdata import PullData
from powersimdata.input.grid import Grid
from powersimdata.scenario.state import State

from collections import OrderedDict


class Execute(State):
    """Scenario is in a state of being executed.

    """
    name = 'execute'
    allowed = ['stop']

    def __init__(self, scenario):
        """Initializes attributes.

        :param class scenario: scenario instance.
        """
        self._scenario_info = scenario._info
        self._scenario_status = scenario._status
        print("SCENARIO: %s | %s\n" % (self._scenario_info['plan'],
                                       self._scenario_info['name']))
        print("# Status\n--> %s\n" % self._scenario_status)

    def _update_scenario_status(self):
        """Updates scenario status.

        """
        td = PullData()
        table = td.get_execute_table()
        id = self._scenario_info['id']
        self._scenario_status = table[table.id == id].status.values[0]

    def print_scenario_info(self):
        """Prints scenario information.

        """
        print("--------------------")
        print("SCENARIO INFORMATION")
        print("--------------------")
        for key, val in self._scenario_info.items():
            print("%s: %s" % (key, val))

    def print_scenario_status(self):
        """Prints scenario status.

        """
        print("---------------")
        print("SCENARIO STATUS")
        print("---------------")
        self._update_scenario_status()
        print(self._scenario_status)

    def prepare_scenario(self):
        """Prepares scenario for execution

        """
        print("PREPARING SCENARIO:\n")
        self._update_execute_list('preparing')
        self._create_folder()


    def _create_folder(self):
        """Creates folder on server that will enclose simulation inputs.

        """
        print("--> Creating folder on server")
        dir = const.EXECUTE_DIR + '/scenario_' + self._scenario_info['id']
        command = "mkdir %s" % dir
        ssh = setup_server_connection()
        stdin, stdout, stderr = ssh.exec_command(command)
        if len(stderr.readlines()) != 0:
            raise IOError("Failed to create %s on server" % dir)

    def _update_execute_list(self, status):
        """Updates status in execute list file on server.

        :param str status: status.
        :raises IOError: if execute list file on server cannot be updated.
        """
        print("--> Updating status in execute table on server")
        options = "-F, -v OFS=',' -v INPLACE_SUFFIX=.bak -i inplace"
        program = ("'{for(i=1; i<=NF; i++){if($1==%s) $2=\"%s\"}};1'" %
                   (self._scenario_info['id'], status))
        command = "awk %s %s %s" % (options, program, const.EXECUTE_LIST)
        ssh = setup_server_connection()
        stdin, stdout, stderr = ssh.exec_command(command)
        if len(stderr.readlines()) != 0:
            raise IOError("Failed to update %s on server" % const.EXECUTE_LIST)

    def _copy_
