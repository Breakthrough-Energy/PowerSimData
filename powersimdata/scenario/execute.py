from postreise.process import const
from postreise.process.transferdata import get_execute_table, get_scenario_table
from postreise.process.transferdata import upload
from powersimdata.input.scaler import Scaler
from powersimdata.scenario.state import State

from collections import OrderedDict
from scipy.io import savemat
import numpy as np
import os
from subprocess import Popen, PIPE


class Execute(State):
    """Scenario is in a state of being executed.

    :param powersimdata.scenario.scenario.Scenario scenario: scenario instance.
    """
    name = 'execute'
    allowed = []

    def __init__(self, scenario):
        """Constructor.

        """
        self._scenario_info = scenario.info
        self._scenario_status = scenario.status
        self._ssh = scenario.ssh

        print("SCENARIO: %s | %s\n" % (self._scenario_info['plan'],
                                       self._scenario_info['name']))
        print("--> State\n%s" % self.name)
        print("--> Status\n%s" % self._scenario_status)

    def _update_scenario_status(self):
        """Updates scenario status.

        """
        execute_table = get_execute_table(self._ssh)
        scenario_id = self._scenario_info['id']
        self._scenario_status = execute_table[execute_table.id == scenario_id
                                              ].status.values[0]

    def _update_scenario_info(self):
        """Updates scenario information.

        """
        scenario_table = get_scenario_table(self._ssh)
        scenario_id = self._scenario_info['id']
        scenario = scenario_table[scenario_table.id == scenario_id]
        self._scenario_info = scenario.to_dict('records', into=OrderedDict)[0]

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
        stdin, stdout, stderr = self._ssh.exec_command(command)
        if len(stderr.readlines()) != 0:
            raise IOError("Failed to update %s on server" % const.EXECUTE_LIST)

    def print_scenario_info(self):
        """Prints scenario information.

        """
        print("--------------------")
        print("SCENARIO INFORMATION")
        print("--------------------")
        self._update_scenario_info()
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

            self.scaler = Scaler(self._scenario_info, self._ssh)
            si = SimulationInput(self.scaler, self._ssh)
            si.create_folder()
            for r in ['demand', 'hydro', 'solar', 'wind']:
                si.prepare_profile(r)

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

        :return: (*subprocess.Popen*) -- new process used to launch simulation.
        """
        print("--> Launching simulation on server")
        cmd = ['ssh', const.SERVER_ADDRESS,
               'export PYTHONPATH="/home/EGM/v2/PreREISE/:$PYTHONPATH";',
               'python3',
               '/home/EGM/v2/PreREISE/prereise/call/call.py',
               self._scenario_info['id']]
        process = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        print("PID: %s" % process.pid)
        return process

    def extract_simulation_output(self):
        """Extracts simulation outputs {PG, PF, LMP, CONGU, CONGL} on server.

        :return: (*subprocess.Popen*) -- new process used to extract output
            data.
        """
        self._update_scenario_status()
        if self._scenario_status == 'finished':
            print("--> Extracting output data on server")
            cmd = ['ssh', const.SERVER_ADDRESS,
                   'export PYTHONPATH="/home/EGM/v2/PostREISE/:$PYTHONPATH";',
                   'python3',
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

    :param Scaler scaler: Scaler instance.
    :param paramiko.client.SSHClient ssh_client: session with an SSH server.
    """

    def __init__(self, scaler, ssh_client):
        """Constructor.

        """
        self.scaler = scaler
        self._tmp_dir = '%s/scenario_%s' % (const.EXECUTE_DIR,
                                            scaler.scenario_id)
        self._ssh = ssh_client

    def create_folder(self):
        """Creates folder on server that will enclose simulation inputs.

        :raises IOError: if folder cannot be created.
        """
        print("--> Creating temporary folder on server for simulation inputs")
        command = "mkdir %s" % self._tmp_dir
        stdin, stdout, stderr = self._ssh.exec_command(command)
        if len(stderr.readlines()) != 0:
            raise IOError("Failed to create %s on server" % self._tmp_dir)

    def prepare_mpc_file(self):
        """Creates MATPOWER case file.

        """
        print("--> Preparing MPC file")
        print("Scaling grid")
        grid = self.scaler.get_grid()

        print("Building MPC file")
        # Format bus
        bus = grid.bus.copy()
        bus.reset_index(level=0, inplace=True)
        bus.drop(columns=['interconnect', 'lat', 'lon'], inplace=True)
        bus.insert(10, 'loss_zone', [1] * len(bus))
        # Format generator
        gen = grid.plant.copy()
        genid = gen.index.values[np.newaxis].T
        gen.reset_index(inplace=True, drop=True)
        genfuel = gen.type.values[np.newaxis].T
        gen.drop(columns=['GenMWMax', 'GenMWMin', 'type', 'interconnect',
                          'lat', 'lon', 'zone_id', 'zone_name'], inplace=True)
        # Format branch
        branch = grid.branch.copy()
        branchid = branch.index.values[np.newaxis].T
        branch.reset_index(inplace=True, drop=True)
        branch.drop(columns=['interconnect', 'from_lat', 'from_lon', 'to_lat',
                             'to_lon', 'from_zone_id', 'to_zone_id',
                             'from_zone_name', 'to_zone_name',
                             'branch_device_type'], inplace=True)
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
        mpc = {'mpc': {'version': '2', 'baseMVA': 100.0, 'bus': bus.values,
                       'gen': gen.values, 'gencost': gencost.values,
                       'genfuel': genfuel, 'genid': genid,
                       'branch': branch.values, 'branchid': branchid}}
        if len(dcline) > 0:
            mpc['mpc']['dcline'] = dcline.values
        # Write MPC file
        file_name = '%s_case.mat' % self.scaler.scenario_id
        savemat(os.path.join(const.LOCAL_DIR, file_name), mpc, appendmat=False)

        upload(self._ssh, file_name, const.LOCAL_DIR, self._tmp_dir,
               change_name_to='case.mat')

    def prepare_profile(self, kind):
        """Prepares profile for simulation.

        :param kind: one of *demand*, *'hydro'*, *'solar'* or *'wind'*.
        """
        if kind in self.scaler.ct.keys():
            self._prepare_scaled_profile(kind)
        else:
            self._copy_base_profile(kind)

    def _copy_base_profile(self, kind):
        """Copies base profile in temporary directory on server.

        :param str kind: one of *demand*, *'hydro'*, *'solar'* or *'wind'*.
        :raises IOError: if file cannot be copied.
        """
        print("--> Copying %s base profile into temporary folder" % kind)
        command = "cp -a %s/%s_%s.csv %s/%s.csv" % (const.INPUT_DIR,
                                                    self.scaler.scenario_id,
                                                    kind,
                                                    self._tmp_dir,
                                                    kind)
        stdin, stdout, stderr = self._ssh.exec_command(command)
        if len(stderr.readlines()) != 0:
            raise IOError("Failed to copy inputs in %s on server" %
                          self._tmp_dir)

    def _prepare_scaled_profile(self, kind):
        """Loads, scales and writes on local machine a base profile.

        :param str kind: one of *'hydro'*, *'solar'* or *'wind'*.
        """
        if kind == 'demand':
            profile = self.scaler.get_demand()
        else:
            profile = self.scaler.get_power_output(kind)

        print("Writing scaled %s profile in %s on local machine" %
              (kind, const.LOCAL_DIR))
        file_name = '%s_%s.csv' % (self.scaler.scenario_id, kind)
        profile.to_csv(os.path.join(const.LOCAL_DIR, file_name))

        upload(self._ssh, file_name, const.LOCAL_DIR, self._tmp_dir,
               change_name_to='%s.csv' % kind)
