import os

from powersimdata.input.abstract_grid import AbstractGrid
from powersimdata.network.hifld.constants.storage import defaults


class HIFLD(AbstractGrid):
    def __init__(self, interconnect):
        """Constructor."""
        self.top_dirname = os.path.dirname(__file__)
        self.interconnect = check_and_format_interconnect(interconnect)
        self.umbrella_interconnect = "USA"
        super().__init__()
        self.storage.update(defaults)


def check_and_format_interconnect(interconnect):
    """Checks interconnect.

    :param str/iterable interconnect: interconnect name(s).
    :return: (*list*) -- interconnect(s)
    :raises TypeError: if parameter has wrong type.
    :raises ValueError: if interconnect not found or combination of interconnect is not
        appropriate.
    """
    if isinstance(interconnect, str):
        interconnect = [interconnect]
    try:
        interconnect = sorted(set(interconnect))
    except:  # noqa
        raise TypeError("interconnect must be either str or an iterable of str")

    possible = ["Eastern", "Western", "ERCOT", "USA"]
    if any(i for i in interconnect if i not in possible):
        raise ValueError("Wrong interconnect. Choose from %s" % " | ".join(possible))
    n = len(interconnect)
    if "USA" in interconnect and n > 1:
        raise ValueError("'USA' cannot be paired")
    if n == 3:
        raise ValueError("Use 'USA' instead")

    return interconnect


def interconnect_to_name(interconnect):
    """Return name of interconnect or collection of interconnects.

    :param iterable interconnect: interconnect name(s).
    """
    return "_".join(sorted(check_and_format_interconnect(interconnect)))
