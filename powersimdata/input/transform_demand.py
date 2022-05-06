from powersimdata.input.electrified_demand_input import ElectrifiedDemand


class TransformDemand:
    """Aggregate demand from electrified sources.

    :param powersimdata.input.grid.Grid grid: a grid object
    :param powersimdata.input.change_table.ChangeTable: a change table object
    :param str kind: the class of electrification, e.g. building, transportation
    """

    def __init__(self, grid, ct, kind):
        self.grid = grid
        self.ct = ct.ct
        self.info = self.ct[kind]
        self.kind = kind
        self._profile_data = ElectrifiedDemand()
        self._set_scale_factors()

    def _get_base_profile(self, profile):
        """Return the base profile from local or blob storage

        :return: (*pandas.DataFrame*) -- profile data frame, filtered to zones within
            the current grid
        """
        zone_id = sorted(self.grid.id2zone)
        model = self.grid.grid_model
        demand = self._profile_data.get_profile(model, self.kind, profile).loc[
            :, zone_id
        ]
        return demand

    def _get_profile_to_zone(self):
        """Maps profile name to scale factors for each zone

        :return: (*dict*) -- a dictionary mapping str to list of tuples of (zone_id,
            scale_factor)
        """
        info = self.info
        p2z = {}
        for zone_name in info["zone"].keys():
            zone_id = self.grid.zone2id[zone_name]
            for end_use in info["zone"][zone_name].keys():
                for tech in info["zone"][zone_name][end_use].keys():
                    profile = f"{end_use}_{tech}.csv"
                    if profile not in p2z:
                        p2z[profile] = []
                    scale_factor = info["zone"][zone_name][end_use][tech]
                    p2z[profile].append((zone_id, scale_factor))
        return p2z

    def _get_profile_to_grid(self):
        """Maps profile name to scale factor, which is applied to all zones in the grid

        :return: (*dict*) -- a dictionary mapping str to float
        """
        info = self.info
        p2g = {}
        for end_use in info["grid"].keys():
            for tech in info["grid"][end_use].keys():
                profile = f"{end_use}_{tech}.csv"
                scale_factor = info["grid"][end_use][tech]
                p2g[profile] = scale_factor
        return p2g

    def _set_scale_factors(self):
        """Populate mappings of profile names to scaling info"""
        self.p2z = self._get_profile_to_zone()
        self.p2g = self._get_profile_to_grid()

    def get_profile(self, profile):
        """Get transformed profile

        :param str profile: the profile name, without file extension
        :return: (*pandas.DataFrame*) -- the scaled profile, filtered to the zones
            within the current grid
        """
        p2z, p2g = self.p2z, self.p2g
        df = self._get_base_profile(profile)

        if profile in p2z:
            for zone_id, scale_factor in p2z[profile]:
                df.loc[:, zone_id] *= scale_factor
            exclude_zones = [_[0] for _ in p2z[profile]]
        else:
            exclude_zones = []

        if profile in p2g:
            scale_factor = p2g[profile]
            df.loc[:, ~df.columns.isin(exclude_zones)] *= scale_factor

        return df

    def value(self):
        """Return the combined electrified demand

        :return: (*pandas.DataFrame*) -- data frame with hourly index and zone columns,
            where the values are demand (in MWh)
        """
        profiles = set(self.p2z.keys()) | set(self.p2g.keys())
        return sum(self.get_profile(p) for p in profiles)
