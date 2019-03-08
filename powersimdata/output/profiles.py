import os
import pandas as pd
from pathlib import Path
from postreise.process.transferdata import PullData


class OutputData(object):
    """Output Data class.
        This class enables you to download data from the server as well as \
        from a local folder. The :meth:`~get_data` function will first look \
        locally if it can find the data requested. If it can't find locally \
        it will download it from the server if it can find it there.

    :param str local_dir: define local folder location to read or save data.

    """

    def __init__(self, local_dir=None):

        self.local_dir = local_dir
        self.TD = PullData()
        # Check if data can be found locally
        if not local_dir:
            home_dir = str(Path.home())
            self.local_dir = os.path.join(home_dir, 'scenario_data', '')

    def get_data(self, scenario_name, field_name):
        """Get data either from server or from local directory.

        :param str scenario_name: name of scenario to get data from.
        :param str field_name: *'PG'* or *'PF'* data.
        :return: (*pandas*) --  data frame of PG or PF.
        :raises FileNotFoundError: file found neither locally nor on the \
            server.
        :raises NameError: If type not *'PG'* or *'PF'*.
        """
        if field_name not in ['PG', 'PF']:
            raise NameError('Can only get PG or PF data.')
        file_name = scenario_name + '_' + field_name + '.pkl'
        try:
            p_out = pd.read_pickle(self.local_dir + file_name)
        except FileNotFoundError:
            print('File not found in %s' % (file_name, self.local_dir))
            try:
                p_out = self.TD.download(scenario_name, field_name)
            except FileNotFoundError as e:
                raise FileNotFoundError('File not found on server.') from e
            if not os.path.exists(self.local_dir):
                os.makedirs(self.local_dir)
            print('Saving file in %s' % self.local_dir)
            p_out.to_pickle(self.local_dir + file_name)

        return p_out
