def check_interconnect(interconnect):
    """Sets interconnect.

    :param list interconnect: interconnect name(s).
    :raises TypeError: if parameter has wrong type.
    :raises Exception: if interconnect not found or unappropriate combination.
    """
    possible = ['Eastern', 'Texas', 'Western', 'USA']
    if not isinstance(interconnect, list):
        raise TypeError("List of string(s) is expected for interconnect")

    for i in interconnect:
        if i not in possible:
            raise Exception("Wrong interconnect. Choose from %s" %
                            " | ".join(possible))
    n = len(interconnect)
    if n > len(set(interconnect)):
        raise Exception("List of interconnects contains duplicate values")
    if 'USA' in interconnect and n > 1:
        raise Exception("USA interconnect cannot be paired")

def interconnect2name(interconnect):
    """Converts list of interconnect to string used for naming files.

    :param list interconnect: List of interconnect(s).
    :return: (*str*) -- name to use.
    """
    check_interconnect(interconnect)

    n = len(interconnect)
    if n == 1:
        return interconnect[0].lower()
    elif n == 2:
        if 'USA' in interconnect:
            return 'usa'
        else:
            if 'Western' in interconnect and 'Texas' in interconnect:
                return 'texaswestern'
            if 'Eastern' in interconnect and 'Texas' in interconnect:
                return 'texaseastern'
            if 'Eastern' in interconnect and 'Western' in interconnect:
                return 'easternwestern'
    else:
        return 'usa'
