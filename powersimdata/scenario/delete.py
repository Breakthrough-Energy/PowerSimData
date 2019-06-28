from postreise.process import const
from powersimdata.scenario.state import State


class Delete(State):
    """Deletes scenario.

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

        # Delete entry in scenario list
        print("--> Deleting entry in scenario table on server")
        entry = ",".join(self._scenario_info.values())
        command = "sed -i.bak '/%s/d' %s" % (entry, const.SCENARIO_LIST)
        stdin, stdout, stderr = self._ssh.exec_command(command)
        if len(stderr.readlines()) != 0:
            raise IOError("Failed to delete entry in %s on server" %
                          const.SCENARIO_LIST)

        # Delete entry in execute list
        print("--> Deleting entry in execute table on server")
        command = "sed -i.bak '/^%s,*/d' %s" % (self._scenario_info['id'],
                                                const.EXECUTE_LIST)
        stdin, stdout, stderr = self._ssh.exec_command(command)
        if len(stderr.readlines()) != 0:
            raise IOError("Failed to delete entry in %s on server" %
                          const.EXECUTE_LIST)

        # Delete links to base profiles on server
        print("--> Deleting scenario inputs on server")
        command = "rm -f %s/%s_*" % (const.INPUT_DIR, self._scenario_info['id'])
        stdin, stdout, stderr = self._ssh.exec_command(command)
        if len(stderr.readlines()) != 0:
            raise IOError("Failed to delete scenario inputs in %s on server" %
                          const.INPUT_DIR)

        # Delete output profiles
        print("--> Deleting scenario outputs on server")
        command = "rm -f %s/%s_*.csv" % (const.OUTPUT_DIR,
                                         self._scenario_info['id'])
        stdin, stdout, stderr = self._ssh.exec_command(command)
        if len(stderr.readlines()) != 0:
            raise IOError("Failed to delete scenario inputs in %s on server" %
                          const.OUTPUT_DIR)

        # Delete temporary folder enclosing simulation inputs
        print("--> Deleting temporary folder on server")
        tmp_dir = '%s/scenario_%s' % (const.EXECUTE_DIR,
                                      self._scenario_info['id'])
        command = "rm -rf %s" % tmp_dir
        stdin, stdout, stderr = self._ssh.exec_command(command)
        if len(stderr.readlines()) != 0:
            raise IOError("Failed to create %s on server" % tmp_dir)
