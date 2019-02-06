import os
import pickle
import re

from postreise.process.transferdata import setup_server_connection
from powersimdata.scenario.helpers import interconnect2name
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

        :param str type: one of *'demand'*, *'hydro'*, *'solar'*, *'wind'*.
        :raises Exception: if no profile is available.
        """
        print("- %s profile" % type.capitalize())
        available = interconnect2name(self.interconnect) + '_' + type + '_*'
        query = os.path.join(self.remote_dir, available)
        stdin, stdout, stderr = self._ssh.exec_command("ls " + query)
        if len(stderr.readlines()) != 0:
            raise Exception("No %s file available." % type)
        else:
            filename = [os.path.basename(line.rstrip())
                        for line in stdout.readlines()]
            possible = [f[f.rfind('_')+1:-4] for f in filename]
            return input("Choose from [%s]: " % "/".join(possible))

    def _change_table_manager(self):
        """Deals with change table.

        :raises FileNotFoundError: if change table file not found.
        """
        print("- Change table")
        status = input("Do you need a change table? [Yes/No]: ")
        if status == 'No':
            print('Creating empty change table.')
            self.table = {'demand': None,
                          'hydro': None,
                          'solar': None,
                          'wind': None,
                          'branch': None}
        else:
            path = input("Enter absolute path to pickle file: ")
            try:
                table = pickle.load(open(path, "rb"))
            except FileNotFoundError as e:
                raise FileNotFoundError("File %s not found. " % path)
            if self._check_change_table(table):
                self.table = table

    def _check_change_table(self, table):
        """Creates change table.

        :param dict table: change table.
        :raises Exception: if keys in table are uncorrectly named, if \
            plant/branch id is not found.
        :return: (*bool*) -- true if change table has expected format and \
            information therein (zone id, plant id and branch id) are \
            consistent with resource and interconnect.
        """
        for type in table.keys():
            if type not in ['branch', 'demand', 'hydro', 'solar', 'wind']:
                raise Exception("Unknown key %s in change table" % possible)

        def check_zone(zone_id, id2name):
            """Checks zone.

            :param int zone_id: zone id.
            :param dict id2name: zone id to zone name.
            :raises Exception: if zone not found.
            """
            if zone_id not in id2name.keys():
                raise Exception('%d (%s) not in interconnect' %
                                (zone_id, id2name[zone_id]))
        for type in table.keys():
            for id in table[type].keys():
                if id == 'zone_id':
                    for zone_id in table[type]['zone_id'].keys():
                        check_zone(zone_id, self.grid.zone)
                if id == 'plant_id':
                    possible = self.grid.plant.groupby('type').get_group(
                        type).index
                    diff = set(table[type]['plant_id'].keys()) - set(possible)
                    if len(diff) != 0:
                        raise Exception("No %s plant with following id:" %
                            (type, "/".join(list(diff))))
                if id == 'branch_id':
                    possible = self.grid.branch.index
                    diff = set(table[type]['branch_id'].keys()) - set(possible)
                    if len(diff) != 0:
                        raise Exception("No %s branch with following id:" %
                            (type, "/".join(list(diff))))

        return True
