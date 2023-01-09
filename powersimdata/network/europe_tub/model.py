import os

import pypsa

from powersimdata.input.converter.helpers import (
    add_interconnect_to_grid_data_frames,
    add_zone_to_grid_data_frames,
)
from powersimdata.input.converter.pypsa_to_grid import FromPyPSA
from powersimdata.input.converter.pypsa_to_profiles import (
    get_pypsa_demand_profile,
    get_pypsa_gen_profile,
)
from powersimdata.input.profile_input import ProfileInput
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

    def __init__(self, interconnect, grid_model, network=None, add_pypsa_cols=True):
        """Constructor."""
        super().__init__(network, add_pypsa_cols)
        self.grid_model = grid_model
        self.interconnect = check_and_format_interconnect(
            interconnect, model=self.grid_model
        )

    def build_eur(self):
        self.id2zone = {i: l for i, l in enumerate(self.network.loads.index)}
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
            self.zone2id = {l: self.zone2id[l] for l in self.network.loads.index}
            self.id2zone = {i: l for l, i in self.zone2id.items()}

        zone = (
            self.network.buses.loc[self.network.loads["bus"]]["country"]
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
        super().__init__(interconnect, "europe_tub")
        self.network = self.from_zenodo(zenodo_record_id, reduction)

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
        self.version = z.version
        self.reduction = reduction
        return self._get_network()

    def _get_network(self):
        """Create a PyPSA network with the given reduction

        :return: (*pypsa.Network*) -- a PyPSA network object
        """
        path = os.path.join(self.data_loc, "elec_s")
        self._check_reduction()
        if self.reduction is None:
            return pypsa.Network(path + ".nc")
        return pypsa.Network(path + f"_{self.reduction}_ec.nc")

    def _check_reduction(self):
        """Validate reduction parameter

        :raises ValueError: if ``reduction`` is not available.
        """
        if self.reduction is None:
            return
        available = [
            s for f in os.listdir(self.data_loc) for s in f.split("_") if s.isdigit()
        ]
        if str(self.reduction) not in available:
            raise ValueError(f"Available reduced network: {' | '.join(available)}")

    @property
    def _profile_version(self):
        """Get the profile version given the current record version from zenodo and the
        reduction.

        :return: (*str*) -- the version which is used to construct a file name
        """
        append = f"_{self.reduction}" if self.reduction is not None else ""
        return f"{self.version}" + append

    def _profile_exists(self, kind):
        """Check if a profile has been uploaded for the given version

        :return: (*bool*) -- True if the profile is available
        """
        _profile_input = ProfileInput()
        available = _profile_input.get_profile_version(self.grid_model, kind)
        return self._profile_version in available

    def _add_information(self):
        """Add zone and interconnect columns to data frames"""
        bus = self.bus
        bus2sub = self.bus2sub
        bus["zone_name"] = bus.index.map(bus2sub.sub_id)
        bus.zone_id = bus.zone_name.map(self.zone2id)
        add_zone_to_grid_data_frames(self)

        zone2ic = self.model_immutables.zones["loadzone2interconnect"]
        bus2sub.interconnect = bus2sub.sub_id.map(zone2ic)
        self.sub.interconnect = self.sub.index.map(zone2ic)
        add_interconnect_to_grid_data_frames(self)

    def _extract_profiles(self):
        """Extract and upload profiles if necessary"""
        profiles = {}
        if not self._profile_exists("demand"):
            demand = get_pypsa_demand_profile(self.network)
            demand.columns = demand.columns.map(self.zone2id)
            profiles[f"demand_{self._profile_version}"] = demand
        p2c = dict(self.model_immutables.plants["group_profile_resources"])
        p2c["hydro"] = {"ror", "hydro"}
        for k in p2c:
            if not self._profile_exists(k):
                profile = get_pypsa_gen_profile(self.network, {k: p2c[k]})
                profiles[f"{k}_{self._profile_version}"] = profile[k]
        if any(profiles):
            print(f"Uploading profiles: {list(profiles.keys())}")
        _profile_input = ProfileInput()
        for k, v in profiles.items():
            _profile_input.upload(self.grid_model, k, v)

    def _update_cols(self):
        """Update columns with default values"""
        pd_mask = self.bus.index.isin(self.zone2id)
        self.bus["Pd"] = [int(x) for x in pd_mask]
        self.plant.status = 1

    def build(self):
        """Construct the network used to build a grid object and extract/upload the
        profiles if necessary.
        """
        super().build()
        self._extract_profiles()
        self._add_information()
        self._update_cols()
