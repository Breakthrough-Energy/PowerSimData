class State(object):
    """Defines an interface for encapsulating the behavior associated with a \
        particular state of the Scenario.
    """

    name = "state"
    allowed = []

    def switch(self, state):
        """Switches to new state.

        :param class state: One of the sub-classes.
        """
        if state.name in self.allowed:
            print('State switching: %s --> %s' % (self, state.name))
            self._leave()
            self.__class__ = state
            self._enter()
        else:
            print('State switching: %s -/-> %s' % (self, state.name))

    def __str__(self):
        return self.name

    def _leave(self):
        """Operations to perform when leaving state.

        """
        if self.name == 'create':
            del self.builder
        elif self.name == 'analyze':
            del self.scaler

    def _enter(self):
        """Operations to perform when entering state.

        """
        if self.name == 'create':
            self.__init__()
