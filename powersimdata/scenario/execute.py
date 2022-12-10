import pickle

import pandas as pd

from powersimdata.data_access.context import Context
from powersimdata.input.configure import adjust_pmin, adjust_ramp30, linearize_gencost
from powersimdata.input.grid import Grid
from powersimdata.input.input_data import InputData
from powersimdata.input.transform_grid import TransformGrid
from powersimdata.input.transform_profile import TransformProfile
from powersimdata.scenario.ready import Ready
from powersimdata.utility.config import get_deployment_mode


class Execute(Ready):
    """Scenario is in a state of being executed.

    :param powersimdata.scenario.scenario.Scenario scenario: scenario instance.
    """

    name = "execute"
    allowed = ["delete"]
    exported_methods = {
        "check_progress",
        "extract_simulation_output",
        "launch_simulation",
        "prepare_simulation_input",
        "print_scenario_status",
        "scenario_id",
    } | Ready.exported_methods

    def __init__(self, scenario):
        """Constructor."""
        super().__init__(scenario)
        self.refresh(scenario)

    @property
    def scenario_id(self):
        """Get the current scenario id

        :return: (*str*) -- scenario id
        """
        return self._scenario_info["id"]

    def refresh(self, scenario):
        """Called during state changes to ensure instance is properly initialized

        :param powersimdata.scenario.scenario.Scenario scenario: scenario instance
        """
        print(
            "SCENARIO: %s | %s\n"
            % (self._scenario_info["plan"], self._scenario_info["name"])
        )
        print("--> State\n%s" % self.name)
        print("--> Status\n%s" % self._scenario_status)

        self._set_ct_and_grid()
        self._launcher = Context.get_launcher(scenario)

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

    def _update_scenario_status(self):
        """Updates scenario status."""
        self._scenario_status = self._execute_list_manager.get_status(self.scenario_id)

    def _update_scenario_info(self):
        """Updates scenario information."""
        self._scenario_info = self._scenario_list_manager.get_scenario(self.scenario_id)

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
            for p in ["demand", "hydro", "solar", "wind"]:
                si.prepare_profile(p, profiles_as)

            si.prepare_grid()

            if "demand_flexibility" in self.ct:
                # Prepare all specified demand flexibility profiles
                for p in list(self.ct["demand_flexibility"]):
                    if p != "demand_flexibility_duration":
                        si.prepare_profile(p, profiles_as)

                si.prepare_demand_flexibility_parameters()

            prepared = "prepared"
            self._execute_list_manager.set_status(self.scenario_id, prepared)
            self._scenario_status = prepared
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

    def launch_simulation(self, threads=None, solver=None, extract_data=True):
        """Launches simulation on target environment

        :param int/None threads: the number of threads to be used. This defaults to None,
            where None means auto.
        :param str solver: the solver used for optimization. This defaults to
            None, which translates to gurobi
        :param bool extract_data: whether the results of the simulation engine should
            automatically extracted after the simulation has run. This defaults to True.
        :return: (*subprocess.Popen*) or (*dict*) - the process, if using ssh to server,
            otherwise a dict containing status information.
        """
        self._check_if_ready()

        mode = get_deployment_mode()
        print(f"--> Launching simulation on {mode.lower()}")
        return self._launcher.launch_simulation(threads, solver, extract_data)

    def check_progress(self):
        """Get the status of an ongoing simulation, if possible

        :return: (*dict*) -- either None if using ssh, or a dict which contains
            "output", "errors", "scenario_id", and "status" keys which map to
            stdout, stderr, and the respective scenario attributes
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


class SimulationInput:
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

        self.REL_TMP_DIR = self._data_access.tmp_folder(self.scenario_id)

    def prepare_grid(self):
        """Prepare grid for simulation."""
        print("--> Preparing grid data")
        grid = self.grid
        storage = grid.storage

        adjust_pmin(grid)
        adjust_ramp30(grid.plant)
        grid.gencost["after"] = linearize_gencost(grid.gencost["before"], grid.plant)
        storage["gencost"] = linearize_gencost(storage["gencost"], storage["gen"])

        dest_path = "/".join([self.REL_TMP_DIR, "grid.pkl"])
        with self._data_access.write(dest_path, save_local=False) as f:
            pickle.dump(self.grid, f)

    def prepare_profile(self, kind, profile_as=None, slice=False):
        """Prepares profile for simulation.

        :param kind: one of *demand*, *'hydro'*, *'solar'*, *'wind'*,
            *'demand_flexibility_up'*, *'demand_flexibility_dn'*,
            *'demand_flexibility_cost_up'*, or *'demand_flexibility_cost_dn'*.
        :param int/str profile_as: if given, copy profile from this scenario.
        :param bool slice: whether to slice the profiles by the Scenario's time range.
        """
        file_name = f"{kind}.csv"
        dest_path = "/".join([self.REL_TMP_DIR, file_name])
        if profile_as is None:
            tp = TransformProfile(self._scenario_info, self.grid, self.ct, slice)
            profile = tp.get_profile(kind)
            with self._data_access.write(dest_path, save_local=False) as f:
                profile.to_csv(f)
        else:
            from_dir = self._data_access.tmp_folder(profile_as)
            src = "/".join([from_dir, file_name])
            self._data_access.fs.copy(src, dest_path)

    def prepare_demand_flexibility_parameters(self):
        """Prepares demand_flexibility parameters file for simulation."""
        params = {}
        params["enabled"] = [True]
        params["interval_balance"] = [True]
        params["rolling_balance"] = [
            True
            if "demand_flexibility_duration" in self.ct["demand_flexibility"]
            else False
        ]
        params["duration"] = [
            self.ct["demand_flexibility"]["demand_flexibility_duration"]
            if "demand_flexibility_duration" in self.ct["demand_flexibility"]
            else 0
        ]
        params = pd.DataFrame.from_dict(params)

        dest_path = "/".join([self.REL_TMP_DIR, "demand_flexibility_parameters.csv"])
        with self._data_access.write(dest_path, save_local=False) as f:
            params.to_csv(f)
