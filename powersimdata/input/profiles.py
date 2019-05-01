from postreise.process.transferdata import PullData
from postreise.process import const

import os
import pickle
import pandas as pd
from pathlib import Path
from postreise.process.transferdata import PullData


class InputData(object):
    """Input Data class.
        This class enables you to download data from the server as well as \
        from a local folder. The :meth:`~get_data` function will first look \
        locally if it can find the data requested. If it can't find locally \
        it will download it from the server if it can find it there.

    """

    def __init__(self):
        """Constructor.

        """
        self.local_dir = const.LOCAL_DIR
        # Check if data can be found locally
        if not self.local_dir:
            home_dir = str(Path.home())
            self.local_dir = os.path.join(home_dir, 'scenario_data', '')

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
            p_out = pd.read_pickle(self.local_dir + file_name)
            print("--> Done loading")
            return p_out
        except FileNotFoundError:
            print("%s not found in %s on local machine. Looking on server." %
                  (file_name, self.local_dir))

        transfer = PullData()
        p_out = transfer.download(scenario_id, field_name)

        if not os.path.exists(self.local_dir):
            os.makedirs(self.local_dir)

        print('Saving file in %s' % self.local_dir)
        if field_name == 'ct':
            pickle.dump(p_out, open(self.local_dir + file_name, "wb"))
        else:
            p_out.to_pickle(self.local_dir + file_name)
        print("--> Done loading")
        return p_out
