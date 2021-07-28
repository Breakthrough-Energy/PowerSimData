class State:
    """Defines an interface for encapsulating the behavior associated with a
    particular state of the Scenario object.

    :param powersimdata.scenario.scenario.Scenario scenario: scenario instance
    :raise TypeError: if not instantiated through a derived class
    """

    name = "state"
    allowed = []
    exported_methods = {"print_scenario_info"}

    def __init__(self, scenario):
        """Constructor."""
        if type(self) == State:
            raise TypeError("Only subclasses of 'State' can be instantiated directly")

        self._scenario = scenario
        self._scenario_info = scenario.info
        self._scenario_status = scenario.status
        self._data_access = scenario.data_access
        self._scenario_list_manager = scenario._scenario_list_manager
        self._execute_list_manager = scenario._execute_list_manager

    def refresh(self, scenario):
        """Called during state changes to ensure instance is properly initialized

        :param powersimdata.scenario.scenario.Scenario scenario: scenario instance
        """
        pass

    def _update_scenario_info(self):
        """Override this method if applicable"""
        pass

    def print_scenario_info(self):
        """Prints scenario information."""
        print("--------------------")
        print("SCENARIO INFORMATION")
        print("--------------------")
        try:
            self._update_scenario_info()
            for key, val in self._scenario_info.items():
                print("%s: %s" % (key, val))
        except AttributeError:
            print("Scenario has been deleted")

    def switch(self, state):
        """Switches state.

        :param class state: One of :class:`.Analyze`, :class:`.Create`,
            :class:`.Execute`, :class:`.Delete`, :class:`.Move`.
        """
        if state.name in self.allowed:
            print("State switching: %s --> %s" % (self, state.name))
            self._leave()
            self.__class__ = state
            self._enter(state)
            self.refresh(self._scenario)
        else:
            raise Exception(
                "State switching: %s --> %s not permitted" % (self, state.name)
            )

    def __str__(self):
        """

        :return: (*str*) -- state name.
        """
        return self.name

    def _leave(self):
        """Cleans when leaving state."""
        pass

    def _enter(self, state):
        """Initializes when entering state."""
        self.exported_methods = state.exported_methods
