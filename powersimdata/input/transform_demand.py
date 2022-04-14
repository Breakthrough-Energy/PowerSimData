from powersimdata.input.profile_input import ProfileInput


class TransformDemand:
    def __init__(self, grid, ct, kind):
        self.grid = grid
        self.ct = ct.ct
        self.info = self.ct[kind]
        self._profile_input = ProfileInput()
        self.scenario_info = {"base_demand": "vJan2021", "grid_model": grid.grid_model}

    def _get_profile(self, profile):
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

    def _scale_profile(self, profile, p2z):
        df = self._get_profile(profile)
        for zone_id, scale_factor in p2z[profile]:
            df.loc[:, zone_id] *= scale_factor
        return df

    def value(self):
        p2z = self._get_profile_to_zone()
        return sum(self._scale_profile(profile, p2z) for profile in p2z)
