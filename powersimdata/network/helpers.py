from powersimdata.network.constants.model import model2interconnect, model2region


def check_model(model):
    """Check that a grid model exists.

    :param str model: grid model name
    :raises TypeError: if ``model`` is not a str.
    :raises ValueError: if grid model does not exist.
    """
    if not isinstance(model, str):
        raise TypeError("model must be a str")
    if model not in model2region:
        raise ValueError(f"Invalid model. Choose among {' | '.join(model2region)}")


def check_and_format_interconnect(interconnect, model="hifld"):
    """Checks interconnect in a grid model.

    :param str/iterable interconnect: interconnect name(s).
    :param str model: the grid model.
    :return: (*set*) -- interconnect(s)
    :raises TypeError: if ``interconnect`` is not a str.
    :raises ValueError:
        if ``interconnect`` is not in the model.
        if combination of interconnect is incorrect.
    """
    if isinstance(interconnect, str):
        interconnect = [interconnect]
    try:
        interconnect = sorted(set(interconnect))
    except TypeError:
        raise TypeError("interconnect must be either str or an iterable of str")

    region = model2region[model]
    possible = model2interconnect[model]
    if len(set(interconnect) - ({region} | set(possible))) != 0:
        raise ValueError(
            f"Invalid interconnect(s). Choose from {' | '.join(set(possible) | {region})}"
        )
    if region in interconnect and len(interconnect) > 1:
        raise ValueError(f"{region} cannot be paired")
    if len(set(possible) - set(interconnect)) == 0:
        raise ValueError(f"Use {region} instead")

    return interconnect


def interconnect_to_name(interconnect, model="hifld"):
    """Return name of interconnect or collection of interconnects for a grid model.

    :param list interconnect: interconnect name(s).
    :param str model: the grid model.
    """
    return "_".join(sorted(check_and_format_interconnect(interconnect, model)))
