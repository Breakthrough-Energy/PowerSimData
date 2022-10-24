import ast

from powersimdata.network.helpers import powerset


class USA:
    """Geographical and timezone information for USA grid models"""

    def __init__(self):
        self.division = "state"
        self.abv2state = {
            "AK": "Alaska",
            "AL": "Alabama",
            "AR": "Arkansas",
            "AZ": "Arizona",
            "CA": "California",
            "CO": "Colorado",
            "CT": "Connecticut",
            "DE": "Delaware",
            "FL": "Florida",
            "GA": "Georgia",
            "HI": "Hawaii",
            "IA": "Iowa",
            "ID": "Idaho",
            "IL": "Illinois",
            "IN": "Indiana",
            "KS": "Kansas",
            "KY": "Kentucky",
            "LA": "Louisiana",
            "MA": "Massachusetts",
            "MD": "Maryland",
            "ME": "Maine",
            "MI": "Michigan",
            "MN": "Minnesota",
            "MO": "Missouri",
            "MS": "Mississippi",
            "MT": "Montana",
            "NC": "North Carolina",
            "ND": "North Dakota",
            "NE": "Nebraska",
            "NH": "New Hampshire",
            "NJ": "New Jersey",
            "NM": "New Mexico",
            "NV": "Nevada",
            "NY": "New York",
            "OH": "Ohio",
            "OK": "Oklahoma",
            "OR": "Oregon",
            "PA": "Pennsylvania",
            "RI": "Rhode Island",
            "SC": "South Carolina",
            "SD": "South Dakota",
            "TN": "Tennessee",
            "TX": "Texas",
            "UT": "Utah",
            "VA": "Virginia",
            "VT": "Vermont",
            "WA": "Washington",
            "WI": "Wisconsin",
            "WV": "West Virginia",
            "WY": "Wyoming",
        }
        self.state2abv = {n: a for a, n in self.abv2state.items()}
        self.interconnect2abv = {
            "Eastern": {
                "ME",
                "NH",
                "VT",
                "MA",
                "RI",
                "CT",
                "NY",
                "NJ",
                "PA",
                "DE",
                "MD",
                "VA",
                "NC",
                "SC",
                "GA",
                "FL",
                "AL",
                "MS",
                "TN",
                "KY",
                "WV",
                "OH",
                "MI",
                "IN",
                "IL",
                "WI",
                "MN",
                "IA",
                "MO",
                "AR",
                "LA",
                "OK",
                "KS",
                "NE",
                "SD",
                "ND",
            },
            "ERCOT": {"TX"},
            "Western": {
                "WA",
                "OR",
                "CA",
                "NV",
                "AZ",
                "UT",
                "NM",
                "CO",
                "WY",
                "ID",
                "MT",
            },
        }
        self.abv2interconnect = {
            a: i for i, abv in self.interconnect2abv.items() for a in abv
        }
        self.abv2timezone = {
            "ME": "ETC/GMT+5",
            "NH": "ETC/GMT+5",
            "VT": "ETC/GMT+5",
            "MA": "ETC/GMT+5",
            "RI": "ETC/GMT+5",
            "CT": "ETC/GMT+5",
            "NY": "ETC/GMT+5",
            "NJ": "ETC/GMT+5",
            "PA": "ETC/GMT+5",
            "DE": "ETC/GMT+5",
            "MD": "ETC/GMT+5",
            "VA": "ETC/GMT+5",
            "NC": "ETC/GMT+5",
            "SC": "ETC/GMT+5",
            "GA": "ETC/GMT+5",
            "FL": "ETC/GMT+5",
            "AL": "ETC/GMT+6",
            "MS": "ETC/GMT+6",
            "TN": "ETC/GMT+6",
            "KY": "ETC/GMT+5",
            "WV": "ETC/GMT+5",
            "OH": "ETC/GMT+5",
            "MI": "ETC/GMT+5",
            "IN": "ETC/GMT+5",
            "IL": "ETC/GMT+6",
            "WI": "ETC/GMT+6",
            "MN": "ETC/GMT+6",
            "IA": "ETC/GMT+6",
            "MO": "ETC/GMT+6",
            "AR": "ETC/GMT+6",
            "LA": "ETC/GMT+6",
            "TX": "ETC/GMT+6",
            "NM": "ETC/GMT+7",
            "OK": "ETC/GMT+6",
            "KS": "ETC/GMT+6",
            "NE": "ETC/GMT+6",
            "SD": "ETC/GMT+6",
            "ND": "ETC/GMT+6",
            "MT": "ETC/GMT+7",
            "WA": "ETC/GMT+8",
            "OR": "ETC/GMT+8",
            "CA": "ETC/GMT+8",
            "NV": "ETC/GMT+8",
            "AZ": "ETC/GMT+7",
            "UT": "ETC/GMT+7",
            "CO": "ETC/GMT+7",
            "WY": "ETC/GMT+7",
            "ID": "ETC/GMT+7",
        }
        self.interconnect2timezone = {
            "USA": "ETC/GMT+6",
            "Eastern": "ETC/GMT+5",
            "ERCOT": "ETC/GMT+6",
            "Western": "ETC/GMT+8",
            format(["ERCOT", "Western"]): "ETC/GMT+7",
            format(["ERCOT", "Eastern"]): "ETC/GMT+5",
            format(["Eastern", "Western"]): "ETC/GMT+6",
        }

        self.sub = {"USA": format(self.interconnect2abv)}
        self.name2interconnect = {
            format(c): set(c) for c in powerset(self.interconnect2abv, 1)
        }
        self.name2interconnect["USA"] = self.name2interconnect.pop(self.sub.get("USA"))
        self.name2component = self.name2interconnect.copy()
        self.name2component.update({"USA": set(self.name2interconnect) - {"USA"}})

    def substitute(self):
        """Replace ERCOT with Texas in all attributes.

        :return: (*dict*) -- updated attributes.
        """
        old = powerset(["ERCOT", "Eastern", "Western"], 1)
        old.reverse()
        new = powerset(["Texas", "Eastern", "Western"], 1)
        new.reverse()

        for o, n in {format(o): format(n) for o, n in zip(old, new)}.items():
            self.__dict__.update(ast.literal_eval(repr(self.__dict__).replace(o, n)))

        return self


class EU:
    """Geographical and timezone information for USA grid models"""

    def __init__(self):
        self.division = "country"
        self.abv2country = {
            "AL": "Albania",
            "AT": "Austria",
            "BA": "Bosnia And Herzegovina",
            "BE": "Belgium",
            "BG": "Bulgaria",
            "CH": "Switzerland",
            "CZ": "Czech Republic",
            "DE": "Germany",
            "DK": "Danemark",
            "EE": "Estonia",
            "ES": "Spain",
            "FI": "Finland",
            "FR": "France",
            "GB": "Great Britain",
            "GR": "Greece",
            "HR": "Croatia",
            "HU": "Hungary",
            "IE": "Ireland",
            "IT": "Italy",
            "LT": "Lithuania",
            "LU": "Luxembourg",
            "LV": "Latvia",
            "ME": "Montenegro",
            "MK": "Macedonia",
            "NL": "Netherlands",
            "NO": "Norway",
            "PL": "Poland",
            "PT": "Portugal",
            "RO": "Romania",
            "RS": "Serbia",
            "SE": "Sweden",
            "SI": "Slovenia",
            "SK": "Slovakia",
        }
        self.country2abv = {n: a for a, n in self.abv2country.items()}
        self.interconnect2abv = {
            "ContinentalEurope": {
                "AL",
                "AT",
                "BA",
                "BE",
                "BG",
                "CH",
                "CZ",
                "DE",
                "DK",
                "ES",
                "FR",
                "GR",
                "HR",
                "HU",
                "IT",
                "LU",
                "ME",
                "MK",
                "NL",
                "PL",
                "PT",
                "RO",
                "RS",
                "SI",
                "SK",
            },
            "Nordic": {"FI", "NO", "SE"},
            "GreatBritain": {"GB"},
            "Ireland": {"IE"},
            "Baltic": {"EE", "LT", "LV"},
        }
        self.abv2interconnect = {
            a: i for i, abv in self.interconnect2abv.items() for a in abv
        }
        self.abv2timezone = {
            "AL": "ETC/GMT-1",
            "AT": "ETC/GMT-1",
            "BA": "ETC/GMT-1",
            "BE": "ETC/GMT-1",
            "BG": "ETC/GMT-2",
            "CH": "ETC/GMT-1",
            "CZ": "ETC/GMT-1",
            "DE": "ETC/GMT-1",
            "DK": "ETC/GMT-1",
            "EE": "ETC/GMT-2",
            "ES": "ETC/GMT-1",
            "FI": "ETC/GMT-2",
            "FR": "ETC/GMT-1",
            "GB": "ETC/GMT",
            "GR": "ETC/GMT-2",
            "HR": "ETC/GMT-1",
            "HU": "ETC/GMT-1",
            "IE": "ETC/GMT",
            "IT": "ETC/GMT-1",
            "LT": "ETC/GMT-2",
            "LU": "ETC/GMT-1",
            "LV": "ETC/GMT-2",
            "ME": "ETC/GMT-1",
            "MK": "ETC/GMT-1",
            "NL": "ETC/GMT-1",
            "NO": "ETC/GMT-1",
            "PL": "ETC/GMT-1",
            "PT": "ETC/GMT",
            "RO": "ETC/GMT-2",
            "RS": "ETC/GMT-1",
            "SE": "ETC/GMT-1",
            "SI": "ETC/GMT-1",
            "SK": "ETC/GMT-1",
        }
        self.sub = {"Europe": format(self.interconnect2abv)}
        self.interconnect2timezone = {
            format(c): "ETC/GMT-1" for c in powerset(self.interconnect2abv, 1)
        }
        self.interconnect2timezone.update(
            {
                "GreatBritain": "ETC/GMT",
                "Ireland": "ETC/GMT",
                format(["GreatBritain", "Ireland"]): "ETC/GMT",
                "Baltic": "ETC/GMT-2",
                format(["Nordic", "Baltic"]): "ETC/GMT-2",
            }
        )
        self.interconnect2timezone["Europe"] = self.interconnect2timezone.pop(
            self.sub.get("Europe")
        )
        self.name2interconnect = {
            format(c): set(c) for c in powerset(self.interconnect2abv, 1)
        }
        self.name2interconnect["Europe"] = self.name2interconnect.pop(
            self.sub.get("Europe")
        )
        self.name2component = self.name2interconnect.copy()
        self.name2component.update({"Europe": set(self.name2interconnect) - {"Europe"}})


def format(name):
    """Format a list of words.

    :param list name: list of words
    """
    return "_".join(sorted([i.replace(" ", "") for i in name]))


def get_geography(model):
    """Return geographical and time zone information for a grid model.

    :param str model: grid model
    """

    _lookup = {
        "usa_tamu": USA().substitute(),
        "hifld": USA(),
        "europe_tub": EU(),
    }
    return _lookup[model].__dict__
