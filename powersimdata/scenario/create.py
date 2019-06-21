from postreise.process import const
from postreise.process.transferdata import get_scenario_table
from postreise.process.transferdata import setup_server_connection
from postreise.process.transferdata import upload
from powersimdata.scenario.state import State
from powersimdata.scenario.execute import Execute
from powersimdata.input.change_table import ChangeTable
from powersimdata.scenario.helpers import interconnect2name, check_interconnect


import os
import numpy as np
import pandas as pd
import pickle
from collections import OrderedDict


class Create(State):
    """Scenario is in a state of being created.

    """
    name = 'create'
    allowed = []

    def __init__(self, scenario):
        """Initializes attributes.

        :param Scenario scenario: scenario instance.
        """
        self.builder = None
        self._scenario_status = None
        self._scenario_info = OrderedDict([
            ('plan', ''),
            ('name', ''),
            ('state', 'create'),
            ('interconnect', ''),
            ('base_demand', ''),
            ('base_hydro', ''),
            ('base_solar', ''),
            ('base_wind', ''),
            ('change_table', ''),
            ('start_date', ''),
            ('end_date', ''),
            ('interval', '')])
        self._ssh = scenario._ssh

    def _update_scenario_info(self):
        """Updates scenario information

        """
        if self.builder is not None:
            self._scenario_info['plan'] = self.builder.plan_name
            self._scenario_info['name'] = self.builder.scenario_name
            self._scenario_info['start_date'] = self.builder.start_date
            self._scenario_info['end_date'] = self.builder.end_date
            self._scenario_info['interval'] = self.builder.interval
            self._scenario_info['base_demand'] = self.builder.demand
            self._scenario_info['base_hydro'] = self.builder.hydro
            self._scenario_info['base_solar'] = self.builder.solar
            self._scenario_info['base_wind'] = self.builder.wind
            if bool(self.builder.change_table.ct):
                self._scenario_info['change_table'] = 'Yes'
            else:
                self._scenario_info['change_table'] = 'No'

    def _generate_scenario_id(self):
        """Generates scenario id.

        """
        print("--> Generating scenario id")
        script = ("(flock -e 200; \
                   id=$(awk -F',' 'END{print $1+1}' %s); \
                   echo $id, >> %s; \
                   echo $id) 200>/tmp/scenario.lockfile" %
                   (const.SCENARIO_LIST, const.SCENARIO_LIST))

        stdin, stdout, stderr = self._ssh.exec_command(script)
        if len(stderr.readlines()) != 0:
            raise IOError("Failed to update %s on server" % const.SCENARIO_LIST)
        else:
            scenario_id = stdout.readlines()[0].splitlines()[0]
            self._scenario_info['id'] = scenario_id
            self._scenario_info.move_to_end('id', last=False)

    def _add_entry_in_scenario_list(self):
        """Adds scenario to the scenario list file on server.

        :raises IOError: if scenario list file on server cannot be updated.
        """
        print("--> Adding entry in scenario table on server")
        entry = ",".join(self._scenario_info.values())
        options = "-F, -v INPLACE_SUFFIX=.bak -i inplace"
        program = ("'{for(i=1; i<=NF; i++){if($1==%s) $0=\"%s\"}};1'" %
                   (self._scenario_info['id'], entry))
        command = "awk %s %s %s" % (options, program, const.SCENARIO_LIST)

        stdin, stdout, stderr = self._ssh.exec_command(command)
        if len(stderr.readlines()) != 0:
            raise IOError("Failed to update %s on server" % const.SCENARIO_LIST)


    def _add_entry_in_execute_list(self):
        """Adds scenario to the execute list file on server.

        :raises IOError: if execute list file on server cannot be updated.
        """
        print("--> Adding entry in execute table on server\n")
        entry = "%s,created" % self._scenario_info['id']
        command = "echo %s >> %s" % (entry, const.EXECUTE_LIST)

        stdin, stdout, stderr = self._ssh.exec_command(command)
        if len(stderr.readlines()) != 0:
            raise IOError("Failed to update %s on server" % const.EXECUTE_LIST)
        self._scenario_status = 'created'
        self.allowed.append('execute')

    def _upload_change_table(self):
        """Uploads change table to server.

        """
        print("--> Writing change table on local machine")
        self.builder.change_table.write(self._scenario_info['id'])
        print("--> Uploading change table to server")
        file_name = self._scenario_info['id'] + '_ct.pkl'
        upload(self._ssh, file_name, const.LOCAL_DIR, const.INPUT_DIR)

    def _create_link(self):
        """Creates links to base profiles on server.

        """
        print("--> Creating links to base profiles on server")
        for p in ['demand', 'hydro', 'solar', 'wind']:
            version = self._scenario_info['base_' + p]
            self.builder.profile.create_link(self._scenario_info['id'],
                                             p, version)

    def create_scenario(self):
        """Creates scenario.

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

            # Generate scenario id
            self._generate_scenario_id()
            # Add missing information
            self._scenario_info['state'] = 'execute'
            self._scenario_info['runtime'] = ''
            self._scenario_info['infeasibilities'] = ''
            # Add scenario to scenario list file on server
            self._add_entry_in_scenario_list()
            # Upload change table to server
            if bool(self.builder.change_table.ct):
                self._upload_change_table()
            # Create symbolic links to base profiles on server
            self._create_link()
            # Add scenario to execute list file on server
            self._add_entry_in_execute_list()

            print("SCENARIO SUCCESSFULLY CREATED WITH ID #%s" %
                  self._scenario_info['id'])
            self.switch(Execute)

    def print_scenario_info(self):
        """Prints scenario information.

        """
        self._update_scenario_info()
        print("--------------------")
        print("SCENARIO INFORMATION")
        print("--------------------")
        for key, val in self._scenario_info.items():
            print("%s: %s" % (key, val))

    def set_builder(self, interconnect):
        """Sets builder.

        :param list interconnect: name of interconnect(s).
        """

        check_interconnect(interconnect)
        if 'Eastern' in interconnect:
            pass
        elif 'Texas' in interconnect:
            pass
        elif 'Western' in interconnect:
            self.builder = Western(self._ssh)
        elif 'Western' in interconnect and 'Texas' in interconnect:
            pass
        elif 'Eastern' in interconnect and 'Texas' in interconnect:
            pass
        elif 'Eastern' in interconnect and 'Western' in interconnect:
            pass
        elif 'USA' in interconnect:
            pass
        print("--> Summary")
        print("# Existing study")
        plan = [p for p in self.builder.existing.plan.unique()]
        print("%s" % " | ".join(plan))

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
    start_date = '2016-01-01 00:00:00'
    end_date = '2016-12-31 23:00:00'
    interval = '144H'
    demand = ''
    hydro = ''
    solar = ''
    wind = ''
    name = 'builder'

    def set_name(self, plan_name, scenario_name): pass

    def set_time(self, start_date, end_date, interval): pass

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

    def __init__(self, ssh_client):
        """Constructor.

        :param paramiko ssh_client: session with an SSH server.
        """
        self.interconnect = ['Western']
        self.profile = CSV(self.interconnect, ssh_client)
        self.change_table = ChangeTable(self.interconnect)

        table = get_scenario_table(ssh_client)
        self.existing = table[table.interconnect == self.name]


    def set_name(self, plan_name, scenario_name):
        """Sets scenario name.

        :param str plan_name: plan name
        :param str scenario_name: scenario name.
        :raises Exception: if combination plan - scenario already exists
        """

        if plan_name in self.existing.plan.tolist():
            scenario = self.existing[self.existing.plan == plan_name]
            if scenario_name in scenario.name.tolist():
                raise Exception('Combination %s - %s already exists' %
                                (plan_name, scenario_name))
        self.plan_name = plan_name
        self.scenario_name = scenario_name

    def set_time(self, start_date, end_date, interval):
        """Sets scenario start and end dates as well as the interval that \
            will be used to split the date range.

        :param str start_date: start date.
        :param str end_date: start date.
        :param str interval: interval.
        :raises Exception: if start date, end date or interval are not \
            properly defined.
        """
        min_ts = pd.Timestamp('2016-01-01 00:00:00')
        max_ts = pd.Timestamp('2016-12-31 23:00:00')

        start_ts = pd.Timestamp(start_date)
        end_ts = pd.Timestamp(end_date)
        hours = (end_ts - start_ts) / np.timedelta64(1, 'h') + 1
        if start_ts > end_ts:
            raise Exception("start_date > end_date")
        elif start_ts < min_ts or start_ts >= max_ts:
            raise Exception("start_date not in [%s,%s[" % (min_ts, max_ts))
        elif end_ts <= min_ts or end_ts > max_ts:
            raise Exception("end_date not in ]%s,%s]" % (lmin_ts, max_ts))
        elif hours % int(interval.split('H', 1)[0]) != 0:
            raise Exception("Incorrect interval for start and end dates")
        else:
            self.start_date = start_date
            self.end_date = end_date
            self.interval = interval

    def get_base_profile(self, type):
        """Returns available base profiles.

        :param str type: one of *'demand'*, *'hydro'*, *'solar'*, *'wind'*.
        :return: (*list*) -- available version for selected profile type.
        """
        return self.profile.get_base_profile(type)

    def set_base_profile(self, type, version):
        """Sets demand profile.

        :param str type: one of *'demand'*, *'hydro'*, *'solar'*, *'wind'*.
        :param str version: demand profile version.
        :raises Exception: if no profile or selected version.
        """
        possible = self.get_base_profile(type)
        if len(possible) == 0:
            raise Exception("No %s profile available in %s" %
                            (type, " + ".join(self.interconnect)))
        elif version in possible:
            if type == 'demand': self.demand = version
            if type == 'hydro': self.hydro = version
            if type == 'solar': self.solar = version
            if type == 'wind': self.wind = version
        else:
            raise Exception("Available %s profiles for %s: %s" %
                            (type,
                             " + ".join(self.interconnect),
                             " | ".join(possible)))

    def load_change_table(self, filename):
        """Uploads change table.

        :param str filename: full path to change table pickle file.
        :raises FileNotFoundError: if file not found.
        """
        try:
            ct = pickle.load(open(filename, "rb"))
            self.change_table.ct = ct
        except:
            raise FileNotFoundError("%s not found. " % filename)


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
    def __init__(self, interconnect, ssh_client):
        """Constructor.

        :param list interconect: interconect(s)
        :param paramiko ssh_client: session with an SSH server.
        """
        self._ssh = ssh_client
        self.interconnect = interconnect

    def get_base_profile(self, type):
        """Returns available base profiles.

        :param str type: one of *'demand'*, *'hydro'*, *'solar'*, *'wind'*.
        :return: (*list*) -- available version for selected profile type.
        """
        possible = ['demand', 'hydro', 'solar', 'wind']
        if type not in possible:
            raise NameError("Choose from %s" % " | ".join(possible))

        available = interconnect2name(self.interconnect) + '_' + type + '_*'
        query = os.path.join(const.BASE_PROFILE_DIR, available)
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
        :raises IOError: if symbolic link cannot be created.
        """
        interconnect = interconnect2name(self.interconnect)
        source = interconnect + '_' + type + '_' + version + '.csv'
        target = id + '_' + type + '.csv'

        command = "ln -s %s %s" % (const.BASE_PROFILE_DIR + '/' + source,
                                   const.INPUT_DIR + '/' + target)
        stdin, stdout, stderr = self._ssh.exec_command(command)
        if len(stderr.readlines()) != 0:
            raise IOError("Failed to create link to %s profile." % type)
