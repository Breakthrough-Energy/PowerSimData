from powersimdata.input.abstract_grid import AbstractGrid


class HIFLD(AbstractGrid):
    def __init__(self, interconnect):
        """Constructor."""
        super().__init__()
        self._set_data_loc()

        self.interconnect = check_and_format_interconnect(interconnect)
        self._build_network()


def check_and_format_interconnect(interconnect):
    # Placeholder for now
    return interconnect


def interconnect_to_name(interconnect):
    # Placeholder for now
    return interconnect
