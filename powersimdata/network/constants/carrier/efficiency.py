class USAEfficiency:
    """Efficiency (MWh electric to MWh thermal) for thermal generators in USA grid
    models come from:

    * The Technology Data for Generation of Energy and District Heating `page
      <https://ens.dk/en/our-services/projections-and-models/technology-data/technology-data-generation-electricity-and>`_ from the Danish Energy Agency for ng and
      diesel fuel oil.

      * ng: efficiency value from section 52 (OCGT – Natural Gas p.383)
      * oil: efficiency value from section 50 (Diesel engine farm p.366)

    * `Lazard’s Levelized Cost of Energy Analysis - Version 13.0 - Updated June
      2022 <https://www.lazard.com/media/451086/lazards-levelized-cost-of-energy-version-130-vf.pdf>`_ for coal and lignite:

      * coal and lignite: efficiency value calculated from Heat Rate value in Lazard
        report (p.19)
    """

    def __init__(self):
        self.efficiency = {
            "coal": 0.33,
            "dfo": 0.35,
            "ng": 0.39,  # referring to OCGT values from Danish Energy Agency
        }


class EUEfficiency:
    """Efficiency (MWh electric to MWh thermal) for thermal generators in EU grid
    model come from:

    * the Technology Data for Generation of Energy and District Heating `page
      <https://ens.dk/en/our-services/projections-and-models/technology-data/technology-data-generation-electricity-and>`_ from the Danish Energy Agency for biomass, gas
      turbines and oil. More specifically, the 2015’s electrical efficiency data (net,
      annual average) can be found in the `Technology Data Catalogue for Electricity
      and district heating production - Updated June 2022 <https://ens.dk/sites/ens.dk/files/Analyser/technology_data_catalogue_for_el_and_dh.pdf>`_. A `Data sheet for
      Electricity and district heat production - Updated June 2022 <https://ens.dk/sites/ens.dk/files/Analyser/technology_data_for_el_and_dh.xlsx>`_ is also
      available.

        * biomass: efficiency average of section 09a (Wood Chips extract. plant p.151)
          and section 09a (Wood Pellets extract. plant p.163)
        * OCGT: efficiency value from section 52 (OCGT – Natural Gas p.383)
        * CCGT: efficiency value from section 05 (Gas turb. CC, steam extract. p.72)
        * oil: efficiency value from section 50 (Diesel engine farm p.366)

    * The `Lazard’s Levelized Cost of Energy Analysis - Version 13.0 - Updated June
      2022 <https://www.lazard.com/media/451086/lazards-levelized-cost-of-energy-version-130-vf.pdf>`_ for coal and lignite:

      * coal and lignite: efficiency value calculated from Heat Rate value in Lazard
        report (p.19)
    """

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
