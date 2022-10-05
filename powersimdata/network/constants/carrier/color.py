class USAColor:
    """Color for each resource in USA grid models."""

    def __init__(self):
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


class EUColor:
    """Color for each resource in EU grid model."""

    def __init__(self):
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


def get_color(model):
    """Return color for generator types.

    :param str model: grid model
    """
    _lookup = {
        "usa_tamu": USAColor,
        "hifld": USAColor,
        "europe_tub": EUColor,
    }
    return _lookup[model]().__dict__
