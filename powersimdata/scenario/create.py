import os
import pickle
import re

from postreise.process.transferdata import setup_server_connection
import powersimdata.scenario.helpers as helpers
from powersimdata.input.grid import Grid

class Scenario:

    def __init__(self, name):
        self.name = name


class Create(Scenario):
    """Create scenario

    """

    def __init__(self, name):
        """Constructor

        """
        super().__init__(name)

        # Server access
        print("Connecting to server")
        self._ssh = setup_server_connection()
        self.remote_dir = "/home/EGM/v2/raw"

        # Interconnect
        self.interconnect = self._select_interconnect()
        self.grid = Grid(self.interconnect)

        # Base profiles
        self.demand = self._select_base_profile('demand')
        self.hydro = self._select_base_profile('hydro')
        self.solar = self._select_base_profile('solar')
        self.wind = self._select_base_profile('wind')

        # Create change table
        self._change_table_manager()

    def _select_interconnect(self):
        """Selects interconnect.

        """
        print("- Interconnect")
        interconnect = input("Choose from [Eastern/Texas/Western/USA]: ")
        interconnect = re.sub('[\s+]', '', interconnect)
        interconnect = re.split(r'[`\-=~!@#$%^&*()_+\[\]{};\'\\:"|<,./<>?]',
                                interconnect)
        return interconnect

    def _select_base_profile(self, type):
        """Selects base profile.

        :param str type: one of *'demand'*, *'hydro'*, *'solar'*, *'wind'*
        """
        print("- %s profile" % type.capitalize())
        file = helpers.interconnect2name(self.interconnect) + '_' + type + '_*'
        query = os.path.join(self.remote_dir, file)
        stdin, stdout, stderr = self._ssh.exec_command("ls " + query)
        if len(stderr.readlines()) != 0:
            print("No %s file available for selected interconnect." % type)
            return
        else:
            possible = [os.path.basename(line.rstrip())[-6:-4]
                        for line in stdout.readlines()]
            return input("Choose from [%s]: " % "/".join(possible))

    def _change_table_manager(self):
        """Deals with change table.

        """
        print("- Change table")
        status = input("Do you need a change table? [Yes/No]: ")
        if status == 'No':
            print('Creating empty change table.')
            self.table = {'demand': None,
                          'hydro': None,
                          'solar': None,
                          'wind': None}
        else:
            file = input("Do you have a change table file? [Yes/No]: ")
            if file == 'Yes':
                path = input("Enter absolute path to pickle file: ")
                try:
                    table = pickle.load(open(path, "rb"))
                except FileNotFoundError as e:
                    raise FileNotFoundError("File %s not found. " % path)
                if self._check_change_table(table):
                    self.table = table
            else:
                print("Let's create a change table")


    def _check_change_table(self, table):
        """Creates change table.

        :param dict table: change table.
        """
        return True
