from powersimdata.network.helpers import check_model


class Resource:
    """Generator type arrangement.

    :param str model: grid model.
    """

    def __init__(self, model):
        if model in ["usa_tamu", "hifld"]:
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
            self.all_resources = {
                r for v in self.group_all_resources.values() for r in v
            }
            self.pretty_name = {
                "biomass": "biomass",
                "coal": "coal",
                "dfo": "diesel fuel oil",
                "geothermal": "geothermal",
                "hydro": "reservoir & dam",
                "ng": "natural gas",
                "nuclear": "nuclear",
                "other": "other",
                "solar": "solar",
                "wind": "onshore wind",
                "wind_offshore": "offshore wind",
            }
            # If None, Pmin in Grid object is maintained or profile is tracked
            # If not None, Pmin in Grid will be replaced for thermal generators and
            # range of curtailment will be set for other.
            self.pmin_as_share_of_pmax = {
                "biomass": 0,
                "coal": None,
                "dfo": 0,
                "geothermal": 0.95,
                "hydro": 0.9,
                "ng": 0,
                "nuclear": 0.95,
                "other": 0,
                "solar": 0,
                "wind": 0,
                "wind_offshore": 0,
            }
        elif model == "europe_tub":
            self.profile_resources = {
                "hydro",
                "offwind-ac",
                "offwind-dc",
                "onwind",
                "phs",
                "ror",
                "solar",
            }
            self.group_profile_resources = {
                "hydro": {"hydro", "phs", "ror"},
                "solar": {"solar"},
                "wind": {"onwind", "offwind-ac", "offwind-dc"},
            }
            self.curtailable_resources = {
                "hydro",
                "phs",
                "ror",
                "solar",
                "offwind-ac",
                "offwind-dc",
                "onwind",
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
                "hydro",
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
                "hydro": {"hydro", "phs", "ror"},
                "ng": {"CCGT", "OCGT"},
                "nuclear": {"nuclear"},
                "oil": {"oil"},
                "solar": {"solar"},
                "wind": {"onwind", "offwind-ac", "offwind-dc"},
            }
            self.all_resources = {
                r for v in self.group_all_resources.values() for r in v
            }
            self.pretty_name = {
                "biomass": "biomass",
                "CCGT": "combined cycle gas",
                "coal": "coal",
                "geothermal": "geothermal",
                "hydro": "reservoir & dam",
                "lignite": "lignite",
                "nuclear": "nuclear",
                "OCGT": "open cycle gas",
                "oil": "oil",
                "offwind-ac": "offshore wind (AC)",
                "offwind-dc": "offshore wind (DC)",
                "onwind": "onshore wind",
                "phs": "pumped hydro storage",
                "ror": "run of river",
                "solar": "solar",
            }
            self.pmin_as_share_of_pmax = {
                "biomass": None,
                "CCGT": None,
                "coal": None,
                "geothermal": None,
                "hydro": 0.9,
                "lignite": None,
                "nuclear": None,
                "OCGT": None,
                "oil": None,
                "offwind-ac": 0,
                "offwind-dc": 0,
                "onwind": 0,
                "phs": 0.9,
                "ror": None,
                "solar": 0,
            }


class Color:
    """Color for each resource.

    :param str model: grid model.
    """

    def __init__(self, model):
        if model in ["usa_tamu", "hifld"]:
            self.type2color = {
                "wind": "xkcd:green",
                "solar": "xkcd:amber",
                "hydro": "xkcd:light blue",
                "ng": "xkcd:orchid",
                "nuclear": "xkcd:silver",
                "coal": "xkcd:light brown",
                "geothermal": "xkcd:hot pink",
                "dfo": "xkcd:royal blue",
                "biomass": "xkcd:dark green",
                "other": "xkcd:melon",
                "storage": "xkcd:orange",
                "wind_offshore": "xkcd:teal",
            }
            self.curtailable2color = {
                "solar": "xkcd:amber",
                "wind": "xkcd:green",
                "wind_offshore": "xkcd:teal",
            }
            self.curtailable2hatchcolor = {
                "solar": "xkcd:grey",
                "wind": "xkcd:grey",
                "wind_offshore": "xkcd:grey",
            }
        elif model == "europe_tub":
            self.type2color = {
                "onwind": "#235ebc",
                "offwind-ac": "#6895dd",
                "offwind-dc": "#74c6f2",
                "hydro": "#08ad97",
                "PHS": "#08ad97",
                "ror": "#4adbc8",
                "solar": "#f9d002",
                "biomass": "#0c6013",
                "geothermal": "#ba91b1",
                "OCGT": "#d35050",
                "CCGT": "#b20101",
                "nuclear": "#ff9000",
                "coal": "#707070",
                "lignite": "#9e5a01",
                "oil": "#262626",
                "H2": "#ea048a",
                "battery": "#b8ea04",
            }
            self.curtailable2color = {
                "solar": "#f9d002",
                "onwind": "#235ebc",
                "offwind-ac": "#6895dd",
                "offwind-dc": "74c6f2",
            }
            self.curtailable2hatchcolor = {
                "solar": "#808080",
                "onwind": "#808080",
                "offwind-ac": "#808080",
                "offwind-dc": "#808080",
            }


class Label:
    """Label for each resource.

    :param str model: grid model.
    """

    def __init__(self, model):
        if model in ["usa_tamu", "hifld"]:
            self.type2label = {
                "nuclear": "Nuclear",
                "geothermal": "thermal",
                "coal": "Coal",
                "dfo": "DFO",
                "hydro": "Hydro",
                "ng": "Natural Gas",
                "solar": "Solar",
                "wind": "Wind",
                "wind_offshore": "Wind Offshore",
                "biomass": "Biomass",
                "other": "Other",
                "storage": "Storage",
            }
            self.curtailable2label = {
                "solar": "Solar Curtailment",
                "wind": "Wind Curtailment",
                "wind_offshore": "Offshore Wind Curtailment",
            }
        elif model == "europe_tub":
            self.type2label = {
                "onwind": "Onshore Wind",
                "offwind-ac": "Offshore Wind (AC)",
                "offwind-dc": "Offshore Wind (DC)",
                "hydro": "Reservoir & Dam",
                "PHS": "Pumped Hydro Storage",
                "ror": "Run of River",
                "solar": "Solar",
                "biomass": "Biomass",
                "geothermal": "Geothermal",
                "OCGT": "Open-Cycle Gas",
                "CCGT": "Combined-Cycle Gas",
                "nuclear": "Nuclear",
                "coal": "Coal",
                "lignite": "Lignite",
                "oil": "Oil",
                "H2": "Hydrogen Storage",
                "battery": "Battery Storage",
            }
            self.curtailable2label = {
                "solar": "Solar Curtailment",
                "onwind": "Onshore Wind Curtailment",
                "offwind-ac": "Offshore Wind Curtailment (AC)",
                "offwind-dc": "Offshore Wind Curtailment (DC)",
            }
        self.label2type = {v: k for k, v in self.type2label.items()}
        self.label2curtailable = {v: k for k, v in self.curtailable2label.items()}


class Efficiency:
    """Efficiency for thermal generators.

    For US model:

    * Mwh electric to MWh thermal: `Danish Energy Agency, Technology Data - Generation
    of Energy and District Heating <https://ens.dk/sites/ens.dk/files/Analyser/technology_data_catalogue_for_el_and_dh.pdf>`_.

    :param str model: grid model.
    """

    def __init__(self, model):
        if model in ["usa_tamu", "hifld"]:
            self.efficiency = {
                "coal": 0.33,
                "dfo": 0.35,
                "ng": 0.41,  # referring to OCGT values from Danish Energy Agency
            }
        elif model == "europe_tub":
            self.efficiency = {
                "biomass": 0.416,
                "OCGT": 0.39,
                "CCGT": 0.55,
                "coal": 0.33,
                "lignite": 0.33,
                "oil": 0.35,
            }


class Emission:
    """Emission for each thermal technology.

    For US model:

    * MWh to kilogram of CO2: `IPCC Special Report on Renewable Energy Sources and
    Climate Change Mitigation (2011), Annex II: Methodology, Table A.II.4, 50th
    percentile <http://www.ipcc-wg3.de/report/IPCC_SRREN_Annex_II.pdf>`_

    * MBTu of fuel per hour to kilograms of CO2 per hour: `EPA Greenhouse Gases
    Equivalencies Calculator - Calculations and References <https://www.epa.gov/energy/greenhouse-gases-equivalencies-calculator-calculations-and-references>`_

    * MWh to kilograms of NOx: `EPA eGrid 2018, tab 'US18' (U.S. summary), columns AN
    to AP <https://www.epa.gov/egrid/egrid-questions-and-answers>`_

    * MWh to kilograms of SO2: `EPA eGrid 2018, tab 'US18' (U.S. summary), columns AV
    to AX <https://www.epa.gov/egrid/egrid-questions-and-answers>`_

    :param str model: grid model.
    """

    def __init__(self, model):
        if model in ["usa_tamu", "hifld"]:
            self.carbon_per_mwh = {
                "coal": 1001,
                "dfo": 840,
                "ng": 469,
            }
            # Equal to (Heat rate MMBTu/h) * (kg C/mmbtu) * (mass ratio CO2/C)
            self.carbon_per_mmbtu = {
                "coal": 26.05,
                "dfo": 20.31,
                "ng": 14.46,
            }
            self.nox_per_mwh = {
                "coal": 0.658,
                "dfo": 1.537,
                "ng": 0.179,
            }
            self.so2_per_mwh = {
                "coal": 0.965,
                "dfo": 2.189,
                "ng": 0.010,
            }
        elif model == "europe_tub":
            self.carbon_per_mwh = {
                "biomass": 721,
                "OCGT": 515,
                "CCGT": 365,
                "coal": 1021,
                "lignite": 1212,
                "oil": 762,
            }
            self.carbon_per_mbtu = {
                "biomass": 21.74,
                "OCGT": 14.57,
                "CCGT": 14.57,
                "coal": 24.41,
                "lignite": 28.97,
                "oil": 19.32,
            }
            self.nox_per_mwh = {
                "biomass": 0.216,
                "OCGT": 0.443,
                "CCGT": 0.131,
                "coal": 0.415,
                "lignite": 0.415,
                "oil": 9.689,
            }
            self.so2_per_mwh = {
                "biomass": 0.032,
                "OCGT": 0.004,
                "CCGT": 0,
                "coal": 0.057,
                "lignite": 0.115,
                "oil": 0.237,
            }


def get_plants(model):
    """Return plant constants.

    :param str model: grid model
    :return: (*dict*) -- plants information.
    """
    check_model(model)

    resources = Resource(model)
    color = Color(model)
    label = Label(model)
    efficiency = Efficiency(model)
    emission = Emission(model)

    return {
        **resources.__dict__,
        **color.__dict__,
        **label.__dict__,
        **efficiency.__dict__,
        **emission.__dict__,
    }
