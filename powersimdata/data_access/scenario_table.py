from powersimdata.data_access.sql_store import SqlStore, to_data_frame


class ScenarioTable(SqlStore):
    """Storage abstraction for scenario list using sql database."""

    table = "scenario_list"
    columns = [
        "id",
        "plan",
        "name",
        "state",
        "grid_model",
        "interconnect",
        "base_demand",
        "base_hydro",
        "base_solar",
        "base_wind",
        "change_table",
        "start_date",
        "end_date",
        "interval",
        "engine",
        "runtime",
        "infeasibilities",
    ]

    def get_scenario_by_id(self, scenario_id):
        """Get entry from scenario list by id

        :param str scenario_id: scenario id
        :return: (*pandas.DataFrame*) -- results as a data frame.
        """
        query = self.select_where("id")
        self.cur.execute(query, (scenario_id,))
        result = self.cur.fetchmany()
        return to_data_frame(result)

    def get_scenario_table(self, limit=None):
        """Returns scenario table from database

        :return: (*pandas.DataFrame*) -- scenario list as a data frame.
        """
        query = self.select_all()
        self.cur.execute(query)
        if limit is None:
            result = self.cur.fetchall()
        else:
            result = self.cur.fetchmany(limit)
        return to_data_frame(result)

    def add_entry(self, scenario_info):
        """Adds scenario to the scenario list.

        :param collections.OrderedDict scenario_info: entry to add to scenario list.
        """
        sql = self.insert(subset=scenario_info.keys())
        self.cur.execute(sql, tuple(scenario_info.values()))

    def delete_entry(self, scenario_id):
        """Deletes entry in scenario list.

        :param int/str scenario_id: the id of the scenario
        """
        sql = self.delete("id")
        self.cur.execute(sql, (scenario_id,))
