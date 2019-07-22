class State(object):
    """Defines an interface for encapsulating the behavior associated with a
        particular state of the Scenario object.
    """

    name = "state"
    allowed = []

    def switch(self, state):
        """Switches state.

        :param class state: One of :class:`.Analyze` :class:`.Create`,
            :class:`.Execute`.
        """
        if state.name in self.allowed:
            print('State switching: %s --> %s' % (self, state.name))
            self._leave()
            self.__class__ = state
            self._enter()
        else:
            print('State switching: %s -/-> %s' % (self, state.name))

    def __str__(self):
        """

        :return: (*str*) -- state name.
        """
        return self.name

    def _leave(self):
        """Cleans when leaving state.

        """
        if self.name == 'create':
            del self.builder
        elif self.name == 'analyze':
            del self.scaler

    def _enter(self):
        """Initializes when entering state.

        """
        pass
