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

    :param str data_dir: define local folder location to read or save data.

    """

    def __init__(self, data_dir=None):

        self.data_dir = data_dir
        self.TD = PullData()
        # Check if data can be found locally
        if not data_dir:
            home_dir = str(Path.home())
            self.data_dir = os.path.join(home_dir, 'scenario_data', '')

            print('Use ', self.data_dir, ' to save/load local scenario data.')

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
        try:
            p_out = pd.read_pickle(
                self.data_dir + scenario_name + '_' + field_name + '.pkl'
            )
        except FileNotFoundError:
            print('Local file not found will',
                  'download data from server and save locally.')
            try:
                p_out = self.TD.download_data(scenario_name, field_name)
            except FileNotFoundError as e:
                raise FileNotFoundError(
                    'File found neither localy nor on server.'
                ) from e
            if not os.path.exists(self.data_dir):
                os.makedirs(self.data_dir)
            print('Saving file localy.')
            p_out.to_pickle(
                self.data_dir + scenario_name + '_' +field_name + '.pkl')
        
        return p_out
