class DivisionMapping:
    """State/Country mapping for grid models.

    :param pandas.DataFrame zone: information on zones of a grid model.
    """

    def __init__(self, zone):
        self.abv = set(zone["abv"])
        self.abv2loadzone = zone.groupby("abv")["zone_name"].apply(set).to_dict()
        self.abv2id = zone.reset_index().groupby("abv")["zone_id"].apply(set).to_dict()
        self.id2abv = zone["abv"].to_dict()
        self.abv2interconnect = dict(zip(zone["abv"], zone["interconnect"]))


class USADivisionMapping(DivisionMapping):
    """State mapping for USA grid models

    :param pandas.DataFrame zone: information on zones of a grid model.
    """

    def __init__(self, zone):
        super().__init__(zone)
        self.state = set(zone["state"])
        self.state_abbr = set(zone["abv"])
        self.state2loadzone = zone.groupby("state")["zone_name"].apply(set).to_dict()
        self.state2abv = dict(zip(zone["state"], zone["abv"]))
        self.abv2state = dict(zip(zone["abv"], zone["state"]))


class EUDivisionMapping(DivisionMapping):
    """Country mapping for EU grid models

    :param pandas.DataFrame zone: information on zones of a grid model.
    """

    def __init__(self, zone):
        super().__init__(zone)
        self.country = set(zone["country"])
        self.country_abbr = set(zone["country"])
        self.country2loadzone = (
            zone.groupby("country")["zone_name"].apply(set).to_dict()
        )
        self.country2abv = dict(zip(zone["country"], zone["abv"]))
        self.abv2country = dict(zip(zone["abv"], zone["country"]))


def get_division_mapping(model, zone):
    """Return division mappings for a grid model.

    :param str model: grid model.
    :param pandas.DataFrame zone: information on zones of a grid model.
    """
    _lookup = {
        "usa_tamu": USADivisionMapping,
        "hifld": USADivisionMapping,
        "europe_tub": EUDivisionMapping,
    }
    return _lookup[model](zone).__dict__
