import os
import shutil
from zipfile import ZipFile

from powersimdata.network.constants.region.europe import (
    abv2country,
    abv2timezone,
    interconnect2abv,
)
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
            filter = list(  # noqa: F841
                interconnect2abv[
                    interconnect_to_name(self.interconnect, model=self.grid_model)
                ]
            )
            self.network = network[network.buses.query("country == @filter").index]
            self.zone2id = {l: zone2id[l] for l in self.network.buses.index}
            self.id2zone = {i: l for l, i in self.zone2id.items()}

        self.model_immutables = self._generate_model_immutables()

    def _generate_model_immutables(self):
        """Generate the model immutables"""
        mapping = ModelImmutables(self.grid_model, interconnect=self.interconnect)

        # loadzone
        mapping.zones["loadzone"] = set(self.zone2id)
        mapping.zones["id2loadzone"] = self.id2zone
        mapping.zones["loadzone2id"] = self.zone2id
        mapping.zones["loadzone2abv"] = self.network.buses["country"].to_dict()
        mapping.zones["loadzone2country"] = (
            self.network.buses["country"].map(abv2country).to_dict()
        )
        mapping.zones["loadzone2interconnect"] = {
            l: mapping.zones["abv2interconnect"][a]
            for l, a in mapping.zones["loadzone2abv"].items()
        }
        mapping.zones["id2timezone"] = {
            self.zone2id[l]: abv2timezone[a]
            for l, a in mapping.zones["loadzone2abv"].items()
        }
        mapping.zones["timezone2id"] = {
            t: i for i, t in mapping.zones["id2timezone"].items()
        }

        # country
        mapping.zones["country2loadzone"] = {
            abv2country[a]: set(l)
            for a, l in self.network.buses.groupby("country").groups.items()
        }
        mapping.zones["abv2loadzone"] = {
            a: set(l) for a, l in self.network.buses.groupby("country").groups.items()
        }
        mapping.zones["abv2id"] = {
            a: {self.zone2id[l] for l in l_in_country}
            for a, l_in_country in mapping.zones["abv2loadzone"].items()
        }
        mapping.zones["id2abv"] = {
            i: mapping.zones["loadzone2abv"][l] for i, l in self.id2zone.items()
        }

        # interconnect
        mapping.zones["interconnect2loadzone"] = {
            i: set().union(
                *(mapping.zones["abv2loadzone"][a] for a in a_in_interconnect)
            )
            for i, a_in_interconnect in mapping.zones["interconnect2abv"].items()
        }
        mapping.zones["interconnect2id"] = {
            i: set().union(*({self.zone2id[l]} for l in l_in_interconnect))
            for i, l_in_interconnect in mapping.zones["interconnect2loadzone"].items()
        }

        return mapping
