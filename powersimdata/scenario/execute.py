from postreise.process import const
from postreise.process.transferdata import setup_server_connection
from postreise.process.transferdata import get_execute_table
from postreise.process.transferdata import upload
from powersimdata.input.scaler import Scaler
from powersimdata.input.grid import Grid
from powersimdata.scenario.state import State

from collections import OrderedDict
from scipy.io import savemat
import numpy as np
import os
from subprocess import Popen, PIPE


class Execute(State):
    """Scenario is in a state of being executed.

    """
    name = 'execute'
    allowed = ['stop']

    def __init__(self, scenario):
        """Constructor.

        :param class scenario: scenario instance.
        """
        self._scenario_info = scenario._info
        self._scenario_status = scenario._status
        print("SCENARIO: %s | %s\n" % (self._scenario_info['plan'],
                                       self._scenario_info['name']))
        print("--> Status\n%s" % self._scenario_status)

    def _update_scenario_status(self):
        """Updates scenario status.

        """
        table = get_execute_table()
        id = self._scenario_info['id']
        self._scenario_status = table[table.id == id].status.values[0]

    def _update_execute_list(self, status):
        """Updates status in execute list file on server.

        :param str status: execution status.
        :raises IOError: if execute list file on server cannot be updated.
        """
        print("--> Updating status in execute table on server")
        options = "-F, -v OFS=',' -v INPLACE_SUFFIX=.bak -i inplace"
        program = ("'{for(i=1; i<=NF; i++){if($1==%s) $2=\"%s\"}};1'" %
                   (self._scenario_info['id'], status))
        command = "awk %s %s %s" % (options, program, const.EXECUTE_LIST)
        ssh = setup_server_connection()
        stdin, stdout, stderr = ssh.exec_command(command)
        if len(stderr.readlines()) != 0:
            raise IOError("Failed to update %s on server" % const.EXECUTE_LIST)

    def print_scenario_info(self):
        """Prints scenario information.

        """
        print("--------------------")
        print("SCENARIO INFORMATION")
        print("--------------------")
        for key, val in self._scenario_info.items():
            print("%s: %s" % (key, val))

    def print_scenario_status(self):
        """Prints scenario status.

        """
        print("---------------")
        print("SCENARIO STATUS")
        print("---------------")
        self._update_scenario_status()
        print(self._scenario_status)

    def prepare_simulation_input(self):
        """Prepares scenario for execution

        """
        self._update_scenario_status()
        if self._scenario_status == 'created':
            print("---------------------------")
            print("PREPARING SIMULATION INPUTS")
            print("---------------------------")

            self._scaler = Scaler(self._scenario_info)
            si = SimulationInput(self._scaler)
            si.create_folder()
            for r in ['demand', 'hydro', 'solar', 'wind']:
                try:
                    self._scaler.ct[r]
                    si.prepare_scaled_profile(r)
                except KeyError:
                    si.copy_base_profile(r)
            si.prepare_mpc_file()

            self._update_execute_list('prepared')
        else:
            print("---------------------------")
            print("SCENARIO CANNOT BE PREPARED")
            print("---------------------------")
            print("Current status: %s" % self._scenario_status)
            return

    def launch_simulation(self):
        """Launches simulation on server.

        :return: (*Popen*) -- new process used to launch simulation.
        """
        print("--> Launching simulation on server")
        cmd = ['ssh', const.SERVER_ADDRESS, 'python3',
               '/home/EGM/v2/PreREISE/prereise/call/call.py',
               self._scenario_info['id']]
        process = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        print("PID: %s" % process.pid)
        return process

    def extract_simulation_output(self):
        """Extracts simulation outputs PG and PF on server.

        :return: (*Popen*) -- new process used to extract output data.
        """
        self._update_scenario_status()
        if self._scenario_status == 'finished':
            print("--> Extracting output data on server")
            cmd = ['ssh', const.SERVER_ADDRESS, 'python3',
                   '/home/EGM/v2/PostREISE/postreise/extract/extract_data.py',
                   self._scenario_info['id']]
            process = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
            print("PID: %s" % process.pid)
            return process
        else:
            print("---------------------------")
            print("OUTPUTS CANNOT BE EXTRACTED")
            print("---------------------------")
            print("Current status: %s" % self._scenario_status)
            return


class SimulationInput(object):
    """Prepares scenario for execution.

    """

    def __init__(self, scaler):
        """Constructor.

        :param Scaler scaler: Scaler instance.
        """
        self._scaler = scaler
        self._tmp_dir = '%s/scenario_%s' % (const.EXECUTE_DIR,
                                            scaler.scenario_id)

    def create_folder(self):
        """Creates folder on server that will enclose simulation inputs.

        :raises IOError: if folder cannot be created.
        """
        print("--> Creating temporary folder on server for simulation inputs")
        command = "mkdir %s" % self._tmp_dir
        ssh = setup_server_connection()
        stdin, stdout, stderr = ssh.exec_command(command)
        if len(stderr.readlines()) != 0:
            raise IOError("Failed to create %s on server" % self._tmp_dir)

    def copy_base_profile(self, resource):
        """Copies base profile in temporary directory on server.

        :param str resource: one of *'hydro'*, *'solar'* or *'wind'*.
        :raises IOError: if file cannot be copied.
        """
        print("--> Copying %s base profile into temporary folder" % resource)
        command = "cp -a %s/%s_%s.csv %s/%s.csv" % (const.INPUT_DIR,
                                                    self._scaler.scenario_id,
                                                    resource,
                                                    self._tmp_dir,
                                                    resource)
        ssh = setup_server_connection()
        stdin, stdout, stderr = ssh.exec_command(command)
        if len(stderr.readlines()) != 0:
            raise IOError("Failed to copy inputs on server" % self._tmp_dir)

    def prepare_mpc_file(self):
        """Creates MATPOWER case file.

        """
        print("--> Preparing MPC file")
        print("Scaling grid")
        grid = self._scaler.get_grid()

        print("Building MPC file")
        # Format bus
        bus = grid.bus.copy()
        bus.reset_index(level=0, inplace=True)
        bus.drop(columns=['interconnect', 'lat', 'lon'], inplace=True)
        bus.insert(10, 'loss_zone', [1]*len(bus))
        # Format generator
        gen = grid.plant.copy()
        gen.reset_index(inplace=True, drop=True)
        genfuel = gen.type.values
        gen.drop(columns=['GenMWMax', 'GenMWMin', 'type', 'interconnect',
                          'lat', 'lon', 'zone_id', 'zone_name'], inplace=True)
        # Format branch
        branch = grid.branch.copy()
        branch.reset_index(inplace=True, drop=True)
        branch.drop(columns=['interconnect', 'from_lat', 'from_lon', 'to_lat',
                             'to_lon', 'from_zone_id', 'to_zone_id',
                             'from_zone_name', 'to_zone_name'], inplace=True)
        # Format generation cost
        gencost = grid.gencost.copy()
        gencost.reset_index(inplace=True, drop=True)
        gencost.drop(columns=['interconnect'], inplace=True)
        # Format DC line
        dcline = grid.dcline.copy()
        dcline.reset_index(inplace=True, drop=True)
        dcline.drop(columns=['from_interconnect', 'to_interconnect'],
                    inplace=True)
        # Create MPC data structure
        mpc = {'mpc':{'version': '2', 'baseMVA': 100, 'bus': bus.values,
                      'gen': gen.values, 'branch': branch.values,
                      'gencost': gencost.values, 'genfuel': genfuel,
                      'dcline': dcline.values}}
        # Write MPC file
        file_name = 'case.mat'
        savemat(os.path.join(const.LOCAL_DIR, file_name), mpc, appendmat=False)

        upload(file_name, const.LOCAL_DIR, self._tmp_dir)

        print("Deleting MPC file on local machine")
        os.remove(os.path.join(const.LOCAL_DIR, file_name))

    def prepare_scaled_profile(self, resource):
        """Loads, scales and writes on local machine a base profile.

        :param str resource: one of *'hydro'*, *'solar'* or *'wind'*.
        """
        profile = self._scaler.get_power_output(resource)

        print("Writing scaled %s profile in %s on local machine" %
              (resource, const.LOCAL_DIR))
        file_name = '%s.csv' % resource
        profile.to_csv(os.path.join(const.LOCAL_DIR, file_name))

        upload(file_name, const.LOCAL_DIR, self._tmp_dir)

        print("Deleting scaled %s profile on local machine" % resource)
        os.remove(os.path.join(const.LOCAL_DIR, file_name))
