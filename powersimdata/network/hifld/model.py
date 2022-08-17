import os

from powersimdata.input.converter.csv_to_grid import FromCSV
from powersimdata.network.constants.storage import get_storage
from powersimdata.network.helpers import check_and_format_interconnect
from powersimdata.network.model import ModelImmutables


class HIFLD(FromCSV):
    """HIFLD network.

    :param str/iterable interconnect: interconnect name(s).
    """

    def __init__(self, interconnect):
        """Constructor."""
        super().__init__()

        self.grid_model = "hifld"
        self.interconnect = check_and_format_interconnect(
            interconnect, model=self.grid_model
        )
        self.model_immutables = ModelImmutables(
            self.grid_model, interconnect=interconnect
        )
        self._set_data_loc(os.path.dirname(__file__))

    def build(self):
        """Build network"""
        self._build(self.interconnect, self.grid_model)
        self.storage.update(get_storage(self.grid_model))
