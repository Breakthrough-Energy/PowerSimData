from powersimdata.network.constants.carrier.color import get_color
from powersimdata.network.constants.carrier.efficiency import get_efficiency
from powersimdata.network.constants.carrier.emission import get_emission
from powersimdata.network.constants.carrier.label import get_label
from powersimdata.network.constants.carrier.resource import get_resource
from powersimdata.network.helpers import check_model


def get_plants(model):
    """Return plant constants.

    :param str model: grid model
    :return: (*dict*) -- plants information.
    """
    check_model(model)

    return {
        **get_color(model),
        **get_efficiency(model),
        **get_emission(model),
        **get_label(model),
        **get_resource(model),
    }
