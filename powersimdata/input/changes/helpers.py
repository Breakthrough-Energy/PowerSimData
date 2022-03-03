def ordinal(n):
    """Translate a 0-based index into a 1-based ordinal, e.g. 0 -> 1st, 1 -> 2nd, etc.

    :param int n: the index to be translated.
    :return: (*str*) -- Ordinal.
    """
    ord_dict = {1: "st", 2: "nd", 3: "rd"}
    return str(n + 1) + ord_dict.get((n + 1) if (n + 1) < 20 else (n + 1) % 10, "th")
