class USAEmission:
    """Emission for each thermal technology in USA grid models.

    * MWh to kilogram of CO2: `IPCC Special Report on Renewable Energy Sources and
    Climate Change Mitigation (2011), Annex II: Methodology, Table A.II.4, 50th
    percentile <http://www.ipcc-wg3.de/report/IPCC_SRREN_Annex_II.pdf>`_

    * MBTu of fuel per hour to kilograms of CO2 per hour: `EPA Greenhouse Gases
    Equivalencies Calculator - Calculations and References <https://www.epa.gov/energy/greenhouse-gases-equivalencies-calculator-calculations-and-references>`_

    * MWh to kilograms of NOx: `EPA eGrid 2018, tab 'US18' (U.S. summary), columns AN
    to AP <https://www.epa.gov/egrid/egrid-questions-and-answers>`_

    * MWh to kilograms of SO2: `EPA eGrid 2018, tab 'US18' (U.S. summary), columns AV
    to AX <https://www.epa.gov/egrid/egrid-questions-and-answers>`_
    """

    def __init__(self):
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


class EUEmission:
    """Emission for each thermal technology in EU grid model."""

    def __init__(self):
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


def get_emission(model):
    """Return emissions by genertor type.

    :param str model: grid model
    """
    _lookup = {
        "usa_tamu": USAEmission,
        "hifld": USAEmission,
        "europe_tub": EUEmission,
    }
    return _lookup[model]().__dict__
