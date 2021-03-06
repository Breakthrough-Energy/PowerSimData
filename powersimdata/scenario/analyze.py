import copy
import os
import pickle

import pandas as pd

from powersimdata.input.grid import Grid
from powersimdata.input.input_data import InputData, get_bus_demand
from powersimdata.input.transform_profile import TransformProfile
from powersimdata.output.output_data import OutputData, construct_load_shed
from powersimdata.scenario.state import State
from powersimdata.utility import server_setup


class Analyze(State):
    """Scenario is in a state of being analyzed.

    :param powersimdata.scenario.scenario.Scenario scenario: scenario instance.
    """

    name = "analyze"
    allowed = []
    exported_methods = {
        "get_averaged_cong",
        "get_bus_demand",
        "get_congl",
        "get_congu",
        "get_ct",
        "get_demand",
        "get_hydro",
        "get_grid",
        "get_dcline_pf",
        "get_lmp",
        "get_load_shed",
        "get_pf",
        "get_pg",
        "get_solar",
        "get_storage_e",
        "get_storage_pg",
        "get_wind",
        "print_infeasibilities",
        "print_scenario_info",
    }

    def __init__(self, scenario):
        """Constructor."""
        self._scenario_info = scenario.info
        self._scenario_status = scenario.status
        super().__init__(scenario)

        self.data_loc = "disk" if scenario.status == "moved" else None

        print(
            "SCENARIO: %s | %s\n"
            % (self._scenario_info["plan"], self._scenario_info["name"])
        )
        print("--> State\n%s" % self.name)

        self._set_allowed_state()
        self._set_ct_and_grid()

    def _set_allowed_state(self):
        """Sets allowed state."""
        if self._scenario_status == "extracted":
            self.allowed = ["delete", "move"]

    def _set_ct_and_grid(self):
        """Sets change table and grid."""
        input_data = InputData(data_loc=self.data_loc)
        grid_mat_path = input_data.get_data(self._scenario_info, "grid")
        self.grid = Grid(
            interconnect=[None],
            source=grid_mat_path,
            engine=self._scenario_info["engine"],
        )

        if self._scenario_info["change_table"] == "Yes":
            self.ct = input_data.get_data(self._scenario_info, "ct")
        else:
            self.ct = {}

    def print_scenario_info(self):
        """Prints scenario information."""
        print("--------------------")
        print("SCENARIO INFORMATION")
        print("--------------------")
        for key, val in self._scenario_info.items():
            print("%s: %s" % (key, val))

    def _parse_infeasibilities(self):
        """Parses infeasibilities. When the optimizer cannot find a solution in a time
        interval, the remedy is to decrease demand by some amount until a solution is
        found. The purpose of this function is to get the interval number(s) and the
        associated decrease(s).

        :return: (*dict*) -- keys are the interval number and the values are
            the decrease in percent (%) applied to the original demand profile.
        """
        field = self._scenario_info["infeasibilities"]
        if field == "":
            return None
        else:
            infeasibilities = {}
            for entry in field.split("_"):
                item = entry.split(":")
                infeasibilities[int(item[0])] = int(item[1])
            return infeasibilities

    def print_infeasibilities(self):
        """Prints infeasibilities."""
        infeasibilities = self._parse_infeasibilities()
        if infeasibilities is None:
            print("There are no infeasibilities.")
        else:
            dates = pd.date_range(
                start=self._scenario_info["start_date"],
                end=self._scenario_info["end_date"],
                freq=self._scenario_info["interval"],
            )
            for key, value in infeasibilities.items():
                print(
                    "demand in %s - %s interval has been reduced by %d%%"
                    % (
                        dates[key],
                        dates[key] + pd.Timedelta(self._scenario_info["interval"]),
                        value,
                    )
                )

    def get_pg(self):
        """Returns PG data frame.

        :return: (*pandas.DataFrame*) -- data frame of power generated.
        """
        output_data = OutputData(data_loc=self.data_loc)
        pg = output_data.get_data(self._scenario_info["id"], "PG")

        return pg

    def get_pf(self):
        """Returns PF data frame.

        :return: (*pandas.DataFrame*) -- data frame of power flow.
        """
        output_data = OutputData(data_loc=self.data_loc)
        pf = output_data.get_data(self._scenario_info["id"], "PF")

        return pf

    def get_dcline_pf(self):
        """Returns PF_DCLINE data frame.

        :return: (*pandas.DataFrame*) -- data frame of power flow on DC line(s).
        """
        output_data = OutputData(data_loc=self.data_loc)
        dcline_pf = output_data.get_data(self._scenario_info["id"], "PF_DCLINE")

        return dcline_pf

    def get_lmp(self):
        """Returns LMP data frame. LMP = locational marginal price

        :return: (*pandas.DataFrame*) -- data frame of nodal prices.
        """
        output_data = OutputData(data_loc=self.data_loc)
        lmp = output_data.get_data(self._scenario_info["id"], "LMP")

        return lmp

    def get_congu(self):
        """Returns CONGU data frame. CONGU = Congestion, Upper flow limit

        :return: (*pandas.DataFrame*) -- data frame of branch flow mu (upper).
        """
        output_data = OutputData(data_loc=self.data_loc)
        congu = output_data.get_data(self._scenario_info["id"], "CONGU")

        return congu

    def get_congl(self):
        """Returns CONGL data frame. CONGL = Congestion, Lower flow limit

        :return: (*pandas.DataFrame*) -- data frame of branch flow mu (lower).
        """
        output_data = OutputData(data_loc=self.data_loc)
        congl = output_data.get_data(self._scenario_info["id"], "CONGL")

        return congl

    def get_averaged_cong(self):
        """Returns averaged CONGL and CONGU.

        :return: (*pandas.DataFrame*) -- data frame of averaged congestion with
            the branch id as indices an the averaged CONGL and CONGU as columns.
        """
        output_data = OutputData(data_loc=self.data_loc)
        mean_cong = output_data.get_data(self._scenario_info["id"], "AVERAGED_CONG")

        return mean_cong

    def get_storage_pg(self):
        """Returns STORAGE_PG data frame.

        :return: (*pandas.DataFrame*) -- data frame of power generated by
            storage units.
        """
        output_data = OutputData(data_loc=self.data_loc)
        storage_pg = output_data.get_data(self._scenario_info["id"], "STORAGE_PG")

        return storage_pg

    def get_storage_e(self):
        """Returns STORAGE_E data frame. Energy state of charge.

        :return: (*pandas.DataFrame*) -- data frame of energy state of charge.
        """
        output_data = OutputData(data_loc=self.data_loc)
        storage_e = output_data.get_data(self._scenario_info["id"], "STORAGE_E")

        return storage_e

    def get_load_shed(self):
        """Returns LOAD_SHED data frame, either via loading or calculating.

        :return: (*pandas.DataFrame*) -- data frame of load shed (hour x bus).
        """
        scenario_id = self._scenario_info["id"]
        try:
            # It's either on the server or in our local ScenarioData folder
            output_data = OutputData(data_loc=self.data_loc)
            load_shed = output_data.get_data(scenario_id, "LOAD_SHED")
        except OSError:
            # The scenario was run without load_shed, and we must construct it
            grid = self.get_grid()
            infeasibilities = self._parse_infeasibilities()
            load_shed = construct_load_shed(self._scenario_info, grid, infeasibilities)

            filename = scenario_id + "_LOAD_SHED.pkl"
            output_dir = server_setup.OUTPUT_DIR
            filepath = os.path.join(server_setup.LOCAL_DIR, output_dir, filename)
            with open(filepath, "wb") as f:
                pickle.dump(load_shed, f)

        return load_shed

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

    def get_demand(self, original=True):
        """Returns demand profiles.

        :param bool original: should the original demand profile or the
            potentially modified one be returned.
        :return: (*pandas.DataFrame*) -- data frame of demand (hour, zone).
        """
        profile = TransformProfile(self._scenario_info, self.get_grid(), self.get_ct())
        demand = profile.get_profile("demand")

        if original:
            return demand
        else:
            dates = pd.date_range(
                start=self._scenario_info["start_date"],
                end=self._scenario_info["end_date"],
                freq=self._scenario_info["interval"],
            )
            infeasibilities = self._parse_infeasibilities()
            if infeasibilities is None:
                print("No infeasibilities. Return original profile.")
                return demand
            else:
                for key, value in infeasibilities.items():
                    start = dates[key]
                    end = (
                        dates[key]
                        + pd.Timedelta(self._scenario_info["interval"])
                        - pd.Timedelta("1H")
                    )
                    demand[start:end] *= 1.0 - value / 100.0
                return demand

    def get_bus_demand(self):
        """Returns demand profiles, by bus.

        :return: (*pandas.DataFrame*) -- data frame of demand (hour, bus).
        """
        grid = self.get_grid()
        return get_bus_demand(self._scenario_info, grid)

    def get_hydro(self):
        """Returns hydro profile

        :return: (*pandas.DataFrame*) -- data frame of hydro energy output.
        """
        profile = TransformProfile(self._scenario_info, self.get_grid(), self.get_ct())
        return profile.get_profile("hydro")

    def get_solar(self):
        """Returns solar profile

        :return: (*pandas.DataFrame*) -- data frame of solar energy output.
        """
        profile = TransformProfile(self._scenario_info, self.get_grid(), self.get_ct())
        return profile.get_profile("solar")

    def get_wind(self):
        """Returns wind profile

        :return: (*pandas.DataFrame*) -- data frame of wind energy output.
        """
        profile = TransformProfile(self._scenario_info, self.get_grid(), self.get_ct())
        return profile.get_profile("wind")
