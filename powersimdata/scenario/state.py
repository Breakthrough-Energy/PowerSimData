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
            print('Switching from <%s> to <%s>' % (self, state.name))
            self.__class__ = state
        else:
            print('Cannot switch from <%s> to <%s>' % (self, state.name))

    def __str__(self):
        return self.name
