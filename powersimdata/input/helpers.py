import os
import sys
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
    """Adds column(s) to data frame. Done inplace.

    :param pandas.DataFrame data_frame: input data frame
    :param dict column_dict: column to be added. Keys are column name and
        values a list of of values.
    """
    for key, value in column_dict.items():
        data_frame[key] = value


def block_print():
    """Suppresses print

    """
    sys.stdout = open(os.devnull, 'w')


def enable_print():
    """Suppresses print

    """
    sys.stdout = sys.__stdout__
