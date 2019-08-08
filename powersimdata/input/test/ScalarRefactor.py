import copy

def get_grid(self):
    """Returns modified grid.
    :return: (*powersimdata.input.grid.Grid*) -- instance of grid object.
    """
    grid = copy.deepcopy(self._original_grid)
    if bool(self.ct):
        grid = scale_generators_by_location(self, grid)
        grid = scale_generators_by_id(self, grid)

        if 'branch' in list(self.ct.keys()):
            grid = scale_branches_by_location(self, grid)
            grid = scale_branches_by_id(self, grid)

        if 'dcline' in list(self.ct.keys()):
            grid = scale_dc_line(self, grid)

    return grid
    
def scale_generators_by_location(self, grid):
    for r in self._gen_types:
        if r in list(self.ct.keys()):
            try:
                for key, value in self.ct[r]['zone_id'].items():
                    plant_id = grid.plant.groupby(
                        ['zone_id', 'type']).get_group(
                        (key, r)).index.values.tolist()
                    for i in plant_id:
                        grid.plant.loc[i, 'GenMWMax'] *= value
                        scale_thermal_gen(self, grid, r, i, value)
            except KeyError:
                pass
    return grid

def scale_generators_by_id(self, grid):
    for r in self._gen_types:
        if r in list(self.ct.keys()):
            try:
                for key, value in self.ct[r]['plant_id'].items():
                    grid.plant.loc[key, 'GenMWMax'] *= value
                    scale_thermal_gen(grid, ct, r, key, value)
            except KeyError:
                pass
    return grid

def scale_branches_by_location(self, grid):
    try:
        for key, value in self.ct['branch']['zone_id'].items():
            branch_id = grid.branch.groupby(
                ['from_zone_id', 'to_zone_id']).get_group(
                (key, key)).index.values.tolist()
            for i in branch_id:
                grid.branch.loc[i, 'rateA'] *= value
                grid.branch.loc[i, 'x'] /= value
    except KeyError:
        pass
    return grid


def scale_branches_by_id(self, grid):
    try:
        for key, value in self.ct['branch']['branch_id'].items():
            grid.branch.loc[key, 'rateA'] *= value
            grid.branch.loc[key, 'x'] /= value
    except KeyError:
        pass
    return grid

def scale_dc_line(self, grid):
    for key, value in self.ct['dcline']['dcline_id'].items():
        if value == 0.0:
            grid.dcline.loc[key, 'status'] = 0
        else:
            grid.dcline.loc[key, 'Pmax'] *= value
    return grid

def scale_thermal_gen(self, grid, r, key, value):
    if r in self._thermal_gen_types:
        try:
            grid.plant.loc[key, 'Pmax'] *= value
            grid.plant.loc[key, 'Pmin'] *= value
            grid.gencost.loc[key, 'c0'] *= value
#           if value == 0:
#                continue
            grid.gencost.loc[key, 'c2'] /= value
        except KeyError:
            pass