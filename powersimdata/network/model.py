from importlib import import_module


class ModelImmutables:
    """Immutables for a grid model.

    :param str model: grid model name.
    """

    def __init__(self, model):
        self._check_model(model)
        self.model = model

        self.plants = self._import_constants("plants")
        self.storage = self._import_constants("storage")
        self.zones = self._import_constants("zones")

        mod = import_module(f"powersimdata.network.{self.model}.model")
        self.area_to_loadzone = getattr(mod, "area_to_loadzone")
        self.check_interconnect = getattr(mod, "check_interconnect")
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

        :param str kind: either *'plants'*, *'zones'* or *'zones'*.
        :return: (*dict*) -- constants of the grid model
        """
        mod = import_module(f"powersimdata.network.{self.model}.constants.{kind}")
        return {a: getattr(mod, a) for a in dir(mod)}
