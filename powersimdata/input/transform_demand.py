from powersimdata.input.profile_input import ProfileInput


class TransformDemand:
    def __init__(self, grid, ct, kind):
        self.grid = grid
        self.ct = ct.ct
        self.info = self.ct[kind]
        self._profile_input = ProfileInput()
        self.scenario_info = {"base_demand": "vJan2021", "grid_model": grid.grid_model}
        self._set_scale_factors()

    def _get_base_profile(self, profile):
        print(f"temporarily ignoring {profile}")
        zone_id = sorted(self.grid.bus.zone_id.unique())
        demand = self._profile_input.get_data(self.scenario_info, "demand").loc[
            :, zone_id
        ]
        return demand

    def _get_profile_to_zone(self):
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
        info = self.info
        p2g = {}
        for end_use in info["grid"].keys():
            for tech in info["grid"][end_use].keys():
                profile = f"{end_use}_{tech}.csv"
                if profile not in p2g:
                    p2g[profile] = []
                scale_factor = info["grid"][end_use][tech]
                p2g[profile].append(scale_factor)
        return p2g

    def _set_scale_factors(self):
        self.p2z = self._get_profile_to_zone()
        self.p2g = self._get_profile_to_grid()

    def get_profile(self, profile):
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
        profiles = set(self.p2z.keys()) | set(self.p2g.keys())
        return sum(self.get_profile(p) for p in profiles)
