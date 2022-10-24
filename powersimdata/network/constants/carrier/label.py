class USALabel:
    """Label for each resource in USA grid models."""

    def __init__(self):
        self.type2label = {
            "nuclear": "Nuclear",
            "geothermal": "Geothermal",
            "coal": "Coal",
            "dfo": "Diesel Fuel Oil",
            "hydro": "Hydro",
            "ng": "Natural Gas",
            "solar": "Solar",
            "wind": "Onshore Wind",
            "wind_offshore": "Offshore Wind",
            "biomass": "Biomass",
            "other": "Other",
            "storage": "Storage",
        }
        self.curtailable2label = {
            "solar": "Solar Curtailment",
            "wind": "Onshore Wind Curtailment",
            "wind_offshore": "Offshore Wind Curtailment",
        }
        self.label2type = {v: k for k, v in self.type2label.items()}
        self.label2curtailable = {v: k for k, v in self.curtailable2label.items()}


class EULabel:
    """Label for each resource in EU grid model."""

    def __init__(self):
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


def get_label(model):
    """Return label for generator types.

    :param str model: grid model
    """
    _lookup = {
        "usa_tamu": USALabel,
        "hifld": USALabel,
        "europe_tub": EULabel,
    }
    return _lookup[model]().__dict__
