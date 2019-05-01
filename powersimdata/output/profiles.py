from postreise.process.transferdata import PullData
from postreise.process import const

import os
import pandas as pd
from pathlib import Path


class OutputData(object):
    """Load output data.

    """

    def __init__(self):
        """Constructor

        """
        if not os.path.exists(const.LOCAL_DIR):
            os.makedirs(const.LOCAL_DIR)

    def get_data(self, scenario_id, field_name):
        """Returns data either from server or from local directory.

        :param str scenario_id: scenario id.
        :param str field_name: *'PG'* or *'PF'*.
        :return: (*pandas*) --  data frame of PG or PF.
        :raises FileNotFoundError: if file not found on local machine
        :raises ValueError: if second argument is not one of *'PG'* or *'PF'*.
        """
        possible = ['PG', 'PF']
        if field_name not in possible:
            raise ValueError("Only %s data can be loaded" % "/".join(possible))

        print("# Loading %s" % field_name)
        file_name = scenario_id + '_' + field_name + '.pkl'
        try:
            p_out = pd.read_pickle(const.LOCAL_DIR + file_name)
            print("--> Done loading")
            return p_out
        except FileNotFoundError:
            print("%s not found in %s on local machine. Looking on server." %
                  (file_name, const.LOCAL_DIR))

        transfer = PullData()
        p_out = transfer.download(scenario_id, field_name, const.OUTPUT_DIR)

        print('Saving file in %s' % const.LOCAL_DIR)
        p_out.to_pickle(const.LOCAL_DIR + file_name)
        print("--> Done loading")

        return p_out
