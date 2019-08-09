def apply_change_table(self, grid):

    if bool(self.ct):
        for gridElement in self.ct:
            if gridElement in self._gen_types:
                grid = scale_location_type(self, grid, gridElement, scale_GenMWMax)
                grid = scale_generators_by_id(self, grid, gridElement)

            if gridElement in self._thermal_gen_types:
                grid = scale_location_type(self, grid, gridElement, scale_Thermal)
                grid = scale_thermal_genID_power_cost(self, grid, gridElement)


            if gridElement == 'branch':
                grid = scale_branches_by_location(self, grid)
                grid = scale_branches_by_id(self, grid)

            if gridElement == 'dcline' in list(self.ct.keys()):
                grid = scale_dc_line(self, grid)

    return grid

def scale_location_type(self, grid, gentype, grid_transform):
    if gentype in self._gen_types and list(self.ct.keys()):
        try:
            for key, value in self.ct[gentype]['zone_id'].items():
                plant_ids = get_plant_ids_by_type(grid, key, gentype)
                grid = grid_transform(self, grid, gentype, plant_ids, value)
        except KeyError:
            pass
    return grid

def get_plant_ids_by_type(grid, key, gentype):
    plant_ids = grid.plant.groupby(['zone_id', 'type']).get_group((key, gentype)).index.values.tolist()
    print('plant_ids: ', plant_ids)
    return plant_ids

def scale_GenMWMax(self, grid, gentype, plant_ids, value):
    if gentype in self._gen_types:
        grid.plant.loc[plant_ids, 'GenMWMax'] *= value
    return grid

def scale_Thermal(self, grid, gentype, plant_ids, value):
    if gentype in self._thermal_gen_types:
        print(grid.plant)
        grid.plant.loc[plant_ids, 'Pmax'] *= value
        grid.plant.loc[plant_ids, 'Pmin'] *= value
        grid.gencost.loc[plant_ids, 'c0'] *= value
        # if value == 0:
        #     continue
        grid.gencost.loc[plant_ids, 'c2'] /= value
        print(grid.plant)
    return grid

def scale_thermal_genID_power_cost(self, grid, gentype):
    if gentype in self._thermal_gen_types and list(self.ct.keys()):
        try:
            for plant_ids, scaling in self.ct[gentype]['plant_id'].items():
                scale_Thermal(grid, plant_ids, scaling)
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

def scale_generators_by_id(self, grid, gentype):
    if gentype in list(self.ct.keys()):
        try:
            for key, value in self.ct[gentype]['plant_id'].items():
                grid.plant.loc[key, 'GenMWMax'] *= value
        except KeyError:
            pass
    return grid

# def apply_to_plant_id(grid, ids, grid_transform):
#     try:
#         for key, value in self.ct[ids]['plant_id'].items():
#             print(key)
#             print(value)
#             grid_transform(grid,key,value)
#     except KeyError:
#         pass
#     return grid