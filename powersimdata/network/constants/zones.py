from importlib import import_module

from powersimdata.network.constants.model import model2region


def get_zones(interconnect, model):
    """Return zone constants.

    :para list interconnect: interconnect(s).
    :param str model: the grid model.
    :return: (*func*) -- function returning information on zones for a given model.
    """
    mod = import_module(
        f"powersimdata.network.constants.region.{model2region[model].lower()}"
    )
    zones = getattr(mod, "get_zones")

    return zones(interconnect, model)
