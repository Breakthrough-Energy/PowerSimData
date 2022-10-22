from powersimdata.network.constants.carrier.plants import get_plants
from powersimdata.network.constants.carrier.storage import get_storage
from powersimdata.network.constants.model import model2region
from powersimdata.network.constants.region.mapping import get_mapping
from powersimdata.network.constants.region.zones import check_zone, from_csv
from powersimdata.network.helpers import (
    check_and_format_interconnect,
    check_model,
    interconnect_to_name,
)


class ModelImmutables:
    """Immutables for a grid model.

    :param str model: grid model name.
    :param str interconnect: interconnect of grid model.
    :param pandas.DataFrame zone: a data frame with loadzone name (*'zone_name'*),
        division name (e.g. *'state'* name for USA grid models), interconnect name
        (*'interconnect'*), time zone of loadzone (*'time_zone'*) and division
        abbreviation (*'abv'*) as columns; and loadzone id (*'zone_id'*) as indices. If
        None, it will be assumed that the data frame can be built from a CSV file
        stored on disk.
    """

    def __init__(self, model, interconnect=None, zone=None):
        """Constructor."""
        check_model(model)
        self.model = model
        interconnect = (
            [model2region[model]]
            if interconnect is None
            else check_and_format_interconnect(interconnect, model=model)
        )
        if zone is None:
            zone = from_csv(self.model)
        else:
            check_zone(model, zone)

        self.plants = get_plants(model)
        self.storage = get_storage(model)
        self.zones = get_mapping(model, interconnect, zone)

        self.check_and_format_interconnect = check_and_format_interconnect
        self.interconnect_to_name = interconnect_to_name

    def area_to_loadzone(self, *args, **kwargs):
        """Map the query area to a list of loadzones, using the known grid model."""
        return area_to_loadzone(self.model, *args, **kwargs)


def area_to_loadzone(model, area, area_type=None, zone=None):
    """Map the query area to a list of loadzones.

    :param str model: grid model to use to look up constants for mapping.
    :param str area: one of *loadzone*, *state*, *state abbreviation*,
        *interconnect*, *'all'*.
    :param str area_type: one of *'loadzone'*, *'state'*/*'country'*,
        *'state_abbr'*/'*country_abbr*', *'interconnect'*. If None, ``area`` will be
        searched successively into *'state'*/*'country'*, *'loadzone'*,
        *'state abbreviation'*/*'country abbreviation'*, *'interconnect'* and *'all'*.
    :param pandas.DataFrame zone: a data frame with loadzone name (*'zone_name'*),
        division name (e.g. *'state'* name for USA grid models), interconnect name
        (*'interconnect'*), time zone of loadzone (*'time_zone'*) and division
        abbreviation (*'abv'*) as columns; and loadzone id (*'zone_id'*) as indices. If
        None, it will be assumed that the data frame can be built from a CSV file
        stored on disk.
    :return: (*set*) -- set of loadzone names located in the query area.
    :raises TypeError:
        if ``area`` is not a str.
        if ``area_type`` is not None or str.
    :raises ValueError:
        if ``area`` is invalid
        if combination of ``area`` and ``area_type`` is invalid.
    """
    zones = ModelImmutables(model, zone=zone).zones
    mappings = zones["mappings"]
    division = zones["division"]

    if not isinstance(area, str):
        raise TypeError("area must be a str")

    if area_type is not None and not isinstance(area_type, str):
        raise TypeError("area_type must be either None or str")

    area2loadzone = {
        f"{division}": zones[f"{division}2loadzone"].get,
        "loadzone": lambda x: zones["loadzone"].intersection({x}),
        f"{division}_abbr": zones["abv2loadzone"].get,
        "interconnect": zones["interconnect2loadzone"].get,
        "all": lambda _: zones["loadzone"],
    }

    if area_type:
        if area_type not in mappings:
            raise ValueError(f"Invalid area type. Choose among {' | '.join(mappings)}")
        if area not in zones[area_type]:
            raise ValueError("Invalid area / area_type combination")
        loadzone = area2loadzone[area_type](area)
    else:
        zones["all"] = "all"
        loadzone = set().union(
            *(area2loadzone[a](area) for a in area2loadzone if area in zones[a])
        )
        if len(loadzone) == 0:
            raise ValueError("Invalid area")

    return loadzone
