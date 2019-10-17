# call appropriate functions according to change table

def apply_change_table(self, grid):

    if bool(self.ct):
        for gridElement, scale_info in self.ct.items():
            #print(gridElement)
            if 'zone_id' in scale_info.keys():
                if gridElement in self._gen_types:
                    grid = scale_location_type(self, grid, gridElement, scale_GenMWMax)

                if gridElement in self._thermal_gen_types:
                    grid = scale_location_type(self, grid, gridElement, scale_Thermal)

                if gridElement == 'branch':
                    grid = scale_location_type(self, grid, gridElement, scale_Branch)

            if 'plant_id' in scale_info.keys():
                if gridElement in self._gen_types:
                    grid = scale_generators_by_id(self, grid, gridElement, scale_GenMWMax)

                if gridElement in self._thermal_gen_types:
                    grid = scale_generators_by_id(self, grid, gridElement, scale_Thermal)

            if 'branch_id' in scale_info.keys():
                if gridElement == 'branch':
                    grid = scale_branches_by_id(self, grid)

            if gridElement == 'dcline' in list(self.ct.keys()):
                grid = scale_dc_line(self, grid)

    return grid

# scale generators by location

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
    return plant_ids

# scale generators by id

def scale_generators_by_id(self, grid, gentype, grid_transform):
    if gentype in list(self.ct.keys()):
        try:
            for plant_ids, scaling in self.ct[gentype]['plant_id'].items():
                grid_transform(self, grid, gentype, plant_ids, scaling)
        except KeyError:
            pass
    return grid

# scale non-thermal generators

def scale_GenMWMax(self, grid, gentype, plant_ids, value):
    if gentype in self._gen_types:
        grid.plant.loc[plant_ids, 'GenMWMax'] *= value
    return grid

# scale thermal generators

def scale_Thermal(self, grid, gentype, plant_ids, value):
    if gentype in self._thermal_gen_types:
        grid.plant.loc[plant_ids, 'Pmax'] *= value
        grid.plant.loc[plant_ids, 'Pmin'] *= value
        grid.gencost.loc[plant_ids, 'c0'] *= value
        if value != 0:
            grid.gencost.loc[plant_ids, 'c2'] /= value
    return grid

# scale branches

def scale_branches_by_location(self, grid):
    try:
        for key, value in self.ct['branch']['zone_id'].items():
            branch_ids = find_branches_within_zone(grid, key)
            scale_Branch(self, grid, branch_ids, value)
    except KeyError:
        pass
    return grid

def find_branches_within_zone(grid, key):
    branch_ids = grid.branch.groupby(['from_zone_id', 'to_zone_id']).get_group(
                (key, key)).index.values.tolist()
    return branch_ids

def scale_branches_by_id(self, grid):
    try:
        for key, value in self.ct['branch']['branch_id'].items():
            scale_Branch(self, grid, key, value)
    except KeyError:
        pass
    return grid

def scale_Branch(self, grid, branch_ids, value):
    grid.branch.loc[branch_ids, 'rateA'] *= value
    grid.branch.loc[branch_ids, 'x'] /= value

# scale dc lines

def scale_dc_line(self, grid):
    for key, value in self.ct['dcline']['dcline_id'].items():
        if value == 0.0:
            grid.dcline.loc[key, 'status'] = 0
        else:
            grid.dcline.loc[key, 'Pmax'] *= value
    return grid