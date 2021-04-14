_exports = ["defaults"]

defaults = {
    "duration": 4,
    "min_stor": 0.05,
    "max_stor": 0.95,
    "InEff": 0.9,
    "OutEff": 0.9,
    "energy_value": 20,
    "LossFactor": 0,
    "terminal_min": 0,
    "terminal_max": 1,
}


def __dir__():
    return sorted(_exports)
