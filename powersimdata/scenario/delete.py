from postreise.process import const
from powersimdata.scenario.state import State
from postreise.process.transferdata import setup_server_connection


class Delete(State):
    """Deletes scenario

    """
    name = 'delete'
    allowed = ['create']

    def print_scenario_info(self):
        """Prints scenario information.

        """
        print("--------------------")
        print("SCENARIO INFORMATION")
        print("--------------------")
        for key, val in self._scenario_info.items():
            print("%s: %s" % (key, val))

    def delete_scenario(self):
        """Deletes scenario on server.

        """
        ssh = setup_server_connection()

        # Delete entry in scenario list
        print("--> Delete entry in scenario table on server")
        entry = ",".join(self._scenario_info.values())
        command = "sed -i.bak '/%s/d' %s" % (entry,
                                             const.SCENARIO_LIST)
        stdin, stdout, stderr = ssh.exec_command(command)
        if len(stderr.readlines()) != 0:
            print("Failed. Return.")
            return

        # Delete links to base profiles on server
        print("--> Delete scenario inputs on server")
        command = "rm -f %s/%s_*" % (const.INPUT_DIR,
                                     self._scenario_info['id'])
        stdin, stdout, stderr = ssh.exec_command(command)
        if len(stderr.readlines()) != 0:
            print("Failed. Return.")
            return

        # Delete output profiles
        print("--> Delete scenario outputs on server")
        command = "rm -f %s/%s_*.csv" % (const.OUTPUT_DIR,
                                         self._scenario_info['id'])
        stdin, stdout, stderr = ssh.exec_command(command)
        if len(stderr.readlines()) != 0:
            print("Failed. Return.")
            return
