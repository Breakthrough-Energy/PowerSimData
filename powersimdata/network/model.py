from importlib import import_module


class ModelImmutables:
    """Immutables for a grid model.

    :param str model: grid model name.
    """

    def __init__(self, model):
        """Constructor."""
        self._check_model(model)
        self.model = model

        self.plants = self._import_constants("plants")
        self.storage = self._import_constants("storage")
        self.zones = self._import_constants("zones")

        mod = import_module(f"powersimdata.network.{self.model}.model")
        self.check_and_format_interconnect = getattr(
            mod, "check_and_format_interconnect"
        )
        self.interconnect_to_name = getattr(mod, "interconnect_to_name")

    @staticmethod
    def _check_model(model):
        """Check that a grid model exists.

        :param str model: grid model name
        :raises ValueError: if grid model does not exist.
        """
        possible = {"usa_tamu"}
        if model not in possible:
            raise ValueError("model must be one of %s" % " | ".join(possible))

    def _import_constants(self, kind):
        """Import constants related to the grid model.

        :param str kind: either *'plants'*, *'storage'* or *'zones'*.
        :return: (*dict*) -- constants of the grid model
        """
        mod = import_module(f"powersimdata.network.{self.model}.constants.{kind}")
        return {a: getattr(mod, a) for a in dir(mod)}

    def area_to_loadzone(self, *args, **kwargs):
        """Map the query area to a list of loadzones, using the known grid model."""
        return area_to_loadzone(
            self.model, *args, mappings=self.zones["mappings"], **kwargs
        )


def area_to_loadzone(grid_model, area, area_type=None, mappings=None):
    """Map the query area to a list of loadzones.

    :param str grid_model: the grid model to use to look up constants for mapping.
    :param str area: one of: *loadzone*, *state*, *state abbreviation*,
        *interconnect*, *'all'*.
    :param str area_type: one of: *'loadzone'*, *'state'*, *'state_abbr'*,
        *'interconnect'*.
    :param iterable mappings: a set of strings, representing area types to use to map.
        If None, all mappings are tried.
    :return: (*set*) -- set of loadzone names associated with the query area.
    :raises TypeError: if area is not None or str.
    :raises ValueError: if area is invalid or the combination of area and area_type is
        invalid.
    :raises KeyError: if a mapping is provided which isn't present for a grid_model.

    .. note:: if area_type is not specified, the function will check the area in the
        order of 'state', 'loadzone', 'state abbreviation', 'interconnect' and 'all'.
    """

    def raise_invalid_area(area_type):
        raise ValueError("Invalid area for area_type=%s" % area_type)

    zones = ModelImmutables(grid_model).zones
    mappings = {"loadzone", "state", "state_abbr", "interconnect"}

    if area_type is not None and not isinstance(area_type, str):
        raise TypeError("'area_type' should be either None or str.")
    if area_type:
        if area_type == "loadzone" and "loadzone" in mappings:
            if area in zones["loadzone"]:
                loadzone_set = {area}
            else:
                raise_invalid_area(area_type)
        elif area_type == "state" and "state" in mappings:
            if area in zones["abv2state"].values():
                loadzone_set = zones["state2loadzone"][area]
            else:
                raise_invalid_area(area_type)
        elif area_type == "state_abbr" and "state_abbr" in mappings:
            if area in zones.abv2state:
                loadzone_set = zones["state2loadzone"][zones["abv2state"][area]]
            else:
                raise_invalid_area(area_type)
        elif area_type == "interconnect" and "interconnect" in mappings:
            if area in zones["interconnect2loadzone"]:
                loadzone_set = zones["interconnect2loadzone"][area]
            else:
                raise_invalid_area(area_type)
        else:
            print(f"{area_type} is incorrect. Available area_types are: {mappings}.")
            raise ValueError("Invalid area_type")
    else:
        if "state" in mappings and area in zones["abv2state"].values():
            loadzone_set = zones["state2loadzone"][area]
        elif "loadzone" in mappings and area in zones["loadzone"]:
            loadzone_set = {area}
        elif "state" in mappings and area in zones["abv2state"]:
            loadzone_set = zones["state2loadzone"][zones["abv2state"][area]]
        elif "interconnect" in mappings and area in zones["interconnect2loadzone"]:
            loadzone_set = zones["interconnect2loadzone"][area]
        elif area == "all":
            loadzone_set = zones["loadzone"]
        else:
            print("%s is incorrect." % area)
            raise ValueError("Invalid area")
    return loadzone_set
