from powersimdata.input.grid import Grid
from powersimdata.scenario.state import State


class Execute(State):
    """Scenario is in a state of being executed.

    """
    name = 'execute'
    allowed = ['delete']

    def __init__(self, scenario):
        """Initializes attributes.

        """
        pass
