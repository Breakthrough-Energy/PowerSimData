from powersimdata.network.helpers import check_model

storage = {
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


def get_storage(model):
    """Return storage constants.

    :param str model: grid model
    :return: (*dict*) -- storage information.
    """
    check_model(model)

    return storage
