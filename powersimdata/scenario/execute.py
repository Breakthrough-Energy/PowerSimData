import copy
import os

from powersimdata.data_access.context import Context
from powersimdata.input.case_mat import export_case_mat
from powersimdata.input.grid import Grid
from powersimdata.input.input_data import InputData
from powersimdata.input.transform_grid import TransformGrid
from powersimdata.input.transform_profile import TransformProfile
from powersimdata.scenario.state import State
from powersimdata.utility import server_setup
from powersimdata.utility.config import get_deployment_mode


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
        "scenario_id",
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
        self._launcher = Context.get_launcher(scenario)

    @property
    def scenario_id(self):
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
        self._scenario_status = self._execute_list_manager.get_status(self.scenario_id)

    def _update_scenario_info(self):
        """Updates scenario information."""
        self._scenario_info = self._scenario_list_manager.get_scenario(self.scenario_id)

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

            self._execute_list_manager.set_status(self.scenario_id, "prepared")
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

        mode = get_deployment_mode()
        print(f"--> Launching simulation on {mode.lower()}")
        self._launcher.launch_simulation(threads, extract_data, solver)

    def check_progress(self):
        """Get the status of an ongoing simulation, if possible

        :return: (*dict*) -- progress information, or None
        """
        return self._launcher.check_progress()

    def extract_simulation_output(self):
        """Extracts simulation outputs {PG, PF, LMP, CONGU, CONGL} on server.

        :return: (*subprocess.Popen*) -- new process used to extract output
            data.
        """
        self._update_scenario_status()
        if self._scenario_status == "finished":
            return self._launcher.extract_simulation_output()
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
