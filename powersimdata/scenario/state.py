from powersimdata.data_access.execute_list import ExecuteListManager
from powersimdata.data_access.scenario_list import ScenarioListManager
from powersimdata.utility import server_setup


class State(object):
    """Defines an interface for encapsulating the behavior associated with a
        particular state of the Scenario object.

    :param powrsimdata.scenario.scenario.Scenario scenario: scenario instance
    :raise TypeError: if not instantiated through a derived class
    """

    name = "state"
    allowed = []

    def __init__(self, scenario):
        """Constructor."""
        if type(self) == State:
            raise TypeError("Only subclasses of 'State' can be instantiated directly")

        self._data_access = scenario.data_access
        self._scenario_list_manager = ScenarioListManager(self._data_access)
        self._execute_list_manager = ExecuteListManager(self._data_access)
        self.path_config = server_setup.PathConfig(server_setup.DATA_ROOT_DIR)

    def switch(self, state):
        """Switches state.

        :param class state: One of :class:`.Analyze`, :class:`.Create`,
            :class:`.Execute`, :class:`.Delete`, :class:`.Move`.
        """
        if state.name in self.allowed:
            print("State switching: %s --> %s" % (self, state.name))
            self._leave()
            self.__class__ = state
            self._enter()
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
        if self.name == "create":
            del self.builder
        elif self.name == "analyze":
            del self.grid
            del self.ct

    def _enter(self):
        """Initializes when entering state."""
        pass
