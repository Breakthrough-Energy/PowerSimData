from postreise.process.transferdata import PullData
from postreise.process import const

import os
import pandas as pd
from pathlib import Path


class OutputData(object):
    """Output Data class.
        This class enables you to download data from the server as well as \
        from a local folder. The :meth:`~get_data` function will first look \
        locally if it can find the data requested. If it can't find locally \
        it will download it from the server if it can find it there.

    """

    def __init__(self):
        """Constructor

        """
        self.local_dir = const.LOCAL_DIR
        # Check if data can be found locally
        if not self.local_dir:
            home_dir = str(Path.home())
            self.local_dir = os.path.join(home_dir, 'scenario_data', '')

    def get_data(self, scenario_id, field_name):
        """Get data either from server or from local directory.

        :param str scenario_id: scenario id.
        :param str field_name: *'PG'* or *'PF'*.
        :return: (*pandas*) --  data frame of PG or PF.
        :raises FileNotFoundError: if file not found on local machine
        :raises ValueError: if second argument is not one of *'PG'* or *'PF'*.
        """
        possible = ['PG', 'PF']
        if field_name not in possible:
            raise ValueError("Only %s data can be loaded" % "/".join(possible))

        print("Loading %s" % field_name)
        file_name = scenario_id + '_' + field_name + '.pkl'
        try:
            p_out = pd.read_pickle(self.local_dir + file_name)
            print("-> Done loading")
        except FileNotFoundError:
            print("%s not found in %s on local machine" %
                  (file_name, self.local_dir))

            transfer = PullData()
            p_out = transfer.download(scenario_id, field_name)
            if p_out is None:
                return

            if not os.path.exists(self.local_dir):
                os.makedirs(self.local_dir)

            print('Saving file in %s' % self.local_dir)
            p_out.to_pickle(self.local_dir + file_name)
            print("-> Done loading")

        return p_out
