class USAEfficiency:
    """Efficiency for thermal generators in USA grid models.

    * Mwh electric to MWh thermal: `Danish Energy Agency, Technology Data - Generation
    of Energy and District Heating <https://ens.dk/sites/ens.dk/files/Analyser/technology_data_catalogue_for_el_and_dh.pdf>`_.
    """

    def __init__(self):
        self.efficiency = {
            "coal": 0.33,
            "dfo": 0.35,
            "ng": 0.41,  # referring to OCGT values from Danish Energy Agency
        }


class EUEfficiency:
    """Efficiency for thermal generators in EU grid model."""

    def __init__(self):
        self.efficiency = {
            "biomass": 0.416,
            "OCGT": 0.39,
            "CCGT": 0.55,
            "coal": 0.33,
            "lignite": 0.33,
            "oil": 0.35,
        }


def get_efficiency(model):
    """Return arrrangement of generator types.

    :param str model: grid model
    """
    _lookup = {
        "usa_tamu": USAEfficiency,
        "hifld": USAEfficiency,
        "europe_tub": EUEfficiency,
    }
    return _lookup[model]().__dict__
