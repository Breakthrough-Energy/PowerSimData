class USAEmission:
    r"""Emissions for each thermal technology in USA grid models.

    * MWh to kilogram of CO\ :sub:`2`: `IPCC Special Report on Renewable Energy Sources
      and Climate Change Mitigation (2011), Annex II: Methodology, Table A.II.4, 50th
      percentile <http://www.ipcc-wg3.de/report/IPCC_SRREN_Annex_II.pdf>`_
    * MBtu of fuel per hour to kilograms of CO\ :sub:`2` per hour: `EPA Greenhouse Gases
      Equivalencies Calculator - Calculations and References <https://www.epa.gov/energy/greenhouse-gases-equivalencies-calculator-calculations-and-references>`_
    * MWh to kilograms of NO\ :sub:`x`: `EPA eGrid 2018, tab 'US18' (U.S. summary),
      columns AN to AP <https://www.epa.gov/egrid/egrid-questions-and-answers>`_
    * MWh to kilograms of SO\ :sub:`2`: `EPA eGrid 2018, tab 'US18' (U.S. summary),
      columns AV to AX <https://www.epa.gov/egrid/egrid-questions-and-answers>`_
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
    r"""Emissions for each thermal technology in EU grid model.

    For carbon emission, numbers for both MWh electric to kilogram of CO\ :sub:`2` and
    MBtu of fuel per hour to kilograms of CO\ :sub:`2`, are calculated using Table 23
    located in p.52 of the `CO2 Emission Factors for Fossil Fuels - Update 2022
    <https://www.umweltbundesamt.de/sites/default/files/medien/479/publikationen/cc_29-2022_emission-factors-fossil-fuels.pdf>`_ report:

    * OCGT and CCGT from tCO\ :sub:`2`/TJ value in row Natural Gas, Germany 2015
    * coal from tCO\ :sub:`2`/TJ value in row Raw hard coal (power stations, industry),
      2015
    * lignite from tCO\ :sub:`2`/TJ value in row Public district heating stations,
      Germany, 2015
    * oil from tCO\ :sub:`2`/TJ value in row Diesel Fuel, Germany, 2015

    For NO\ :sub:`x` emission, see the Technology Data for Generation of Energy and District Heating page from the Danish Energy Agency located `here <https://ens.dk/en/our-services/projections-and-models/technology-data/technology-data-generation-electricity-and>`_. The 2015’s NO\ :sub:`x` [g/GJ] data can be found in the
    `Technology Data Catalogue for Electricity and district heating production -
    Updated June 2022 <https://ens.dk/sites/ens.dk/files/Analyser/technology_data_catalogue_for_el_and_dh.pdf>`_:

    * biomass: NO\ :sub:`x` average value from section 09a (Wood Chips extract. plant
      p.151) and section 09a (Wood Pellets extract. plant p.163)
    * OCGT: NO\ :sub:`x` value from section 52 (OCGT – Natural Gas p.383)
    * CCGT: NO\ :sub:`x` value from section 05 (Gas turb. CC, steam extract. p.73)
    * coal and lignite: NO\ :sub:`x` value from section 01 (Coal CHP p.37)
    * oil: NO\ :sub:`x` value from section 50 (Diesel engine farm p.366)

    Values can also be found in the in `Data sheet for Electricity and district heat
    production - Updated June 2022 <https://ens.dk/sites/ens.dk/files/Analyser/technology_data_for_el_and_dh.xlsx>`_

    For SO\ :sub:`2` emission, see both the Technology Data for Generation of Energy
    and District Heating `page <https://ens.dk/en/our-services/projections-and-models/technology-data/technology-data-generation-electricity-and>`_ and the `CO2 Emission
    Factors for Fossil Fuels - Update 2022 <https://www.umweltbundesamt.de/sites/default/files/medien/479/publikationen/cc_29-2022_emission-factors-fossil-fuels.pdf>`_ report. When available, the 2015 SO\ :sub:`2` [g/GJ] data can be found
    in the `Technology Data Catalogue for Electricity and district heating production - Updated June 2022 <https://ens.dk/sites/ens.dk/files/Analyser/technology_data_catalogue_for_el_and_dh.pdf>`_:

    * OCGT: SO\ :sub:`2` value from section 52 (OCGT – Natural Gas p.383)
    * CCGT: SO\ :sub:`2` value from section 52 (OCGT – Natural Gas p.383) and
      desulphuring percentage from section 05 (Gas turb. CC, steam extract. p.73)
    * oil: CO\ :sub:`2` value from section 50 (Diesel engine farm p.366)

    When only the desulphuring percentage is available, the 2015 CO\ :sub:`2` constants
    are calculated by taking the average mass percentage of sulphur and multiplying by
    the reported desulphuring percentage:

    * coal: weight per unit energy (MJ/kg) from Chapter 3, Figure 3 (p.13 of the Umwelt
      Bundesamt report), percent sulphur from Chapter 3, Table 1 (p.18 of the Umwelt
      Bundesamt report), and the desulphuring percentage from section 01 (Coal CHP p.37
      of the DEA report)
    * lignite: weight per unit energy (MJ/kg) from Chapter 4, Figure 12 (p.24 of the
      Umwelt Bundesamt report), percent sulphur from Chapter 4, Table 2 (p.26 of the
      Umwelt Bundesamt report), and the desulphuring percentage from section 01 (Coal
      CHP p.37 of the DEA report)
    * biomass: using peat values of weight per unit energy (MJ / kg) and percent
      sulphur from Chapter 4, Table 4 (p.30 of the Umwelt Bundesamt report), and the
      desulphuring percentage from section 09a (Wood Chips extract. plant p.151) and
      section 09a (Wood Pellets extract. plant p.163 of the DEA report)
    """

    def __init__(self):
        self.carbon_per_mwh = {
            "biomass": 721,
            "OCGT": 516,
            "CCGT": 366,
            "coal": 1021,
            "lignite": 1212,
            "oil": 762,
        }
        self.carbon_per_mbtu = {
            "biomass": 21.74,
            "OCGT": 14.59,
            "CCGT": 14.59,
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
            "CCGT": 0.003,
            "coal": 0.057,
            "lignite": 0.115,
            "oil": 0.237,
        }


def get_emission(model):
    """Return emissions by generator type.

    :param str model: grid model
    """
    _lookup = {
        "usa_tamu": USAEmission,
        "hifld": USAEmission,
        "europe_tub": EUEmission,
    }
    return _lookup[model]().__dict__
