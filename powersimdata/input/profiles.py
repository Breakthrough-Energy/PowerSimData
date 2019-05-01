from postreise.process.transferdata import PullData
from postreise.process import const

import os
import pickle
import pandas as pd
from pathlib import Path
from postreise.process.transferdata import PullData


class InputData(object):
    """Load input data.

    """

    def __init__(self):
        """Constructor.

        """
        if not os.path.exists(const.LOCAL_DIR):
            os.makedirs(const.LOCAL_DIR)

    def get_data(self, scenario_id, field_name):
        """Returns data either from server or local directory.

        :param str scenario_id: scenario id.
        :param str field_name: *'demand'*, *'hydro'*, *'solar'* or *'wind'*.
        :return: (*pandas*) -- data frame of demand, hydro, solar or wind.
        :raises FileNotFoundError: if file not found on local machine.
        :raises ValueError: if second argument is not one of *'demand'*, \
            *'hydro'*, *'solar'*, *'wind'* or *'ct'*.
        """
        possible = ['demand', 'hydro', 'solar', 'wind', 'ct']
        if field_name not in possible:
            raise ValueError("Only %s data can be loaded" % "/".join(possible))

        print("# Loading %s" % field_name)
        file_name = scenario_id + '_' + field_name + '.pkl'
        try:
            p_out = pd.read_pickle(const.LOCAL_DIR + file_name)
            print("--> Done loading")
            return p_out
        except FileNotFoundError:
            print("%s not found in %s on local machine" %
                  (file_name, const.LOCAL_DIR))

        transfer = PullData()
        p_out = transfer.download(scenario_id, field_name, const.INPUT_DIR)

        print('Saving file in %s' % const.LOCAL_DIR)
        if field_name == 'ct':
            pickle.dump(p_out, open(const.LOCAL_DIR + file_name, "wb"))
        else:
            p_out.to_pickle(const.LOCAL_DIR + file_name)
        print("--> Done loading")

        return p_out
