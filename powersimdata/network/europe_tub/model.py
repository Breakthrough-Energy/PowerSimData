import os

import pypsa

from powersimdata.input.converter.pypsa_to_grid import FromPyPSA
from powersimdata.network.constants.region.geography import get_geography
from powersimdata.network.constants.region.zones import from_pypsa
from powersimdata.network.helpers import (
    check_and_format_interconnect,
    interconnect_to_name,
)
from powersimdata.network.model import ModelImmutables
from powersimdata.network.zenodo import Zenodo


class PyPSABase(FromPyPSA):
    """Arbitrary PyPSA network.

    :param str/iterable interconnect: interconnect name(s).
    :param str grid_model: the grid model
    :param pypsa.Network network: a PyPSA network object
    :param bool add_pypsa_cols: PyPSA data frames with renamed columns appended to
        Grid object data frames.
    """

    def __init__(self, interconnect, grid_model, network, add_pypsa_cols=True):
        """Constructor."""
        super().__init__(network, add_pypsa_cols)
        self.grid_model = grid_model
        self.interconnect = check_and_format_interconnect(
            interconnect, model=self.grid_model
        )

    def build_eur(self):
        self.id2zone = {i: l for i, l in enumerate(self.network.buses.index)}
        self.zone2id = {l: i for i, l in self.id2zone.items()}

        if self.interconnect != ["Europe"]:
            geo = get_geography(self.grid_model)
            filter = list(  # noqa: F841
                geo["interconnect2abv"][
                    interconnect_to_name(self.interconnect, model=self.grid_model)
                ]
            )
            self.network = self.network[
                self.network.buses.query("country == @filter").index
            ]
            self.zone2id = {l: self.zone2id[l] for l in self.network.buses.index}
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

    def build(self):
        """Build network"""
        if self.grid_model == "europe_tub":
            self.build_eur()
        else:
            self.model_immutables = ModelImmutables(
                self.grid_model, interconnect=self.interconnect
            )

        super().build()


class TUB(PyPSABase):
    """PyPSA Europe network.

    :param str/iterable interconnect: interconnect name(s).
    :param str zenodo_record_id: the zenodo record id. If set to None, v0.6.1 will
        be used. If set to latest, the latest version will be used.
    :param int reduction: reduction parameter (number of nodes in network). If None,
        the full network is loaded.
    """

    def __init__(self, interconnect, zenodo_record_id=None, reduction=None):
        network = self.from_zenodo(zenodo_record_id, reduction)
        super().__init__(interconnect, "europe_tub", network)

    def from_zenodo(self, zenodo_record_id, reduction):
        """Create network from zenodo data

        :param str zenodo_record_id: the zenodo record id. If set to None, v0.6.1 will
            be used. If set to latest, the latest version will be used.
        :param int reduction: reduction parameter (number of nodes in network). If None,
            the full network is loaded.
        :return: (*pypsa.Network*) -- a PyPSA network object
        """
        if zenodo_record_id is None:
            z = Zenodo("7251657")
        elif zenodo_record_id == "latest":
            z = Zenodo("3601881")
        else:
            z = Zenodo(zenodo_record_id)

        z.load_data(os.path.dirname(__file__))
        self.data_loc = os.path.join(z.dir, "networks")
        return self._get_network(reduction)

    def _get_network(self, reduction):
        """Create a PyPSA network with the given reduction

        :param int reduction: reduction parameter (number of nodes in network). If None,
            the full network is loaded.
        :return: (*pypsa.Network*) -- a PyPSA network object
        """
        path = os.path.join(self.data_loc, "elec_s")
        self._check_reduction(reduction)
        if reduction is None:
            return pypsa.Network(path + ".nc")
        return pypsa.Network(path + f"_{reduction}_ec.nc")

    def _check_reduction(self, reduction):
        """Validate reduction parameter

        :param int reduction: reduction parameter (number of nodes in network).
        :raises ValueError: if ``reduction`` is not available.
        """
        if reduction is None:
            return
        available = [
            s for f in os.listdir(self.data_loc) for s in f.split("_") if s.isdigit()
        ]
        if str(reduction) not in available:
            raise ValueError(f"Available reduced network: {' | '.join(available)}")
