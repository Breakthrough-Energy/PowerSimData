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


def calculate_inflation(start_year, end_year):
    if start_year not in inflation_rate_pct:
        raise ValueError
    if (end_year - 1) not in inflation_rate_pct:
        raise ValueError
    factor = 1
    for i in range(start_year, end_year):
        factor *= 1 + (inflation_rate_pct[i] / 100)
    return factor
