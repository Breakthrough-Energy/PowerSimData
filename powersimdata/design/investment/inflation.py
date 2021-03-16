from powersimdata.design.investment.const import inflation_rate_pct


def calculate_inflation(start_year, end_year=None):
    """Calculate the overall inflation between two years.

    :param int start_year: Year to start calculating inflation from.
    :param int/None end_year: Year to calculate inflation to. Calculates using the
        rates from [start_year, end_year), since we calculate _to_ end_year, not
        _through_ end_year. If None, inflates to as recent as possible.
    :return: (*float*) -- Inflation factor.
    """
    if start_year not in inflation_rate_pct:
        raise ValueError(f"No inflation data for year {start_year}")
    if end_year is None:
        end_year = max(inflation_rate_pct.keys()) + 1
    if (end_year - 1) not in inflation_rate_pct:
        raise ValueError(f"No inflation data for year {(end_year - 1)}")
    factor = 1
    for i in range(start_year, end_year):
        factor *= 1 + (inflation_rate_pct[i] / 100)
    return factor
