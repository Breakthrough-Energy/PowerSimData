import copy
import pickle
import warnings

import numpy as np
import pandas as pd

from powersimdata.input.change_table import ChangeTable
from powersimdata.input.grid import Grid
from powersimdata.input.input_data import (
    InputData,
    distribute_demand_from_zones_to_buses,
)
from powersimdata.input.transform_grid import TransformGrid
from powersimdata.input.transform_profile import TransformProfile
from powersimdata.network.model import ModelImmutables
from powersimdata.scenario.execute import Execute
from powersimdata.scenario.state import State
from powersimdata.utility import server_setup


class Create(State):
    """Scenario is in a state of being created.

    :param powersimdata.scenario.scenario.Scenario scenario: scenario instance.
    """

    name = "create"
    allowed = []
    default_exported_methods = {
        "create_scenario",
        "get_bus_demand",
        "set_builder",
        "set_grid",
    } | State.exported_methods

    def __init__(self, scenario):
        """Constructor."""
        self.builder = None
        self.grid = None
        self.ct = None
        self.exported_methods = set(self.default_exported_methods)
        super().__init__(scenario)

    def __getattr__(self, name):
        if self.builder is not None and name in self.builder.exported_methods:
            return getattr(self.builder, name)
        if self.builder is None and name in _Builder.exported_methods:
            raise AttributeError(f"Call set_grid first to access {name} attribute")
        else:
            raise AttributeError(f"Create object has no attribute {name}")

    def __setattr__(self, name, value):
        if name in _Builder.exported_methods:
            raise AttributeError(
                f"{name} is exported from Create.builder, edit it there if necessary"
            )
        super().__setattr__(name, value)

    def _update_scenario_info(self):
        """Updates scenario information."""
        if self.builder is not None:
            self._scenario_info["plan"] = self.builder.plan_name
            self._scenario_info["name"] = self.builder.scenario_name
            self._scenario_info["start_date"] = self.builder.start_date
            self._scenario_info["end_date"] = self.builder.end_date
            self._scenario_info["interval"] = self.builder.interval
            self._scenario_info["base_demand"] = self.builder.demand
            self._scenario_info["base_hydro"] = self.builder.hydro
            self._scenario_info["base_solar"] = self.builder.solar
            self._scenario_info["base_wind"] = self.builder.wind
            self._scenario_info["engine"] = self.builder.engine
            if bool(self.builder.change_table.ct):
                self._scenario_info["change_table"] = "Yes"
            else:
                self._scenario_info["change_table"] = "No"

    def _upload_change_table(self):
        """Uploads change table to server."""
        print("--> Writing change table on local machine")
        self.builder.change_table.write(self._scenario_info["id"])
        file_name = self._scenario_info["id"] + "_ct.pkl"
        input_dir = self._data_access.join(*server_setup.INPUT_DIR)
        self._data_access.move_to(file_name, input_dir)

    def get_bus_demand(self):
        """Returns demand profiles, by bus.

        :return: (*pandas.DataFrame*) -- data frame of demand (hour, bus).
        """
        self._update_scenario_info()
        demand = self.get_demand()
        grid = self.get_grid()
        return distribute_demand_from_zones_to_buses(demand, grid.bus)

    def create_scenario(self):
        """Creates scenario."""
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
            print(
                "CREATING SCENARIO: %s | %s \n"
                % (self._scenario_info["plan"], self._scenario_info["name"])
            )

            # Add missing information
            self._scenario_info["state"] = "execute"
            self._scenario_info["runtime"] = ""
            self._scenario_info["infeasibilities"] = ""
            self.grid = self.builder.get_grid()
            self.ct = self.builder.change_table.ct
            # Add to scenario list and set the id in scenario_info
            self._scenario_list_manager.add_entry(self._scenario_info)

            if bool(self.builder.change_table.ct):
                self._upload_change_table()
            self._execute_list_manager.add_entry(self._scenario_info)
            self._scenario_status = "created"
            self.allowed.append("execute")

            print(
                "SCENARIO SUCCESSFULLY CREATED WITH ID #%s" % self._scenario_info["id"]
            )
            self.switch(Execute)

    def set_builder(self, *args, **kwargs):
        """Alias to :func:`~powersimdata.scenario.create.Create.set_grid`"""
        warnings.warn(
            "set_builder is deprecated, use set_grid instead", DeprecationWarning
        )
        self.set_grid(*args, **kwargs)

    def set_grid(self, grid_model="usa_tamu", interconnect="USA"):
        """Sets grid builder.

        :param str grid_model: name of grid model. Default is *'usa_tamu'*.
        :param str/list interconnect: name of interconnect(s). Default is *'USA'*.
        """
        self.builder = _Builder(
            grid_model, interconnect, self._scenario_list_manager.get_scenario_table()
        )
        self.exported_methods |= _Builder.exported_methods

        print("--> Summary")
        print("# Existing study")
        if self.builder.existing.empty:
            print("Nothing yet")
        else:
            plan = [p for p in self.builder.existing.plan.unique()]
            print("%s" % " | ".join(plan))

        print("# Available profiles")
        for p in ["demand", "hydro", "solar", "wind"]:
            possible = self.builder.get_base_profile(p)
            if len(possible) != 0:
                print("%s: %s" % (p, " | ".join(possible)))

        self._scenario_info["grid_model"] = self.builder.grid_model
        self._scenario_info["interconnect"] = self.builder.interconnect

    def _leave(self):
        """Cleans when leaving state."""
        del self.builder


class _Builder:
    """Scenario Builder.

    :param str grid_model: grid model.
    :param list interconnect: list of interconnect(s) to build.
    :param pandas.DataFrame table: scenario list table
    """

    plan_name = ""
    scenario_name = ""
    start_date = "2016-01-01 00:00:00"
    end_date = "2016-12-31 23:00:00"
    interval = "24H"
    demand = ""
    hydro = ""
    solar = ""
    wind = ""
    engine = "REISE.jl"
    exported_methods = {
        "set_base_profile",
        "set_engine",
        "set_name",
        "set_time",
        "get_ct",
        "get_grid",
        "get_base_grid",
        "get_demand",
        "get_hydro",
        "get_solar",
        "get_wind",
        "change_table",
    }

    def __init__(self, grid_model, interconnect, table):
        """Constructor."""
        mi = ModelImmutables(grid_model)

        self.grid_model = mi.model
        self.interconnect = mi.interconnect_to_name(interconnect)

        self.base_grid = Grid(interconnect, source=grid_model)
        self.change_table = ChangeTable(self.base_grid)

        self.existing = table[table.interconnect == self.interconnect]

    def get_ct(self):
        """Returns change table.

        :return: (*dict*) -- change table.
        """
        return copy.deepcopy(self.change_table.ct)

    def get_profile(self, kind):
        """Returns demand, hydro, solar or wind  profile.

        :param str kind: either *'demand'*, *'hydro'*, *'solar'*, *'wind'*.
        :return: (*pandas.DataFrame*) -- profile.
        """
        if getattr(self, kind):
            profile = TransformProfile(
                {
                    "grid_model": self.grid_model,
                    "base_%s" % kind: getattr(self, kind),
                },
                self.get_grid(),
                self.get_ct(),
            )
            return profile.get_profile(kind)
        else:
            raise Exception("%s profile version not set" % kind)

    def get_demand(self):
        """Returns demand profile.

        :return: (*pandas.DataFrame*) -- data frame of demand (hour, zone id).
        """
        return self.get_profile("demand")

    def get_hydro(self):
        """Returns hydro profile.

        :return: (*pandas.DataFrame*) -- data frame of hydro power output (hour, plant).
        """
        return self.get_profile("hydro")

    def get_solar(self):
        """Returns solar profile.

        :return: (*pandas.DataFrame*) -- data frame of solar power output (hour, plant).
        """
        return self.get_profile("solar")

    def get_wind(self):
        """Returns wind profile.

        :return: (*pandas.DataFrame*) -- data frame of wind power output (hour, plant).
        """
        return self.get_profile("wind")

    def set_name(self, plan_name, scenario_name):
        """Sets scenario name.

        :param str plan_name: plan name
        :param str scenario_name: scenario name.
        :raises ValueError: if combination plan - scenario already exists
        """

        if plan_name in self.existing.plan.tolist():
            scenario = self.existing[self.existing.plan == plan_name]
            if scenario_name in scenario.name.tolist():
                raise ValueError(
                    "Combination %s - %s already exists" % (plan_name, scenario_name)
                )
        self.plan_name = plan_name
        self.scenario_name = scenario_name

    def set_time(self, start_date, end_date, interval):
        """Sets scenario start and end dates as well as the interval that will
        be used to split the date range.

        :param str start_date: start date.
        :param str end_date: start date.
        :param str interval: interval.
        :raises ValueError: if start date, end date or interval are invalid.
        """
        min_ts = pd.Timestamp("2016-01-01 00:00:00")
        max_ts = pd.Timestamp("2016-12-31 23:00:00")

        start_ts = pd.Timestamp(start_date)
        end_ts = pd.Timestamp(end_date)
        hours = (end_ts - start_ts) / np.timedelta64(1, "h") + 1
        if start_ts > end_ts:
            raise ValueError("start_date > end_date")
        elif start_ts < min_ts or start_ts >= max_ts:
            raise ValueError("start_date not in [%s,%s[" % (min_ts, max_ts))
        elif end_ts <= min_ts or end_ts > max_ts:
            raise ValueError("end_date not in ]%s,%s]" % (min_ts, max_ts))
        elif hours % int(interval.split("H", 1)[0]) != 0:
            raise ValueError("Incorrect interval for start and end dates")
        else:
            self.start_date = start_date
            self.end_date = end_date
            self.interval = interval

    def get_base_profile(self, kind):
        """Returns available base profiles.

        :param str kind: one of *'demand'*, *'hydro'*, *'solar'*, *'wind'*.
        :return: (*list*) -- available version for selected profile kind.
        """
        return InputData().get_profile_version(self.grid_model, kind)

    def set_base_profile(self, kind, version):
        """Sets demand profile.

        :param str kind: one of *'demand'*, *'hydro'*, *'solar'*, *'wind'*.
        :param str version: demand profile version.
        :raises ValueError: if no profiles are available or version is not available.
        """
        possible = self.get_base_profile(kind)
        if len(possible) == 0:
            raise ValueError("No %s profile available" % kind)
        elif version in possible:
            if kind == "demand":
                self.demand = version
            if kind == "hydro":
                self.hydro = version
            if kind == "solar":
                self.solar = version
            if kind == "wind":
                self.wind = version
        else:
            raise ValueError("Available %s profiles: %s" % (kind, " | ".join(possible)))

    def set_engine(self, engine):
        """Sets simulation engine to be used for scenarion.

        :param str engine: simulation engine
        """
        possible = ["REISE.jl"]
        if engine not in possible:
            print("Available engines: %s" % " | ".join(possible))
            return
        else:
            self.engine = engine

    def load_change_table(self, filename):
        """Uploads change table.

        :param str filename: full path to change table pickle file.
        :raises FileNotFoundError: if file not found.
        """
        try:
            ct = pickle.load(open(filename, "rb"))
            self.change_table.ct = ct
        except FileNotFoundError:
            raise ("%s not found. " % filename)

    def get_grid(self):
        """Returns a transformed grid.

        :return: (*powersimdata.input.grid.Grid*) -- a Grid object.
        """
        return TransformGrid(self.base_grid, self.change_table.ct).get_grid()

    def get_base_grid(self):
        """Returns original grid.

        :return: (*powersimdata.input.grid.Grid*) -- a Grid object.
        """
        return copy.deepcopy(self.base_grid)

    def __str__(self):
        return self.name
