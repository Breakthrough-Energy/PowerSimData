from powersimdata.network.constants.model import model2interconnect, model2region
from powersimdata.network.constants.region.division import get_division_mapping
from powersimdata.network.constants.region.interconnect import get_interconnect_mapping
from powersimdata.network.constants.region.loadzone import get_loadzone_mapping


class Mapping:
    """Geographical/time mapping for USA grid models

    :param str model: grid model.
    :param list interconnect: interconnect(s)
    :param pandas.DataFrame info: information on zones of a grid model.
    """

    def __init__(self, model, interconnect, info):
        self.zones = dict()

        interconnect = (  # noqa
            model2interconnect[model]
            if model2region[model] in interconnect
            else interconnect
        )
        zone = info.query("interconnect == @interconnect")
        self.zones.update(get_loadzone_mapping(model, zone))
        self.zones.update(get_division_mapping(model, zone))
        self.zones.update(get_interconnect_mapping(model, zone))


class USAMapping(Mapping):
    """Geographical/time mapping for USA grid models

    :param str model: grid model.
    :param list interconnect: interconnect(s)
    :param pandas.DataFrame info: information on zones of a grid model.
    """

    def __init__(self, model, interconnect, info):
        super().__init__(model, interconnect, info)
        self.zones["mappings"] = {"state_abbr", "state", "loadzone", "interconnect"}
        self.zones["division"] = "state"


class EUMapping(Mapping):
    """Geographical/time mapping for EU grid models

    :param str model: grid model.
    :param list interconnect: interconnect(s)
    :param pandas.DataFrame info: information on zones of a grid model.
    """

    def __init__(self, model, interconnect, info):
        super().__init__(model, interconnect, info)
        self.zones["mappings"] = {"country_abbr", "country", "loadzone", "interconnect"}
        self.zones["division"] = "country"


def get_mapping(model, interconnect, info):
    """Return interconnect mappings for a grid model.

    :param str model: grid model.
    :param list interconnect: interconnect(s)
    :param pandas.DataFrame info: information on zones of a grid model.
    """
    _lookup = {
        "usa_tamu": USAMapping,
        "hifld": USAMapping,
        "europe_tub": EUMapping,
    }
    return _lookup[model](model, interconnect, info).zones
