from powersimdata.data_access.sql_store import SqlStore, to_data_frame


class ExecuteTable(SqlStore):
    """Storage abstraction for execute list using sql database."""

    table = "execute_list"
    columns = ["id", "status"]

    def get_status(self, scenario_id):
        """Get status of scenario by scenario_id

        :param str scenario_id: the scenario id
        :return: (*pandas.DataFrame*) -- results as a data frame.
        """
        query = self.select_where("id")
        self.cur.execute(query, (scenario_id,))
        result = self.cur.fetchmany()
        return to_data_frame(result)

    def get_execute_table(self, limit=None):
        """Return the execute table as a data frame

        :return: (*pandas.DataFrame*) -- execute list as a data frame.
        """
        query = self.select_all()
        self.cur.execute(query)
        if limit is None:
            result = self.cur.fetchall()
        else:
            result = self.cur.fetchmany(limit)
        return to_data_frame(result)

    def add_entry(self, scenario_info):
        """Add entry to execute list

        :param collections.OrderedDict scenario_info: entry to add
        """
        scenario_id, status = scenario_info["id"], "created"
        sql = self.insert()
        self.cur.execute(
            sql,
            (
                scenario_id,
                status,
            ),
        )

    def set_status(self, scenario_id, status):
        """Updates status of scenario in execute list

        :param int scenario_id: the scenario id
        :param str status: execution status.
        """
        self.cur.execute(
            "UPDATE execute_list SET status = %s WHERE id = %s",
            (status, scenario_id),
        )

    def delete_entry(self, scenario_id):
        """Deletes entry from execute list.

        :param int/str scenario_id: the id of the scenario
        """
        sql = self.delete("id")
        self.cur.execute(sql, (scenario_id,))
