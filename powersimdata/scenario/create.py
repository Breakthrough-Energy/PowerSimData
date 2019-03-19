from powersimdata.scenario import const

from postreise.process.transferdata import setup_server_connection
from powersimdata.scenario.state import State
from powersimdata.scenario.helpers import interconnect2name

import os


class Create(State):
    """Scenario is in a state of being created.

    """
    name = 'create'
    allowed = []

    def init(self, scenario):
        """Initializes attributes.

        """
        self._builder = None
        self._ssh = setup_server_connection()

    def clean(self):
        """Deletes attributes prior to switching state.

        """
        del self._builder
        del self._ssh
        del self.interconnect

    def set_interconnect(self, interconnect):
        """Sets interconnect object.

        :param object interconnect: interconnect object.
        """

        self._builder = interconnect
        self.interconnect = self._builder.get_interconnect()
        print("Available profiles for %s:" % " + ".join(self.interconnect))
        for p in ['demand', 'hydro', 'solar', 'wind']:
            possible = self._get_base_profile(p)
            if len(possible) != 0:
                print("# %s: %s"  % (p, " | ".join(possible)))

    def set_base_demand(self, demand):
        """Sets demand profile.

        :param str demand: demand profile version.
        """
        possible = self._get_base_profile('demand')
        if len(possible) == 0:
            self.demand = None
        elif demand in possible:
            self.demand = demand
        else:
            print("Available demand profiles for %s: %s" %
                  (" + ".join(self.interconnect),
                   " | ".join(possible)))
            self.demand = None

    def set_base_hydro(self, hydro):
        """Sets hydro profile.

        :param str hydro: hydro profile version.
        """
        possible = self._get_base_profile('hydro')
        if len(possible) == 0:
            self.hydro = None
        elif hydro in possible:
            self.hydro = hydro
        else:
            print("Available hydro profiles for %s: %s" %
                  (" + ".join(self.interconnect),
                   " | ".join(possible)))
            self.hydro = None

    def set_base_solar(self, solar):
        """Sets solar profile.

        :param str solar: solar profile version.
        """
        possible = self._get_base_profile('solar')
        if len(possible) == 0:
            self.solar = None
        elif solar in possible:
            self.solar = solar
        else:
            print("Available solar profiles for %s: %s" %
                  (" + ".join(self.interconnect),
                   " | ".join(possible)))
            self.solar = None

    def set_base_wind(self, wind):
        """Sets wind profile.

        :param str wind: wind profile version.
        """
        possible = self._get_base_profile('wind')
        if len(possible) == 0:
            self.wind = None
        elif wind in possible:
            self.wind = wind
        else:
            print("Available wind profiles for %s: %s" %
                  (" + ".join(self.interconnect),
                   " | ".join(possible)))
            self.wind = None

    def _get_base_profile(self, type):
        """Prints available base profiles.

        :param str type: one of *'demand'*, *'hydro'*, *'solar'*, *'wind'*.
        :raises NameError: if wrong type.
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


class Builder(object):
    def get_interconnect(self): pass


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

    def __init__(self):
        self.interconnect = ['Western']

    def get_interconnect(self):
        """Get list of interconnect.

        """
        return self.interconnect


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
