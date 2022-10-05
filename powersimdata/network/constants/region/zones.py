from importlib import import_module

from powersimdata.network.constants.model import model2region
from powersimdata.network.helpers import check_model


def get_zones(interconnect, model):
    """Return zone constants.

    :para list interconnect: interconnect(s).
    :param str model: the grid model.
    :return: (*func*) -- function returning information on zones for a given model.
    """
    check_model(model)

    mod = import_module(
        f"powersimdata.network.constants.region.{model2region[model].lower()}"
    )
    zones = getattr(mod, "get_zones")

    return zones(interconnect, model)
