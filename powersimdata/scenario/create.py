from postreise.process import const

from postreise.process.transferdata import PullData
from postreise.process.transferdata import setup_server_connection
from powersimdata.scenario.state import State
from powersimdata.scenario.helpers import interconnect2name

import os
import pandas as pd


class Create(State):
    """Scenario is in a state of being created.

    """
    name = 'create'
    allowed = ['execute']

    def __init__(self, scenario):
        """Initializes attributes.

        """
        self.builder = None

        td = PullData()
        table = td.get_scenario_table()

        self._scenario_info = {'id': table.id.max() + 1,
                               'name': '',
                               'status': 0,
                               'interconnect': '',
                               'base_demand': '',
                               'base_hydro': '',
                               'base_solar': '',
                               'base_wind': '',
                               'change_table': 'No',
                               'start_index': 0,
                               'end_index': 60,
                               'interval': '144H',
                               'start_date': pd.Timestamp(2016, 1, 1, 0),
                               'end_date': pd.Timestamp(2016, 12, 31, 23)}

    def _update_scenario_info(self):
        """Updates scenario information

        """
        if self.builder is not None:
            self._scenario_info['base_demand'] = self.builder.demand
            self._scenario_info['base_hydro'] = self.builder.hydro
            self._scenario_info['base_solar'] = self.builder.solar
            self._scenario_info['base_wind'] = self.builder.wind
            if self.builder.ct is not None:
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
            print("Information that still need to be set:")
            for field in missing:
                print(field)
            return
        else:
            self._scenario_info['status'] = 1
            print('Update scenario list file on server')

    def print_scenario_info(self):
        """Prints scenario information

        """
        self._update_scenario_info()
        for key, val in self._scenario_info.items():
            print("%s: %s" % (key, val))

    def set_builder(self, interconnect):
        """Sets interconnect object.

        :param object interconnect: interconnect object.
        """

        self.builder = interconnect
        pick = self.builder.interconnect
        print("Available profiles for %s:" % " + ".join(pick))
        for p in ['demand', 'hydro', 'solar', 'wind']:
            possible = self.builder.get_base_profile(p)
            if len(possible) != 0:
                print("# %s: %s"  % (p, " | ".join(possible)))
        self._scenario_info['interconnect'] = "_".join(pick)


class Builder(object):
    """Scenario Builder

    """
    name = 'builder'

    def __init__(self):
        self.demand = ''
        self.hydro = ''
        self.solar = ''
        self.wind = ''
        self.ct = None

    def get_base_profile(self, type): pass

    def set_base_profile(self, type, version): pass

    def __str__(self):
        return self.name

class Eastern(Builder):
    """Builder for Eastern interconnect.

    """

    def __init__(self):
        self.interconnect = ['Eastern']


class Texas(Builder):
    """Builder for Texas interconnect.

    """

    def __init__(self):
        self.interconnect = ['Texas']


class Western(Builder):
    """Builder for Western interconnect.

    """
    name = 'Western'

    def __init__(self):
        super().__init__()
        self.interconnect = ['Western']
        self.profile = CSV()

    def get_base_profile(self, type):
        """Get available base profiles.

        :param str type: one of *'demand'*, *'hydro'*, *'solar'*, *'wind'*.
        """
        return self.profile.get_base_profile(self.interconnect, type)

    def set_base_profile(self, type, version):
        """Sets demand profile.

        :param str type: one of *'demand'*, *'hydro'*, *'solar'*, *'wind'*.
        :param str version: demand profile version.
        """
        possible = self.get_base_profile('demand')
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

class TexasWestern(Builder):
    """Builder for Texas + Western interconnect.

    """

    def __init__(self):
        self.interconnect = ['Texas', 'Western']


class TexasEastern(Builder):
    """Builder for Texas + Eastern interconnect.

    """

    def __init__(self):
        self.interconnect = ['Texas', 'Eastern']


class EasternWestern(Builder):
    """Builder for Eastern + Western interconnect.

    """

    def __init__(self):
        self.interconnect = ['Eastern', 'Western']


class USA(Builder):
    """Builder for USA interconnect.

    """

    def __init__(self):
        self.interconnect = ['USA']


class CSV(object):
    """Profiles storage.

    """
    def __init__(self):
        self._ssh = setup_server_connection()

    def get_base_profile(self, interconnect, type):
        """Get available base profiles.

        :param list interconnect: interconnect
        :param str type: one of *'demand'*, *'hydro'*, *'solar'*, *'wind'*.
        """
        possible = ['demand', 'hydro', 'solar', 'wind']
        if type not in possible:
            raise NameError("Choose from %s" % " | ".join(possible))

        available = interconnect2name(interconnect) + '_' + type + '_*'
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
