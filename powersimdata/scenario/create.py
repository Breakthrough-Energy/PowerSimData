from postreise.process import const
from postreise.process.transferdata import PullData
from postreise.process.transferdata import setup_server_connection
from powersimdata.scenario.state import State
from powersimdata.input.change_table import ChangeTable
from powersimdata.scenario.helpers import interconnect2name

from collections import OrderedDict

import os
import pickle


class Create(State):
    """Scenario is in a state of being created.

    """
    name = 'create'
    allowed = []

    def __init__(self, scenario):
        """Initializes attributes.

        """
        self.builder = None

        self._scenario_info = OrderedDict([
            ('plan', ''),
            ('name', ''),
            ('status', '0'),
            ('interconnect', ''),
            ('base_demand', ''),
            ('base_hydro', ''),
            ('base_solar', ''),
            ('base_wind', ''),
            ('change_table', 'No'),
            ('start_index', '0'),
            ('end_index', '60'),
            ('interval', '144H'),
            ('start_date', '2016-01-01 00:00:00'),
            ('end_date', '2016-12-31 23:00:00')])

    def _update_scenario_info(self):
        """Updates scenario information

        """
        if self.builder is not None:
            self._scenario_info['plan'] = self.builder.plan_name
            self._scenario_info['name'] = self.builder.scenario_name
            self._scenario_info['base_demand'] = self.builder.demand
            self._scenario_info['base_hydro'] = self.builder.hydro
            self._scenario_info['base_solar'] = self.builder.solar
            self._scenario_info['base_wind'] = self.builder.wind
            if bool(self.builder.change_table.ct):
                self._scenario_info['change_table'] = 'Yes'

    def create_scenario(self):
        """Creates entry in scenario file on server.

        """
        self._update_scenario_info()
        missing = []
        for key, val in self._scenario_info.items():
            if not val:
                missing.append(key)
        if len(missing) != 0:
            print("-------------------")
            print("MISSING INFORMATION")
            print("-------------------")
            for field in missing:
                print(field)
            return
        else:
            print("CREATING SCENARIO: %s | %s \n" %
                  (self._scenario_info['plan'], self._scenario_info['name']))

            # Update status
            self._scenario_info['status'] = '1'
            # Create entries that that will be filled out after execution
            self._scenario_info['runtime'] = ''
            self._scenario_info['infeasibilities'] = ''
            # Create scenario id
            td = PullData()
            table = td.get_scenario_table()
            self._scenario_info['id'] = str(table.id.max() + 1)
            self._scenario_info.move_to_end('id', last=False)

            # Update the scenario list
            print("--> Update scenario table on server")
            entry = ",".join(self._scenario_info.values())
            command = "echo %s >> %s" % (entry, const.SCENARIO_LIST_LOCATION)
            ssh = setup_server_connection()
            stdin, stdout, stderr = ssh.exec_command(command)
            if len(stderr.readlines()) != 0:
                print("Failed to update %s. Return." %
                      const.SCENARIO_LIST_LOCATION)
                return

            # Upload change table
            if bool(self.builder.change_table.ct):
                id = self._scenario_info['id']
                print("--> Write change table on local machine")
                self.builder.change_table.write(id)
                print("--> Upload change table to server")
                self.builder.change_table.push(id)
            # Create links
            print("--> Create links to base profiles on server \n")
            for p in ['demand', 'hydro', 'solar', 'wind']:
                version = self._scenario_info['base_' + p]
                self.builder.profile.create_link(id, p, version)

            print("SCENARIO SUCCESSFULLY CREATED WITH ID #%s" % id)
            self.allowed = ['execute']

    def print_scenario_info(self):
        """Prints scenario information

        """
        self._update_scenario_info()
        print("--------------------")
        print("SCENARIO INFORMATION")
        print("--------------------")
        for key, val in self._scenario_info.items():
            print("%s: %s" % (key, val))

    def set_builder(self, interconnect):
        """Sets interconnect object.

        :param object interconnect: interconnect object.
        """

        self.builder = interconnect
        print("")
        print("# Existing study")
        plan = [p for p in self.builder.existing.plan.unique()]
        print("%s \n" % " | ".join(plan))

        print("# Available profiles")
        for p in ['demand', 'hydro', 'solar', 'wind']:
            possible = self.builder.get_base_profile(p)
            if len(possible) != 0:
                print("%s: %s"  % (p, " | ".join(possible)))

        self._scenario_info['interconnect'] = self.builder.name


class Builder(object):
    """Scenario Builder

    """

    plan_name = ''
    scenario_name = ''
    demand = ''
    hydro = ''
    solar = ''
    wind = ''
    name = 'builder'

    def set_name(self, plan_name, scenario_name): pass

    def get_base_profile(self, type): pass

    def set_base_profile(self, type, version): pass

    def load_change_table(self, filename): pass

    def __str__(self):
        return self.name


class Eastern(Builder):
    """Builder for Eastern interconnect.

    """
    name = 'Eastern'

    def __init__(self):
        self.interconnect = ['Eastern']


class Texas(Builder):
    """Builder for Texas interconnect.

    """
    name = 'Texas'

    def __init__(self):
        self.interconnect = ['Texas']


class Western(Builder):
    """Builder for Western interconnect.

    """
    name = 'Western'

    def __init__(self):
        self.interconnect = ['Western']
        self.profile = CSV(self.interconnect)
        self.change_table = ChangeTable(self.interconnect)

        td = PullData()
        table = td.get_scenario_table()
        self.existing = table[table.interconnect == self.name]


    def set_name(self, plan_name, scenario_name):
        """Sets scenario name.

        :param str plan_name: plan name
        :param str scenario_name: scenario name.
        """

        if plan_name in self.existing.plan.tolist():
            scenario = self.existing[self.existing.plan == plan_name]
            if scenario_name in scenario.name.tolist():
                print('Combination %s - %s already exists' %
                      (plan_name, scenario_name))
                return
        self.plan_name = plan_name
        self.scenario_name = scenario_name


    def get_base_profile(self, type):
        """Get available base profiles.

        :param str type: one of *'demand'*, *'hydro'*, *'solar'*, *'wind'*.
        """
        return self.profile.get_base_profile(type)

    def set_base_profile(self, type, version):
        """Sets demand profile.

        :param str type: one of *'demand'*, *'hydro'*, *'solar'*, *'wind'*.
        :param str version: demand profile version.
        """
        possible = self.get_base_profile(type)
        if len(possible) == 0:
            return
        elif version in possible:
            if type == 'demand': self.demand = version
            if type == 'hydro': self.hydro = version
            if type == 'solar': self.solar = version
            if type == 'wind': self.wind = version
        else:
            print("Available %s profiles for %s: %s" %
                  (type, " + ".join(self.interconnect), " | ".join(possible)))
            return

    def load_change_table(self, filename):
        """Uploads change table.

        :param str filename: full path to change table pickle file.
        :raises FileNotFoundError: if file not found.
        """
        try:
            ct = pickle.load(open(filename, "rb"))
            self.change_table.ct = ct
        except FileNotFoundError as e:
            raise FileNotFoundError("File %s not found. " % filename)


class TexasWestern(Builder):
    """Builder for Texas + Western interconnect.

    """
    name = 'Texas_Western'

    def __init__(self):
        self.interconnect = ['Texas', 'Western']


class TexasEastern(Builder):
    """Builder for Texas + Eastern interconnect.

    """
    name = 'Texas_Eastern'

    def __init__(self):
        self.interconnect = ['Texas', 'Eastern']


class EasternWestern(Builder):
    """Builder for Eastern + Western interconnect.

    """
    name = 'Eastern_Western'

    def __init__(self):
        self.interconnect = ['Eastern', 'Western']


class USA(Builder):
    """Builder for USA interconnect.

    """
    name = 'USA'

    def __init__(self):
        self.interconnect = ['USA']


class CSV(object):
    """Profiles storage.

    """
    def __init__(self, interconnect):
        self._ssh = setup_server_connection()
        self.interconnect = interconnect

    def get_base_profile(self, type):
        """Get available base profiles.

        :param str type: one of *'demand'*, *'hydro'*, *'solar'*, *'wind'*.
        """
        possible = ['demand', 'hydro', 'solar', 'wind']
        if type not in possible:
            raise NameError("Choose from %s" % " | ".join(possible))

        available = interconnect2name(self.interconnect) + '_' + type + '_*'
        query = os.path.join(const.REMOTE_DIR_BASE, available)
        stdin, stdout, stderr = self._ssh.exec_command("ls " + query)
        if len(stderr.readlines()) != 0:
            print("No %s profiles available." % type)
            possible = []
        else:
            filename = [os.path.basename(line.rstrip())
                        for line in stdout.readlines()]
            possible = [f[f.rfind('_')+1:-4] for f in filename]
        return possible

    def create_link(self, id, type, version):
        """Creates link on server to base profile.

        :param str id: scenario id.
        :param str type: one of *'demand'*, *'hydro'*, *'solar'*, *'wind'*.
        :param str version: profile version.
        """
        interconnect = interconnect2name(self.interconnect)
        source = interconnect + '_' + type + '_' + version + '.csv'
        target = id + '_' + type + '.csv'

        command = "ln -s %s %s" % (const.REMOTE_DIR_BASE + '/' + source,
                                   const.REMOTE_DIR_INPUT + '/' + target)
        stdin, stdout, stderr = self._ssh.exec_command(command)
        if len(stderr.readlines()) != 0:
            print("Failed to create link to %s profile. Return." % type)
            return
