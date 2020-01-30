import os
import pandas as pd


def csv_to_data_frame(data_loc, filename):
    """Reads CSV.

    :return: (*pandas.DataFrame*) -- created data frame.
    """
    print('Reading %s' % filename)
    data_frame = pd.read_csv(os.path.join(data_loc, filename),
                             index_col=0, float_precision='high')
    return data_frame


def add_column_to_data_frame(data_frame, column_dict):
    """Adds column(s) to data frame

    :param pandas.DataFrame data_frame: input data frame
    :param dict column_dict: column to be added. Keys are column name and
        values a list of of values.
    :return: (*pandas.DataFrame*) -- data frame with extra column(s)
    """
    for key, value in column_dict.items():
        data_frame[key] = value

    return data_frame
