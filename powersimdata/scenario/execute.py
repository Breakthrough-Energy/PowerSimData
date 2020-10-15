import copy
import os
import posixpath
from collections import OrderedDict
from subprocess import Popen

import numpy as np
from scipy.io import savemat

from powersimdata.input.grid import Grid
from powersimdata.input.input_data import InputData
from powersimdata.input.transform_grid import TransformGrid
from powersimdata.input.transform_profile import TransformProfile
from powersimdata.scenario.helpers import interconnect2name
from powersimdata.scenario.state import State
from powersimdata.utility import server_setup
from powersimdata.utility.transfer_data import upload


class Execute(State):
    """Scenario is in a state of being executed.

    :param powersimdata.scenario.scenario.Scenario scenario: scenario instance.
    """

    name = "execute"
    allowed = []

    def __init__(self, scenario):
        """Constructor."""
        self._scenario_info = scenario.info
        self._scenario_status = scenario.status
        super().__init__(scenario)

        print(
            "SCENARIO: %s | %s\n"
            % (self._scenario_info["plan"], self._scenario_info["name"])
        )
        print("--> State\n%s" % self.name)
        print("--> Status\n%s" % self._scenario_status)

        self._set_ct_and_grid()

    def _set_ct_and_grid(self):
        """Sets change table and grid."""
        base_grid = Grid(self._scenario_info["interconnect"].split("_"))
        if self._scenario_info["change_table"] == "Yes":
            input_data = InputData(self._ssh)
            self.ct = input_data.get_data(self._scenario_info, "ct")
            self.grid = TransformGrid(base_grid, self.ct).get_grid()
        else:
            self.ct = {}
            self.grid = base_grid

    def get_ct(self):
        """Returns change table.

        :return: (*dict*) -- change table.
        """
        return copy.deepcopy(self.ct)

    def get_grid(self):
        """Returns Grid.

        :return: (*powersimdata.input.grid.Grid*) -- a Grid object.
        """
        return copy.deepcopy(self.grid)

    def _update_scenario_status(self):
        """Updates scenario status."""
        execute_table = self._execute_list_manager.get_execute_table()
        scenario_id = self._scenario_info["id"]
        self._scenario_status = execute_table[
            execute_table.id == scenario_id
        ].status.values[0]

    def _update_scenario_info(self):
        """Updates scenario information."""
        scenario_table = self._scenario_list_manager.get_scenario_table()
        scenario_id = self._scenario_info["id"]
        scenario = scenario_table[scenario_table.id == scenario_id]
        self._scenario_info = scenario.to_dict("records", into=OrderedDict)[0]

    def _run_script(self, script, extra_args=None):
        """Returns running process

        :param str script: script to be used.
        :param list/None extra_args: list of strings to be passed after scenario id.
        :return: (*subprocess.Popen*) -- process used to run script
        """
        if extra_args is None:
            extra_args = []
        else:
            extra_args = [str(a) for a in extra_args]

        path_to_package = posixpath.join(
            server_setup.MODEL_DIR, self._scenario_info["engine"]
        )
        if self._scenario_info["engine"] == "REISE":
            folder = "pyreise"
        else:
            folder = "pyreisejl"
        path_to_script = posixpath.join(path_to_package, folder, "utility", script)
        username = server_setup.get_server_user()
        cmd_ssh = ["ssh", username + "@" + server_setup.SERVER_ADDRESS]
        cmd_pythonpath = [f'export PYTHONPATH="{path_to_package}:$PYTHONPATH";']
        cmd_pythoncall = [
            "nohup",
            "python3",
            "-u",
            path_to_script,
            self._scenario_info["id"],
        ]
        cmd_io_redirect = ["</dev/null >/dev/null 2>&1 &"]
        cmd = cmd_ssh + cmd_pythonpath + cmd_pythoncall + extra_args + cmd_io_redirect
        process = Popen(cmd)
        print("PID: %s" % process.pid)
        return process

    def print_scenario_info(self):
        """Prints scenario information."""
        print("--------------------")
        print("SCENARIO INFORMATION")
        print("--------------------")
        self._update_scenario_info()
        for key, val in self._scenario_info.items():
            print("%s: %s" % (key, val))

    def print_scenario_status(self):
        """Prints scenario status."""
        print("---------------")
        print("SCENARIO STATUS")
        print("---------------")
        self._update_scenario_status()
        print(self._scenario_status)

    def prepare_simulation_input(self, profiles_as=None):
        """Prepares scenario for execution

        :param int/str/None profiles_as: if given, copy profiles from this scenario.
        :raises TypeError: if profiles_as parameter not a str or int.
        """
        if profiles_as is not None and not isinstance(profiles_as, (str, int)):
            raise TypeError("profiles_as must be None, str, or int.")

        self._update_scenario_status()
        if self._scenario_status == "created":
            print("---------------------------")
            print("PREPARING SIMULATION INPUTS")
            print("---------------------------")

            si = SimulationInput(self._ssh, self._scenario_info, self.grid, self.ct)
            si.create_folder()
            for p in ["demand", "hydro", "solar", "wind"]:
                si.prepare_profile(p, profiles_as)

            si.prepare_mpc_file()

            self._execute_list_manager.update_execute_list(
                "prepared", self._scenario_info
            )
        else:
            print("---------------------------")
            print("SCENARIO CANNOT BE PREPARED")
            print("---------------------------")
            print("Current status: %s" % self._scenario_status)
            return

    def launch_simulation(self, threads=None):
        """Launches simulation on server.

        :param int/None threads: the number of threads to be used (None -> auto).
        :return: (*subprocess.Popen*) -- new process used to launch simulation.
        """
        print("--> Launching simulation on server")
        if threads is None:
            extra_args = None
        else:
            if not isinstance(threads, int):
                raise TypeError("threads must be an int")
            if threads < 1:
                raise ValueError("threads must be a positive value")
            extra_args = [threads]

        return self._run_script("call.py", extra_args=extra_args)

    def extract_simulation_output(self):
        """Extracts simulation outputs {PG, PF, LMP, CONGU, CONGL} on server.

        :return: (*subprocess.Popen*) -- new process used to extract output
            data.
        """
        self._update_scenario_status()
        if self._scenario_status == "finished":
            print("--> Extracting output data on server")
            return self._run_script("extract_data.py")
        else:
            print("---------------------------")
            print("OUTPUTS CANNOT BE EXTRACTED")
            print("---------------------------")
            print("Current status: %s" % self._scenario_status)
            return


class SimulationInput(object):
    """Prepares scenario for execution.

    :param paramiko.client.SSHClient ssh_client: session with an SSH server.
    :param dict scenario_info: scenario information.
    :param powersimdata.input.grid.Grid grid: a Grid object.
    :param dict ct: change table.
    """

    def __init__(self, ssh_client, scenario_info, grid, ct):
        """Constructor."""
        self._ssh = ssh_client
        self._scenario_info = scenario_info
        self.grid = grid
        self.ct = ct

        self.TMP_DIR = posixpath.join(
            server_setup.EXECUTE_DIR, "scenario_%s" % scenario_info["id"]
        )

    def create_folder(self):
        """Creates folder on server that will enclose simulation inputs.

        :raises IOError: if folder cannot be created.
        """
        print("--> Creating temporary folder on server for simulation inputs")
        command = "mkdir %s" % self.TMP_DIR
        stdin, stdout, stderr = self._ssh.exec_command(command)
        if len(stderr.readlines()) != 0:
            raise IOError("Failed to create %s on server" % self.TMP_DIR)

    def prepare_mpc_file(self):
        """Creates MATPOWER case file."""
        print("--> Preparing MPC file")
        print("Scaling grid")
        grid = copy.deepcopy(self.grid)

        print("Building MPC file")
        mpc = {"mpc": {"version": "2", "baseMVA": 100.0}}

        # zone
        mpc["mpc"]["zone"] = np.array(list(grid.id2zone.items()), dtype=object)

        # sub
        sub = grid.sub.copy()
        subid = sub.index.values[np.newaxis].T
        mpc["mpc"]["sub"] = sub.values
        mpc["mpc"]["subid"] = subid

        # bus
        bus = grid.bus.copy()
        busid = bus.index.values[np.newaxis].T
        bus.reset_index(level=0, inplace=True)
        bus.drop(columns=["interconnect", "lat", "lon"], inplace=True)
        mpc["mpc"]["bus"] = bus.values
        mpc["mpc"]["busid"] = busid

        # bus2sub
        bus2sub = grid.bus2sub.copy()
        mpc["mpc"]["bus2sub"] = bus2sub.values

        # plant
        gen = grid.plant.copy()
        genid = gen.index.values[np.newaxis].T
        genfuel = gen.type.values[np.newaxis].T
        genfuelcost = gen.GenFuelCost.values[np.newaxis].T
        heatratecurve = gen[["GenIOB", "GenIOC", "GenIOD"]].values
        gen.reset_index(inplace=True, drop=True)
        gen.drop(
            columns=[
                "type",
                "interconnect",
                "lat",
                "lon",
                "zone_id",
                "zone_name",
                "GenFuelCost",
                "GenIOB",
                "GenIOC",
                "GenIOD",
            ],
            inplace=True,
        )
        mpc["mpc"]["gen"] = gen.values
        mpc["mpc"]["genid"] = genid
        mpc["mpc"]["genfuel"] = genfuel
        mpc["mpc"]["genfuelcost"] = genfuelcost
        mpc["mpc"]["heatratecurve"] = heatratecurve
        # branch
        branch = grid.branch.copy()
        branchid = branch.index.values[np.newaxis].T
        branchdevicetype = branch.branch_device_type.values[np.newaxis].T
        branch.reset_index(inplace=True, drop=True)
        branch.drop(
            columns=[
                "interconnect",
                "from_lat",
                "from_lon",
                "to_lat",
                "to_lon",
                "from_zone_id",
                "to_zone_id",
                "from_zone_name",
                "to_zone_name",
                "branch_device_type",
            ],
            inplace=True,
        )
        mpc["mpc"]["branch"] = branch.values
        mpc["mpc"]["branchid"] = branchid
        mpc["mpc"]["branchdevicetype"] = branchdevicetype

        # generation cost
        gencost = grid.gencost.copy()
        gencost["before"].reset_index(inplace=True, drop=True)
        gencost["before"].drop(columns=["interconnect"], inplace=True)
        mpc["mpc"]["gencost"] = gencost["before"].values

        # DC line
        if len(grid.dcline) > 0:
            dcline = grid.dcline.copy()
            dclineid = dcline.index.values[np.newaxis].T
            dcline.reset_index(inplace=True, drop=True)
            dcline.drop(columns=["from_interconnect", "to_interconnect"], inplace=True)
            mpc["mpc"]["dcline"] = dcline.values
            mpc["mpc"]["dclineid"] = dclineid

        # energy storage
        if len(grid.storage["gen"]) > 0:
            storage = grid.storage.copy()

            mpc_storage = {
                "storage": {
                    "xgd_table": np.array([]),
                    "gen": np.array(storage["gen"].values, dtype=np.float64),
                    "sd_table": {
                        "colnames": storage["StorageData"].columns.values[np.newaxis],
                        "data": storage["StorageData"].values,
                    },
                }
            }

            file_name = "%s_case_storage.mat" % self._scenario_info["id"]
            savemat(
                os.path.join(server_setup.LOCAL_DIR, file_name),
                mpc_storage,
                appendmat=False,
            )
            upload(
                self._ssh,
                file_name,
                server_setup.LOCAL_DIR,
                self.TMP_DIR,
                change_name_to="case_storage.mat",
            )
            print("Deleting %s on local machine" % file_name)
            os.remove(os.path.join(server_setup.LOCAL_DIR, file_name))

        # MPC file
        file_name = "%s_case.mat" % self._scenario_info["id"]
        savemat(os.path.join(server_setup.LOCAL_DIR, file_name), mpc, appendmat=False)

        upload(
            self._ssh,
            file_name,
            server_setup.LOCAL_DIR,
            self.TMP_DIR,
            change_name_to="case.mat",
        )

        print("Deleting %s on local machine" % file_name)
        os.remove(os.path.join(server_setup.LOCAL_DIR, file_name))

    def prepare_profile(self, kind, profile_as=None):
        """Prepares profile for simulation.

        :param kind: one of *demand*, *'hydro'*, *'solar'* or *'wind'*.
        :param int/str/None profile_as: if given, copy profile from this scenario.
        """
        if profile_as is None:
            profile = TransformProfile(
                self._ssh, self._scenario_info, self.grid, self.ct
            )
            if bool(profile.scale_keys[kind] & set(self.ct.keys())):
                self._prepare_scaled_profile(kind, profile)
            else:
                self._create_link_to_base_profile(kind)
        else:
            from_dir = posixpath.join(
                server_setup.EXECUTE_DIR, f"scenario_{profiles_as}"
            )
            to_dir = posixpath.join(
                server_setup.EXECUTE_DIR, f"scenario_{self._scenario_info['id']}"
            )
            command = f"cp {from_dir}/{p}.csv {to_dir}"
            stdin, stdout, stderr = self._ssh.exec_command(command)
            if len(stderr.readlines()) != 0:
                raise IOError(f"Failed to copy {p}.csv on server")

    def _create_link_to_base_profile(self, kind):
        """Creates link to base profile in temporary directory on server.

        :param str kind: one of *demand*, *'hydro'*, *'solar'* or *'wind'*.
        :raises IOError: if link cannot be created.
        """
        print("--> Creating link to %s base profile into temporary folder" % kind)

        interconnect = interconnect2name(self._scenario_info["interconnect"].split("_"))
        version = self._scenario_info["base_" + kind]
        source = interconnect + "_" + kind + "_" + version + ".csv"
        target = kind + ".csv"

        command = "ln -s %s %s" % (
            posixpath.join("../../raw", source),
            posixpath.join(self.TMP_DIR, target),
        )
        stdin, stdout, stderr = self._ssh.exec_command(command)
        if len(stderr.readlines()) != 0:
            raise IOError("Failed to create link to %s profile." % kind)

    def _prepare_scaled_profile(self, kind, profile):
        """Loads, scales and writes on local machine a base profile.

        :param powersimdata.input.transform_profile.TransformProfile profile: a
            TransformProfile object.
        :param str kind: one of *'hydro'*, *'solar'*, *'wind'* or *'demand'*.
        """
        profile = profile.get_profile(kind)

        print(
            "Writing scaled %s profile in %s on local machine"
            % (kind, server_setup.LOCAL_DIR)
        )
        file_name = "%s_%s.csv" % (self._scenario_info["id"], kind)
        profile.to_csv(os.path.join(server_setup.LOCAL_DIR, file_name))

        upload(
            self._ssh,
            file_name,
            server_setup.LOCAL_DIR,
            self.TMP_DIR,
            change_name_to="%s.csv" % kind,
        )

        print("Deleting %s on local machine" % file_name)
        os.remove(os.path.join(server_setup.LOCAL_DIR, file_name))
