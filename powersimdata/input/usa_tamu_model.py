import os
import seaborn as sns

from powersimdata.input.abstract_grid import AbstractGrid
from powersimdata.input.mpc_reader import MPCReader, get_storage


class TAMU(AbstractGrid):
    """TAMU network.

    """
    def __init__(self, interconnect):
        """Constructor.

        :param list interconnect: interconnect name(s).
        """
        super().__init__()
        self.data_loc = self.get_data_loc()

        if self._check_interconnect(interconnect):
            self.interconnect = interconnect
            self._build_network()
            self._add_extra_information()

    @staticmethod
    def get_data_loc():
        """Sets data location.

        :raises IOError: if directory does not exist.
        """
        top_dirname = os.path.dirname(__file__)
        data_loc = os.path.join(top_dirname, 'data', 'usa_tamu')
        if os.path.isdir(data_loc) is False:
            raise IOError('%s directory not found' % data_loc)
        else:
            return data_loc

    @staticmethod
    def _check_interconnect(interconnect):
        """Checks interconnect.

        :param list interconnect: interconnect name(s).
        :raises TypeError: if parameter has wrong type.
        :raises Exception: if interconnect not found or combination of
            interconnect is not appropriate.
        :return: (*bool*) -- if valid
        """
        possible = ['Eastern', 'Texas', 'Western', 'USA']
        if not isinstance(interconnect, list):
            raise TypeError("List of string(s) is expected for interconnect")

        for i in interconnect:
            if i not in possible:
                raise ValueError("Wrong interconnect. Choose from %s" %
                                 " | ".join(possible))
        n = len(interconnect)
        if n > len(set(interconnect)):
            raise ValueError("List of interconnects contains duplicate values")
        if 'USA' in interconnect and n > 1:
            raise ValueError("USA interconnect cannot be paired")

        return True

    @staticmethod
    def _get_storage():
        """Get storage.

        :return: (*dict*) -- storage.
        """
        storage = get_storage()
        storage['duration'] = 4
        storage['min_stor'] = 0.05
        storage['max_stor'] = 0.95
        storage['InEff'] = 0.9
        storage['OutEff'] = 0.9
        storage['energy_price'] = 20

        return storage

    def _build_network(self):
        """Build network.

        """
        reader = MPCReader(self.data_loc)
        self.zone2id = reader.zone2id
        self.id2zone = reader.id2zone
        self.sub = reader.sub
        self.bus2sub = reader.bus2sub
        self.bus = reader.bus
        self.plant = reader.plant
        self.gencost = reader.gencost
        self.branch = reader.branch
        self.dcline = reader.dcline
        self.storage = self._get_storage()

        if 'USA' not in self.interconnect:
            self._drop_interconnect()

    def _drop_interconnect(self):
        """Trim data frames to only keep information pertaining to the user
            defined interconnect(s)

        """
        expression = 'interconnect == @self.interconnect'
        self.sub.query(expression, inplace=True)
        self.bus2sub.query(expression, inplace=True)
        self.bus.query(expression, inplace=True)
        self.plant.query(expression, inplace=True)
        self.gencost.query(expression, inplace=True)
        self.branch.query(expression, inplace=True)
        self.sub.query(expression, inplace=True)
        self.dcline.query('from_interconnect == @self.interconnect',
                          inplace=True)
        self.dcline.query('to_interconnect == @self.interconnect',
                          inplace=True)
        self.id2zone = self.plant[
            ['zone_id', 'zone_name']].set_index('zone_id').zone_name.to_dict()
        self.zone2id = {value: key for key, value in self.id2zone.items()}

    def _add_extra_information(self):
        """Add information.

        """
        self.id2type = {
            0: 'wind',
            1: 'solar',
            2: 'hydro',
            3: 'ng',
            4: 'nuclear',
            5: 'coal',
            6: 'geothermal',
            7: 'dfo',
            8: 'biomass',
            9: 'other',
            10: 'storage'}

        self.type2id = {value: key for key, value in self.id2type.items()}

        self.type2color = {
            'wind': sns.xkcd_rgb["green"],
            'solar': sns.xkcd_rgb["amber"],
            'hydro': sns.xkcd_rgb["light blue"],
            'ng': sns.xkcd_rgb["orchid"],
            'nuclear': sns.xkcd_rgb["silver"],
            'coal': sns.xkcd_rgb["light brown"],
            'geothermal': sns.xkcd_rgb["hot pink"],
            'dfo': sns.xkcd_rgb["royal blue"],
            'biomass': sns.xkcd_rgb["dark green"],
            'other': sns.xkcd_rgb["melon"],
            'storage': sns.xkcd_rgb["orange"]}
