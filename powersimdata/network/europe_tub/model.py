import os
import shutil
from zipfile import ZipFile

from powersimdata.network.constants.region.geography import get_geography
from powersimdata.network.constants.region.zones import from_pypsa
from powersimdata.network.helpers import (
    check_and_format_interconnect,
    interconnect_to_name,
)
from powersimdata.network.model import ModelImmutables
from powersimdata.utility.helpers import _check_import

pypsa = _check_import("pypsa")
zenodo_get = _check_import("zenodo_get")


class TUB:
    """PyPSA Europe network.

    :param str/iterable interconnect: interconnect name(s).
    :param int reduction: reduction parameter (number of nodes in network). If None,
        the full network is loaded.
    :param bool overwrite: the existing dataset is deleted and a new dataset is
        downloaded from zenodo.
    """

    def __init__(self, interconnect, reduction=None, overwrite=False):
        """Constructor."""
        self.grid_model = "europe_tub"
        self.interconnect = check_and_format_interconnect(
            interconnect, model=self.grid_model
        )
        self.data_loc = os.path.join(os.path.dirname(__file__), "data")
        self.zenodo_record_id = "3601881"
        self.reduction = reduction

        if overwrite:
            self.remove_data()

        self.retrieve_data()

    def remove_data(self):
        """Remove data stored on disk"""
        print("Removing PyPSA-Eur dataset")
        shutil.rmtree(self.data_loc)

    def retrieve_data(self):
        """Fetch data"""
        zenodo_get.zenodo_get([self.zenodo_record_id, "-o", f"{self.data_loc}"])
        with ZipFile(os.path.join(self.data_loc, "networks.zip"), "r") as zip_network:
            zip_network.extractall(self.data_loc)

    def build(self):
        """Build network"""
        path = os.path.join(self.data_loc, "networks", "elec_s")
        if self.reduction is None:
            network = pypsa.Network(path + ".nc")
        elif os.path.exists(path + f"_{self.reduction}_ec.nc"):
            network = pypsa.Network(path + f"_{self.reduction}_ec.nc")
        else:
            raise ValueError(
                "Invalid Resolution. Choose among: None | 1024 | 512 | 256 | 128 | 37"
            )
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
