import copy
import os
import posixpath

import requests

from powersimdata.input.case_mat import export_case_mat
from powersimdata.input.grid import Grid
from powersimdata.input.input_data import InputData
from powersimdata.input.transform_grid import TransformGrid
from powersimdata.input.transform_profile import TransformProfile
from powersimdata.scenario.state import State
from powersimdata.utility import server_setup
from powersimdata.utility.server_setup import DeploymentMode, get_deployment_mode


class Execute(State):
    """Scenario is in a state of being executed.

    :param powersimdata.scenario.scenario.Scenario scenario: scenario instance.
    """

    name = "execute"
    allowed = []
    exported_methods = {
        "check_progress",
        "extract_simulation_output",
        "get_ct",
        "get_grid",
        "launch_simulation",
        "prepare_simulation_input",
        "print_scenario_info",
        "print_scenario_status",
    }

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

    def _scenario_id(self):
        return self._scenario_info["id"]

    def _set_ct_and_grid(self):
        """Sets change table and grid."""
        base_grid = Grid(
            self._scenario_info["interconnect"].split("_"),
            source=self._scenario_info["grid_model"],
        )
        if self._scenario_info["change_table"] == "Yes":
            input_data = InputData()
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
        self._scenario_status = self._execute_list_manager.get_status(
            self._scenario_id()
        )

    def _update_scenario_info(self):
        """Updates scenario information."""
        self._scenario_info = self._scenario_list_manager.get_scenario(
            self._scenario_id()
        )

    def _run_script(self, script, extra_args=None):
        """Returns running process

        :param str script: script to be used.
        :param list extra_args: list of strings to be passed after scenario id.
        :return: (*subprocess.Popen*) -- process used to run script
        """

        if not extra_args:
            extra_args = []

        path_to_package = posixpath.join(
            server_setup.MODEL_DIR, self._scenario_info["engine"]
        )

        if self._scenario_info["engine"] == "REISE":
            folder = "pyreise"
        else:
            folder = "pyreisejl"

        path_to_script = posixpath.join(path_to_package, folder, "utility", script)
        cmd_pythonpath = [f'export PYTHONPATH="{path_to_package}:$PYTHONPATH";']
        cmd_pythoncall = [
            "nohup",
            "python3",
            "-u",
            path_to_script,
            self._scenario_info["id"],
        ]
        cmd_io_redirect = ["</dev/null >/dev/null 2>&1 &"]
        cmd = cmd_pythonpath + cmd_pythoncall + extra_args + cmd_io_redirect
        process = self._data_access.execute_command_async(cmd)
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

            si = SimulationInput(
                self._data_access, self._scenario_info, self.grid, self.ct
            )
            si.create_folder()
            for p in ["demand", "hydro", "solar", "wind"]:
                si.prepare_profile(p, profiles_as)

            si.prepare_mpc_file()

            self._execute_list_manager.set_status(self._scenario_id(), "prepared")
        else:
            print("---------------------------")
            print("SCENARIO CANNOT BE PREPARED")
            print("---------------------------")
            print("Current status: %s" % self._scenario_status)
            return

    def _check_if_ready(self):
        """Check if the current scenario is ready to launch

        :raises ValueError: if status is invalid
        """
        self._update_scenario_status()
        valid_status = ["prepared", "failed", "finished"]
        if self._scenario_status not in valid_status:
            raise ValueError(
                f"Status must be one of {valid_status}, but got status={self._scenario_status}"
            )

    def _launch_on_server(self, threads=None, solver=None, extract_data=True):
        """Launch simulation on server, via ssh.

        :param int/None threads: the number of threads to be used. This defaults to None,
            where None means auto.
        :param str solver: the solver used for optimization. This defaults to
            None, which translates to gurobi
        :param bool extract_data: whether the results of the simulation engine should
            automatically extracted after the simulation has run. This defaults to True.
        :raises TypeError: if extract_data is not a boolean
        :return: (*subprocess.Popen*) -- new process used to launch simulation.
        """
        extra_args = []

        if threads:
            # Use the -t flag as defined in call.py in REISE.jl
            extra_args.append("--threads " + str(threads))

        if solver:
            extra_args.append("--solver " + solver)

        if not isinstance(extract_data, bool):
            raise TypeError("extract_data must be a boolean: 'True' or 'False'")
        if extract_data:
            extra_args.append("--extract-data")

        return self._run_script("call.py", extra_args=extra_args)

    def _launch_in_container(self, threads, solver):
        """Launches simulation in container via http call

        :param int/None threads: the number of threads to be used. This defaults to None,
            where None means auto.
        :param str solver: the solver used for optimization. This defaults to
            None, which translates to gurobi
        :return: (*requests.Response*) -- the http response object
        """
        scenario_id = self._scenario_id()
        url = f"http://{server_setup.SERVER_ADDRESS}:5000/launch/{scenario_id}"
        resp = requests.post(url, params={"threads": threads, "solver": solver})
        if resp.status_code != 200:
            print(
                f"Failed to launch simulation: status={resp.status_code}. See response for details"
            )
        return resp

    def _check_threads(self, threads):
        """Validate threads argument

        :param int threads: the number of threads to be used
        :raises TypeError: if threads is not an int
        :raises ValueError: if threads is not a positive value
        """
        if threads:
            if not isinstance(threads, int):
                raise TypeError("threads must be an int")
            if threads < 1:
                raise ValueError("threads must be a positive value")

    def _check_solver(self, solver):
        """Validate solver argument

        :param str solver: the solver used for the optimization
        :raises ValueError: if invalid solver provided
        """
        solvers = ("gurobi", "glpk")
        if solver is not None and solver.lower() not in solvers:
            raise ValueError(f"Invalid solver: options are {solvers}")

    def launch_simulation(self, threads=None, extract_data=True, solver=None):
        """Launches simulation on target environment (server or container)

        :param int/None threads: the number of threads to be used. This defaults to None,
            where None means auto.
        :param bool extract_data: whether the results of the simulation engine should
            automatically extracted after the simulation has run. This defaults to True.
        :param str solver: the solver used for optimization. This defaults to
            None, which translates to gurobi
        :return: (*subprocess.Popen*) or (*requests.Response*) - either the
            process (if using ssh to server) or http response (if run in container)
        """
        self._check_if_ready()
        self._check_threads(threads)
        self._check_solver(solver)

        mode = get_deployment_mode()
        print(f"--> Launching simulation on {mode.lower()}")
        if mode == DeploymentMode.Server:
            return self._launch_on_server(threads, solver, extract_data)
        return self._launch_in_container(threads, solver)

    def check_progress(self):
        """Get the lastest information from the server container

        :raises NotImplementedError: if not running in container mode
        """
        mode = get_deployment_mode()
        if mode != DeploymentMode.Container:
            raise NotImplementedError("Operation only supported for container mode")

        scenario_id = self._scenario_id()
        url = f"http://{server_setup.SERVER_ADDRESS}:5000/status/{scenario_id}"
        resp = requests.get(url)
        return resp.json()

    def extract_simulation_output(self):
        """Extracts simulation outputs {PG, PF, LMP, CONGU, CONGL} on server.

        :return: (*subprocess.Popen*) -- new process used to extract output
            data.
        """
        self._update_scenario_status()
        if self._scenario_status == "finished":
            mode = get_deployment_mode()
            if mode == DeploymentMode.Container:
                print("WARNING: extraction not yet supported, please extract manually")
                return

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

    :param powersimdata.data_access.data_access.DataAccess data_access:
        data access object.
    :param dict scenario_info: scenario information.
    :param powersimdata.input.grid.Grid grid: a Grid object.
    :param dict ct: change table.
    """

    def __init__(self, data_access, scenario_info, grid, ct):
        """Constructor."""
        self._data_access = data_access
        self._scenario_info = scenario_info
        self.grid = grid
        self.ct = ct
        self.scenario_id = scenario_info["id"]

        self.REL_TMP_DIR = self._data_access.join(
            server_setup.EXECUTE_DIR, f"scenario_{self.scenario_id}"
        )
        self.TMP_DIR = self._data_access.match_scenario_files(self.scenario_id, "tmp")

    def create_folder(self):
        """Creates folder on server that will enclose simulation inputs."""
        description = self._data_access.description
        print(f"--> Creating temporary folder on {description} for simulation inputs")
        self._data_access.makedir(self.TMP_DIR)

    def prepare_mpc_file(self):
        """Creates MATPOWER case file."""
        file_name = f"{self.scenario_id}_case.mat"
        storage_file_name = f"{self.scenario_id}_case_storage.mat"
        file_path = os.path.join(server_setup.LOCAL_DIR, file_name)
        storage_file_path = os.path.join(server_setup.LOCAL_DIR, storage_file_name)
        print("Building MPC file")
        export_case_mat(self.grid, file_path, storage_file_path)
        self._data_access.move_to(
            file_name, self.REL_TMP_DIR, change_name_to="case.mat"
        )
        if len(self.grid.storage["gen"]) > 0:
            self._data_access.move_to(
                storage_file_name, self.REL_TMP_DIR, change_name_to="case_storage.mat"
            )

    def prepare_profile(self, kind, profile_as=None):
        """Prepares profile for simulation.

        :param kind: one of *demand*, *'hydro'*, *'solar'* or *'wind'*.
        :param int/str/None profile_as: if given, copy profile from this scenario.
        """
        if profile_as is None:
            tp = TransformProfile(self._scenario_info, self.grid, self.ct)
            profile = tp.get_profile(kind)
            print(
                f"Writing scaled {kind} profile in {server_setup.LOCAL_DIR} on local machine"
            )
            file_name = "%s_%s.csv" % (self.scenario_id, kind)
            profile.to_csv(os.path.join(server_setup.LOCAL_DIR, file_name))

            self._data_access.move_to(
                file_name, self.REL_TMP_DIR, change_name_to=f"{kind}.csv"
            )
        else:
            from_dir = self._data_access.match_scenario_files(profile_as, "tmp")
            to_dir = self.TMP_DIR
            self._data_access.copy(f"{from_dir}/{kind}.csv", to_dir)
