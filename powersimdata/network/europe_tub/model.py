import os

from powersimdata.input.converter.pypsa_to_grid import FromPyPSA
from powersimdata.network.constants.region.geography import get_geography
from powersimdata.network.constants.region.zones import from_pypsa
from powersimdata.network.helpers import (
    check_and_format_interconnect,
    interconnect_to_name,
)
from powersimdata.network.model import ModelImmutables
from powersimdata.network.zenodo import Zenodo
from powersimdata.utility.helpers import _check_import

pypsa = _check_import("pypsa")


class PyPSABase(FromPyPSA):
    """Arbitrary PyPSA network.

    :param str/iterable interconnect: interconnect name(s).
    :param pypsa.Network network: a PyPSA network object
    """

    def __init__(self, interconnect, network):
        """Constructor."""
        super().__init__()
        self.grid_model = "europe_tub"
        self.interconnect = check_and_format_interconnect(
            interconnect, model=self.grid_model
        )
        self.network = network

    def build(self):
        """Build network"""
        network = self.network
        id2zone = {i: l for i, l in enumerate(network.buses.index)}
        zone2id = {l: i for i, l in id2zone.items()}

        if self.interconnect == ["Europe"]:
            self.network = network
            self.id2zone = id2zone
            self.zone2id = zone2id
        else:
            geo = get_geography(self.grid_model)
            filter = list(  # noqa: F841
                geo["interconnect2abv"][
                    interconnect_to_name(self.interconnect, model=self.grid_model)
                ]
            )
            self.network = network[network.buses.query("country == @filter").index]
            self.zone2id = {l: zone2id[l] for l in self.network.buses.index}
            self.id2zone = {i: l for l, i in self.zone2id.items()}

        zone = (
            self.network.buses["country"]
            .reset_index()
            .set_axis(self.id2zone)
            .rename(columns={"Bus": "zone_name", "country": "abv"})
            .rename_axis(index="zone_id")
        )
        self.model_immutables = ModelImmutables(
            self.grid_model,
            interconnect=self.interconnect,
            zone=from_pypsa(self.grid_model, zone),
        )
        super().build(network)


class TUB(PyPSABase):
    """PyPSA Europe network.

    :param str/iterable interconnect: interconnect name(s).
    :param str zenodo_record_id: the zenodo record id. If set to None, v0.6.1 will
        be used. If set to latest, the latest version will be used.
    :param int reduction: reduction parameter (number of nodes in network). If None,
        the full network is loaded.
    """

    def __init__(self, interconnect, zenodo_record_id=None, reduction=None):
        self.from_zenodo(zenodo_record_id, reduction)
        super().__init__(interconnect, self.network)

    def from_zenodo(self, zenodo_record_id, reduction):
        """Create network from zenodo data

        :param str zenodo_record_id: the zenodo record id. If set to None, v0.6.1 will
            be used. If set to latest, the latest version will be used.
        :param int reduction: reduction parameter (number of nodes in network). If None,
            the full network is loaded.
        """
        if zenodo_record_id is None:
            z = Zenodo("7251657")
        elif zenodo_record_id == "latest":
            z = Zenodo("3601881")
        else:
            z = Zenodo(zenodo_record_id)

        z.load_data(os.path.dirname(__file__))
        self.data_loc = os.path.join(z.dir, "networks")
        self._set_reduction(reduction)
        self._set_network()

    def _set_network(self):
        path = os.path.join(self.data_loc, "elec_s")
        if self.reduction is None:
            self.network = pypsa.Network(path + ".nc")
        else:
            self.network = pypsa.Network(path + f"_{self.reduction}_ec.nc")

    def _set_reduction(self, reduction):
        """Validate and set reduction parameter

        :raises ValueError: if ``reduction`` is not available.
        """
        if reduction is None:
            self.reduction = None
        else:
            available = [
                s
                for f in os.listdir(self.data_loc)
                for s in f.split("_")
                if s.isdigit()
            ]
            if str(reduction) in available:
                self.reduction = reduction
            else:
                raise ValueError(f"Available reduced network: {' | '.join(available)}")
