class LoadzoneMapping:
    """Loadzone mapping for grid models

    :param pandas.DataFrame zone: information on zones of a grid model.
    """

    def __init__(self, zone):
        self.loadzone = set(zone["zone_name"])
        self.id2timezone = zone["time_zone"].to_dict()
        self.id2loadzone = zone["zone_name"].to_dict()
        self.timezone2id = (
            zone.reset_index().groupby("time_zone")["zone_id"].apply(set).to_dict()
        )
        self.loadzone2id = (
            zone.reset_index().groupby("zone_name")["zone_id"].apply(int).to_dict()
        )
        self.loadzone2abv = dict(zip(zone["zone_name"], zone["abv"]))
        self.loadzone2interconnect = dict(zip(zone["zone_name"], zone["interconnect"]))


class USALoadzoneMapping(LoadzoneMapping):
    """Loadzone mapping for USA grid models

    :param pandas.DataFrame zone: information on zones of a grid model.
    """

    def __init__(self, zone):
        super().__init__(zone)
        self.loadzone2state = dict(zip(zone["zone_name"], zone["state"]))


class EULoadzoneMapping(LoadzoneMapping):
    """Loadzone mapping for EU grid models

    :param pandas.DataFrame zone: information on zones of a grid model.
    """

    def __init__(self, zone):
        super().__init__(zone)
        self.loadzone2country = dict(zip(zone["zone_name"], zone["country"]))


def get_loadzone_mapping(model, zone):
    """Return loadzone mappings for a grid model.

    :param str model: grid model
    :param pandas.DataFrame zone: information on zones of a grid model.
    """
    _lookup = {
        "usa_tamu": USALoadzoneMapping,
        "hifld": USALoadzoneMapping,
        "europe_tub": EULoadzoneMapping,
    }
    return _lookup[model](zone).__dict__
