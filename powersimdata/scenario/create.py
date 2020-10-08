import copy
import os
import pickle
import posixpath
from collections import OrderedDict

import numpy as np
import pandas as pd

from powersimdata.data_access.scenario_list import ScenarioListManager
from powersimdata.input.change_table import ChangeTable
from powersimdata.input.grid import Grid
from powersimdata.input.transform_grid import TransformGrid
from powersimdata.input.transform_profile import TransformProfile
from powersimdata.scenario.execute import Execute
from powersimdata.scenario.helpers import (
    calculate_bus_demand,
    check_interconnect,
    interconnect2name,
)
from powersimdata.scenario.state import State
from powersimdata.utility import server_setup
from powersimdata.utility.transfer_data import upload


class Create(State):
    """Scenario is in a state of being created.

    :param powersimdata.scenario.scenario.Scenario scenario: scenario instance.
    """

    name = "create"
    allowed = []

    def __init__(self, scenario):
        """Constructor."""
        self.builder = None
        self.grid = None
        self.ct = None
        self._scenario_status = None
        self._scenario_info = OrderedDict(
            [
                ("plan", ""),
                ("name", ""),
                ("state", "create"),
                ("interconnect", ""),
                ("base_demand", ""),
                ("base_hydro", ""),
                ("base_solar", ""),
                ("base_wind", ""),
                ("change_table", ""),
                ("start_date", ""),
                ("end_date", ""),
                ("interval", ""),
                ("engine", ""),
            ]
        )
        super().__init__(scenario)

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

    def _generate_and_set_scenario_id(self):
        """Generates scenario id."""
        scenario_id = self._scenario_list_manager.generate_scenario_id()
        self._scenario_info["id"] = scenario_id
        self._scenario_info.move_to_end("id", last=False)

    def _add_entry_in_execute_list(self):
        """Adds scenario to the execute list file on server and update status
        information.

        """
        self._execute_list_manager.add_entry(self._scenario_info)
        self._scenario_status = "created"
        self.allowed.append("execute")

    def _upload_change_table(self):
        """Uploads change table to server."""
        print("--> Writing change table on local machine")
        self.builder.change_table.write(self._scenario_info["id"])
        print("--> Uploading change table to server")
        file_name = self._scenario_info["id"] + "_ct.pkl"
        upload(self._ssh, file_name, server_setup.LOCAL_DIR, server_setup.INPUT_DIR)
        print("--> Deleting change table on local machine")
        os.remove(os.path.join(server_setup.LOCAL_DIR, file_name))

    def get_ct(self):
        """Returns change table.

        :return: (*dict*) -- change table.
        :raises Exception: if :attr:`builder` has not been assigned yet through
            meth:`set_builder`.
        """
        if self.builder is not None:
            return copy.deepcopy(self.builder.change_table.ct)
        else:
            raise Exception("Change table does not exist yet")

    def get_grid(self):
        """Returns the Grid object.

        :return: (*powersimdata.input.grid.Grid*) -- a Grid object.
        :raises Exception: if :attr:`builder` has not been assigned yet through
            meth:`set_builder`.
        """
        if self.builder is not None:
            return self.builder.get_grid()
        else:
            raise Exception("Grid object does not exist yet")

    def get_profile(self, name):
        """Returns demand, hydro, solar or wind  profile.

        :param str name: either *'demand'*, *'hydro'*, *'solar'*, *'wind'*.
        :return: (*pandas.DataFrame*) -- profile.
        :raises Exception: if :meth:`_Builder.set_base_profile` has not been called yet.
        """
        if getattr(self.builder, name):
            profile = TransformProfile(
                self._ssh,
                {
                    "interconnect": self.builder.name,
                    "base_%s" % name: getattr(self.builder, name),
                },
                self.get_grid(),
                self.get_ct(),
            )
            return profile.get_profile(name)
        else:
            raise Exception("Set base %s profile version first" % name)

    def get_demand(self):
        """Returns demand profile.

        :return: (*pandas.DataFrame*) -- load with zone id as columns and UTC timestamp
            as index.
        """
        return self.get_profile("demand")

    def get_bus_demand(self):
        """Returns demand profiles, by bus.

        :return: (*pandas.DataFrame*) -- data frame of demand (hour, bus).
        """
        demand = self.get_profile("demand")
        grid = self.get_grid()
        return calculate_bus_demand(grid.bus, demand)

    def get_hydro(self):
        """Returns hydro profile.

        :return: (*pandas.DataFrame*) -- hydro energy output with plant id as columns
            and UTC timestamp as index.
        """
        return self.get_profile("hydro")

    def get_solar(self):
        """Returns solar profile.

        :return: (*pandas.DataFrame*) -- solar energy output with plant id as columns
            and UTC timestamp as index.
        """
        return self.get_profile("solar")

    def get_wind(self):
        """Returns wind profile.

        :return: (*pandas.DataFrame*) -- power output with plant identification number
            as columns and UTC timestamp as index.
        """
        return self.get_profile("wind")

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

            # Generate scenario id
            self._generate_and_set_scenario_id()
            # Add missing information
            self._scenario_info["state"] = "execute"
            self._scenario_info["runtime"] = ""
            self._scenario_info["infeasibilities"] = ""
            self.grid = self.builder.get_grid()
            self.ct = self.builder.change_table.ct
            # Add scenario to scenario list file on server
            self._scenario_list_manager.add_entry(self._scenario_info)
            # Upload change table to server
            if bool(self.builder.change_table.ct):
                self._upload_change_table()
            # Add scenario to execute list file on server
            self._add_entry_in_execute_list()

            print(
                "SCENARIO SUCCESSFULLY CREATED WITH ID #%s" % self._scenario_info["id"]
            )
            self.switch(Execute)

    def print_scenario_info(self):
        """Prints scenario information."""
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
        n = len(interconnect)
        if n == 1:
            if "Eastern" in interconnect:
                self.builder = Eastern(self._ssh)
            elif "Texas" in interconnect:
                self.builder = Texas(self._ssh)
            elif "Western" in interconnect:
                self.builder = Western(self._ssh)
            elif "USA" in interconnect:
                self.builder = USA(self._ssh)
        elif n == 2:
            if "Western" in interconnect and "Texas" in interconnect:
                self.builder = TexasWestern(self._ssh)
            elif "Eastern" in interconnect and "Texas" in interconnect:
                print("Not implemented yet")
                return
            elif "Eastern" in interconnect and "Western" in interconnect:
                print("Not implemented yet")
                return
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

        self._scenario_info["interconnect"] = self.builder.name


class _Builder(object):
    """Scenario Builder."""

    interconnect = None
    base_grid = None
    change_table = None
    profile = None
    existing = None
    plan_name = ""
    scenario_name = ""
    start_date = "2016-01-01 00:00:00"
    end_date = "2016-12-31 23:00:00"
    interval = "144H"
    demand = ""
    hydro = ""
    solar = ""
    wind = ""
    engine = "REISE.jl"
    name = "builder"

    def __init__(self, interconnect, ssh_client):
        """Constructor."""
        self.base_grid = Grid(interconnect)
        self.profile = CSV(interconnect, ssh_client)
        self.change_table = ChangeTable(self.base_grid)
        self._scenario_list_manager = ScenarioListManager(ssh_client)

        table = self._scenario_list_manager.get_scenario_table()
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
                raise Exception(
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
        :raises Exception: if start date, end date or interval are not properly defined.
        """
        min_ts = pd.Timestamp("2016-01-01 00:00:00")
        max_ts = pd.Timestamp("2016-12-31 23:00:00")

        start_ts = pd.Timestamp(start_date)
        end_ts = pd.Timestamp(end_date)
        hours = (end_ts - start_ts) / np.timedelta64(1, "h") + 1
        if start_ts > end_ts:
            raise Exception("start_date > end_date")
        elif start_ts < min_ts or start_ts >= max_ts:
            raise Exception("start_date not in [%s,%s[" % (min_ts, max_ts))
        elif end_ts <= min_ts or end_ts > max_ts:
            raise Exception("end_date not in ]%s,%s]" % (min_ts, max_ts))
        elif hours % int(interval.split("H", 1)[0]) != 0:
            raise Exception("Incorrect interval for start and end dates")
        else:
            self.start_date = start_date
            self.end_date = end_date
            self.interval = interval

    def get_base_profile(self, kind):
        """Returns available base profiles.

        :param str kind: one of *'demand'*, *'hydro'*, *'solar'*, *'wind'*.
        :return: (*list*) -- available version for selected profile kind.
        """
        return self.profile.get_base_profile(kind)

    def set_base_profile(self, kind, version):
        """Sets demand profile.

        :param str kind: one of *'demand'*, *'hydro'*, *'solar'*, *'wind'*.
        :param str version: demand profile version.
        :raises Exception: if no profile or selected version.
        """
        possible = self.get_base_profile(kind)
        if len(possible) == 0:
            raise Exception(
                "No %s profile available in %s" % (kind, " + ".join(self.interconnect))
            )
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
            raise Exception(
                "Available %s profiles for %s: %s"
                % (kind, " + ".join(self.interconnect), " | ".join(possible))
            )

    def set_engine(self, engine):
        """Sets simulation engine to be used for scenarion.

        :param str engine: simulation engine
        """
        possible = ["REISE", "REISE.jl"]
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

    def __str__(self):
        return self.name


class Eastern(_Builder):
    """Builder for Eastern interconnect."""

    name = "Eastern"

    def __init__(self, ssh_client):
        """Constructor."""
        self.interconnect = ["Eastern"]
        super().__init__(self.interconnect, ssh_client)


class Texas(_Builder):
    """Builder for Texas interconnect."""

    name = "Texas"

    def __init__(self, ssh_client):
        """Constructor."""
        self.interconnect = ["Texas"]
        super().__init__(self.interconnect, ssh_client)


class Western(_Builder):
    """Builder for Western interconnect.

    :param paramiko.client.SSHClient ssh_client: session with an SSH server.
    """

    name = "Western"

    def __init__(self, ssh_client):
        """Constructor."""
        self.interconnect = ["Western"]
        super().__init__(self.interconnect, ssh_client)


class TexasWestern(_Builder):
    """Builder for Texas + Western interconnect.

    :param paramiko.client.SSHClient ssh_client: session with an SSH server.
    """

    name = "Texas_Western"

    def __init__(self, ssh_client):
        """Constructor."""
        self.interconnect = ["Texas", "Western"]
        super().__init__(self.interconnect, ssh_client)


class TexasEastern(_Builder):
    """Builder for Texas + Eastern interconnect."""

    name = "Texas_Eastern"

    def __init__(self):
        """Constructor."""
        self.interconnect = ["Texas", "Eastern"]
        super().__init__(self.interconnect, ssh_client)


class EasternWestern(_Builder):
    """Builder for Eastern + Western interconnect."""

    name = "Eastern_Western"

    def __init__(self):
        """Constructor."""
        self.interconnect = ["Eastern", "Western"]
        super().__init__(self.interconnect, ssh_client)


class USA(_Builder):
    """Builder for USA interconnect."""

    name = "USA"

    def __init__(self, ssh_client):
        """Constructor."""
        self.interconnect = ["USA"]
        super().__init__(self.interconnect, ssh_client)


class CSV(object):
    """Profiles handler.

    :param list interconnect: interconnect(s)
    :param paramiko.client.SSHClient ssh_client: session with an SSH server.
    """

    def __init__(self, interconnect, ssh_client):
        """Constructor."""
        self._ssh = ssh_client
        self.interconnect = interconnect

    def get_base_profile(self, kind):
        """Returns available base profiles.

        :param str kind: one of *'demand'*, *'hydro'*, *'solar'*, *'wind'*.
        :return: (*list*) -- available version for selected profile kind.
        """
        possible = ["demand", "hydro", "solar", "wind"]
        if kind not in possible:
            raise NameError("Choose from %s" % " | ".join(possible))

        available = interconnect2name(self.interconnect) + "_" + kind + "_*"
        query = posixpath.join(server_setup.BASE_PROFILE_DIR, available)
        stdin, stdout, stderr = self._ssh.exec_command("ls " + query)
        if len(stderr.readlines()) != 0:
            print("No %s profiles available." % kind)
            possible = []
        else:
            filename = [os.path.basename(line.rstrip()) for line in stdout.readlines()]
            possible = [f[f.rfind("_") + 1 : -4] for f in filename]
        return possible
