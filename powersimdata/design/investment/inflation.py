inflation_rate_pct = {
    2010: 1.5,
    2011: 3.0,
    2012: 1.7,
    2013: 1.5,
    2014: 0.8,
    2015: 0.7,
    2016: 2.1,
    2017: 2.1,
    2018: 1.9,
    2019: 2.3,
    2020: 1.3,
}


def calculate_inflation(start_year, end_year=None):
    """Calculate the overall inflation between two years.

    :param int start_year: Year to start calculating inflation from.
    :param int/None end_year: Year to calculate inflation to. If None,
        inflates to as recent as possible.
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
