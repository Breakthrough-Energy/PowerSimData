from powersimdata.scenario import const

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

        self.scenario_info = {'id': table.id.max() + 1,
                      'name': '',
                      'status': '0',
                      'interconnect': '',
                      'base_demand': '',
                      'base_hydro': '',
                      'base_solar': '',
                      'base_wind': '',
                      'ct': '',
                      'start_index': '0',
                      'end_index': '60',
                      'interval': '144H',
                      'start_date': pd.Timestamp(2016, 1, 1, 0),
                      'end_date': pd.Timestamp(2016, 12, 31, 23)}

        self.interconnect = None
        self.demand = None
        self.hydro = None
        self.solar = None
        self.wind = None
        self.ct = None

    def create(self):
        """Creates entry in scenario file on server.

        """
        missing = []
        for key, val in self.scenario_info.items():
            if not val:
                missing.append(key)
        if len(missing) != 0:
            print("Information that still need to be set:")
            for field in missing:
                print(field)
            return
        else:
            self.scenario_info['status'] = '1'
            print('Update scenario list file on server')

    def print_scenario_info(self):
        """Prints scenario information

        """
        for key, val in self.scenario_info.items():
            print("%s: %s" % (key, val))

    def set_builder(self, interconnect):
        """Sets interconnect object.

        :param object interconnect: interconnect object.
        """

        self.builder = interconnect
        self.interconnect = self.builder.interconnect#get_interconnect()
        print("Available profiles for %s:" % " + ".join(self.interconnect))
        for p in ['demand', 'hydro', 'solar', 'wind']:
            possible = self.builder.get_base_profile(p)
            if len(possible) != 0:
                print("# %s: %s"  % (p, " | ".join(possible)))
        self.scenario_info['interconnect'] = "_".join(self.interconnect)

    def set_base_demand(self, demand):
        """Sets demand profile.

        :param str demand: demand profile version.
        """
        possible = self.builder.get_base_profile('demand')
        if len(possible) == 0:
            return
        elif demand in possible:
            self.demand = demand
            self.scenario_info['base_demand'] = demand
        else:
            print("Available demand profiles for %s: %s" %
                  (" + ".join(self.interconnect),
                   " | ".join(possible)))
            return

    def set_base_hydro(self, hydro):
        """Sets hydro profile.

        :param str hydro: hydro profile version.
        """
        possible = self.builder.get_base_profile('hydro')
        if len(possible) == 0:
            return
        elif hydro in possible:
            self.hydro = hydro
            self.scenario_info['base_hydro'] = hydro
        else:
            print("Available hydro profiles for %s: %s" %
                  (" + ".join(self.interconnect),
                   " | ".join(possible)))
            return

    def set_base_solar(self, solar):
        """Sets solar profile.

        :param str solar: solar profile version.
        """
        possible = self.builder.get_base_profile('solar')
        if len(possible) == 0:
            return
        elif solar in possible:
            self.solar = solar
            self.scenario_info['base_solar'] = solar
        else:
            print("Available solar profiles for %s: %s" %
                  (" + ".join(self.interconnect),
                   " | ".join(possible)))
            return

    def set_base_wind(self, wind):
        """Sets wind profile.

        :param str wind: wind profile version.
        """
        possible = self.builder.get_base_profile('wind')
        if len(possible) == 0:
            return
        elif wind in possible:
            self.wind = wind
            self.scenario_info['base_wind'] = wind
        else:
            print("Available wind profiles for %s: %s" %
                  (" + ".join(self.interconnect),
                   " | ".join(possible)))
            return


class Builder(object):
    name = 'builder'

    def get_interconnect(self): pass
    def get_base_profile(self, type): pass
    def set_base_demand(self): pass
    def __str__(self):
        return self.name

class Eastern(Builder):
    """Builder for Eastern interconnect.

    """

    def __init__(self):
        self.interconnect = ['Eastern']

    def get_interconnect(self):
        """Get list of interconnect.

        """
        return self.interconnect


class Texas(Builder):
    """Builder for Texas interconnect.

    """

    def __init__(self):
        self.interconnect = ['Texas']

    def get_interconnect(self):
        """Get list of interconnect.

        """
        return self.interconnect


class Western(Builder):
    """Builder for Western interconnect.

    """

    name = 'Western'

    def __init__(self):
        self.interconnect = ['Western']
        self.profile = CSV()

    def get_interconnect(self):
        """Get list of interconnect.

        """
        return self.interconnect

    def get_base_profile(self, type):
        """Get available base profiles.

        :param str type: one of *'demand'*, *'hydro'*, *'solar'*, *'wind'*.
        """
        return self.profile.get_base_profile(self.interconnect, type)

    def set_base_demand(self, version):
        """Sets demand profile.

        :param str version: demand profile version.
        """
        pass

class TexasWestern(Builder):
    """Builder for Texas + Western interconnect.

    """

    def __init__(self):
        self.interconnect = ['Texas', 'Western']

    def get_interconnect(self):
        """Get list of interconnect.

        """
        return self.interconnect


class TexasEastern(Builder):
    """Builder for Texas + Eastern interconnect.

    """

    def __init__(self):
        self.interconnect = ['Texas', 'Eastern']

    def get_interconnect(self):
        """Get name of interconnect.

        """
        return self.interconnect


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
