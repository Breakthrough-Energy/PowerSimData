def interconnect2name(interconnect):
    """Converts list of interconnect to string used for naming files.

    :param list interconnect: List of interconnect.
    :return: (*str*) -- name to use.
    """
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
