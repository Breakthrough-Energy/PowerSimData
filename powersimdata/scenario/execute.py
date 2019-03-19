from powersimdata.input.grid import Grid
from powersimdata.scenario.state import State


class Execute(State):
    """Scenario is in a state of being executed.

    """
    name = 'execute'
    allowed = ['delete']

    def init(self, scenario):
        """Initializes attributes.

        """
        pass

    def clean(self):
        """Deletes attributes prior to switching state.

        """
        pass
