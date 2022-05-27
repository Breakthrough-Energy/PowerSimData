from powersimdata.input.profile_input import ProfileInput


def get_profile_version(_fs, grid_model, kind, end_use, tech):
    _fs = _fs.makedirs(f"raw/{grid_model}/{kind}", recreate=True)
    base_name = f"{end_use}_{tech}_"
    matching = [f for f in _fs.listdir(".") if base_name in f]

    return [f.replace(base_name, "").replace(".csv", "") for f in matching]


class ElectrifiedDemand(ProfileInput):
    """Loads electrification profile data"""

    def __init__(self):
        super().__init__()
        self._file_extension = {}

    def get_profile(self, grid_model, kind, profile):
        """Get the specified profile

        :param str grid_model: the grid model
        :param str kind: the kind of electrification
        :param str profile: the filename
        :return: (*pandas.DataFrame*) -- profile data frame
        """
        path = f"raw/{grid_model}/{kind}/{profile}.csv"
        return self._get_data_internal(path)

    def get_profile_version(self, grid_model, kind, end_use, tech):
        """Returns available raw profile from blob storage or local disk.

        :param str grid_model: grid model.
        :param str kind: *'building'*, *'transportation'*
        :param str end_use: electrification use case
        :param str tech: the technology used for the given use case
        :return: (*list*) -- available profile version.
        """

        def _callback(fs):
            return get_profile_version(fs, grid_model, kind, end_use, tech)

        return self.data_access.get_profile_version(_callback)
