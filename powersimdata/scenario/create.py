from postreise.process import const

from postreise.process.transferdata import PullData
from postreise.process.transferdata import setup_server_connection
from powersimdata.scenario.state import State
from powersimdata.input.change_table import ChangeTable
from powersimdata.scenario.helpers import interconnect2name

import os
import pandas as pd
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

        td = PullData()
        table = td.get_scenario_table()

        self._scenario_info = {'id': str(table.id.max() + 1),
                               'plan': '',
                               'name': '',
                               'status': '0',
                               'interconnect': '',
                               'base_demand': '',
                               'base_hydro': '',
                               'base_solar': '',
                               'base_wind': '',
                               'change_table': 'No',
                               'start_index': '0',
                               'end_index': '60',
                               'interval': '144H',
                               'start_date': pd.Timestamp(2016, 1, 1, 0),
                               'end_date': pd.Timestamp(2016, 12, 31, 23)}

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
            if bool(self.builder.ct):
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
            self._scenario_info['status'] = '1'
            print("SCENARIO: %s | %s \n" % (self._scenario_info['plan'],
                                            self._scenario_info['name']))

            print("--> Update scenario table")
            
            if bool(self.builder.ct):
                id = self._scenario_info['id']
                print("--> Write change table")
                self.builder.write(id)
                print("--> Upload change table")
                self.builder.push(id)
            print("--> Create links to base profiles")
            for p in ['demand', 'hydro', 'solar', 'wind']:
                version = self._scenario_info['base_' + p]
                self.builder.profile.create_link(id, p, version)
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
        print("--------------")
        print("EXISTING STUDY")
        print("--------------")
        for s in self.builder.existing.plan.unique():
            print(s)
        print("------------------")
        print("AVAILABLE PROFILES")
        print("------------------")
        for p in ['demand', 'hydro', 'solar', 'wind']:
            possible = self.builder.get_base_profile(p)
            if len(possible) != 0:
                print("%s: %s"  % (p, " | ".join(possible)))
        self._scenario_info['interconnect'] = "_".join(self.builder.interconnect)


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

    def link(self, id, type): pass

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


class Western(ChangeTable, Builder):
    """Builder for Western interconnect.

    """
    name = 'Western'

    def __init__(self):
        self.interconnect = ['Western']
        self.profile = CSV(self.interconnect)
        super().__init__(self.interconnect)

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
                print('Combination %s - %s already exists' % (plan_name,
                                                              scenario_name))
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
                  (type,
                   " + ".join(self.interconnect),
                   " | ".join(possible)))
            return

    def load_change_table(self, filename):
        """Uploads change table.

        :param str filename: full path to change table pickle file.
        :raises FileNotFoundError: if file not found.
        """
        try:
            ct = pickle.load(open(path, "rb"))
            self.ct = ct
        except FileNotFoundError as e:
            raise FileNotFoundError("File %s not found. " % path)


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
            print("Cannot create link to %s profile on server. Return." % type)
            return
