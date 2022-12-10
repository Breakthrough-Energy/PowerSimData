class USAResource:
    """Generator type arrangement for USA grid models."""

    def __init__(self):
        self.profile_resources = {"hydro", "solar", "wind", "wind_offshore"}
        self.group_profile_resources = {
            "hydro": {"hydro"},
            "solar": {"solar"},
            "wind": {"wind", "wind_offshore"},
        }
        self.curtailable_resources = {"hydro", "solar", "wind", "wind_offshore"}
        self.thermal_resources = {
            "biomass",
            "coal",
            "dfo",
            "geothermal",
            "ng",
            "nuclear",
        }
        self.renewable_resources = {"wind", "wind_offshore", "solar"}
        self.carbon_resources = {"biomass", "coal", "dfo", "ng"}
        self.clean_resources = {
            "geothermal",
            "hydro",
            "nuclear",
            "solar",
            "wind",
            "wind_offshore",
        }
        self.group_all_resources = {
            "biomass": {"biomass"},
            "coal": {"coal"},
            "geothermal": {"geothermal"},
            "hydro": {"hydro"},
            "ng": {"ng"},
            "nuclear": {"nuclear"},
            "other": {"other"},
            "oil": {"dfo"},
            "solar": {"solar"},
            "wind": {"wind", "wind_offshore"},
        }
        self.all_resources = {r for v in self.group_all_resources.values() for r in v}
        # If None, Pmin in Grid object is maintained or profile is tracked
        # If not None, Pmin in Grid will be replaced for thermal generators and
        # range of curtailment will be set for other.
        self.pmin_as_share_of_pmax = {
            "biomass": 0,
            "coal": None,
            "dfo": 0,
            "geothermal": 0.95,
            "hydro": 1,
            "ng": 0,
            "nuclear": 0.95,
            "other": 0,
            "solar": 0,
            "wind": 0,
            "wind_offshore": 0,
        }


class EUResource:
    """Generator type arrangement for EU grid model."""

    def __init__(self):
        self.profile_resources = {
            "inflow",
            "offwind-ac",
            "offwind-dc",
            "onwind",
            "ror",
            "solar",
        }
        self.group_profile_resources = {
            "hydro": {"inflow", "ror"},
            "solar": {"solar"},
            "wind": {"onwind", "offwind-ac", "offwind-dc"},
        }
        self.curtailable_resources = {
            "inflow",
            "offwind-ac",
            "offwind-dc",
            "onwind",
            "ror",
            "solar",
        }
        self.thermal_resources = {
            "biomass",
            "CCGT",
            "coal",
            "geothermal",
            "lignite",
            "nuclear",
            "oil",
            "OCGT",
        }
        self.renewable_resources = {"offwind-ac", "offwind-dc", "onwind", "solar"}
        self.carbon_resources = {
            "biomass",
            "CCGT",
            "coal",
            "lignite",
            "OCGT",
            "oil",
        }
        self.clean_resources = {
            "geothermal",
            "inflow",
            "nuclear",
            "offwind-ac",
            "offwind-dc",
            "onwind",
            "ror",
            "solar",
        }
        self.group_all_resources = {
            "biomass": {"biomass"},
            "coal": {"coal", "lignite"},
            "geothermal": {"geothermal"},
            "hydro": {"inflow", "ror"},
            "ng": {"CCGT", "OCGT"},
            "nuclear": {"nuclear"},
            "oil": {"oil"},
            "solar": {"solar"},
            "wind": {"onwind", "offwind-ac", "offwind-dc"},
        }
        self.all_resources = {r for v in self.group_all_resources.values() for r in v}
        self.pmin_as_share_of_pmax = {
            "biomass": None,
            "CCGT": None,
            "coal": None,
            "geothermal": None,
            "inflow": 0,
            "lignite": None,
            "nuclear": None,
            "OCGT": None,
            "oil": None,
            "offwind-ac": 0,
            "offwind-dc": 0,
            "onwind": 0,
            "ror": 0,
            "solar": 0,
        }


def get_resource(model):
    """Return arrrangement of generator types.

    :param str model: grid model
    """
    _lookup = {
        "usa_tamu": USAResource,
        "hifld": USAResource,
        "europe_tub": EUResource,
    }
    return _lookup[model]().__dict__
