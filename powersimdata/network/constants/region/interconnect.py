import ast

from powersimdata.network.constants.model import model2region
from powersimdata.network.constants.region.geography import format, get_geography
from powersimdata.network.helpers import powerset


class InterconnectMapping:
    """Interconnect mapping for grid models

    :param str model: grid model.
    :param pandas.DataFrame zone: information on zones of a grid model.
    """

    def __init__(self, model, zone):
        geo = get_geography(model)
        region = model2region[model]

        self.interconnect = {
            ast.literal_eval(repr(format(c)).replace(geo["sub"][region], region))
            for c in powerset(zone["interconnect"].unique(), 1)
        }
        self.interconnect2timezone = {
            i: geo["interconnect2timezone"][i] for i in self.interconnect
        }
        self.name2interconnect = {
            i: geo["name2interconnect"][i] for i in self.interconnect
        }
        self.name2component = {i: geo["name2component"][i] for i in self.interconnect}
        self.interconnect2loadzone = (
            zone.groupby("interconnect")["zone_name"].apply(set).to_dict()
        )
        self.interconnect2id = (
            zone.reset_index().groupby("interconnect")["zone_id"].apply(set).to_dict()
        )
        self.interconnect2abv = zone.groupby("interconnect")["abv"].apply(set).to_dict()


def get_interconnect_mapping(model, zone):
    """Return interconnect mappings for a grid model.

    :param str model: grid model
    :param pandas.DataFrame zone: information on zones of a grid model.
    """
    return InterconnectMapping(model, zone).__dict__
