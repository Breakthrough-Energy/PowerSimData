# call appropriate functions according to change table

def apply_change_table(self, ct, grid):

    if bool(ct):
        for gridElement, scale_info in ct.items():
            if 'zone_id' in scale_info.keys():
                if gridElement in self._gen_types:
                    grid = scale_location_by_gentype(ct, grid, gridElement, scale_GenMWMax)

                if gridElement in self._thermal_gen_types:
                    grid = scale_location_by_gentype(ct, grid, gridElement, scale_Thermal)

                if gridElement == 'branch':
                    grid = scale_location_by_gentype(ct, grid, gridElement, scale_Branch)

            if 'plant_id' in scale_info.keys():
                if gridElement in self._gen_types:
                    grid = scale_generators_by_id(ct, grid, gridElement, scale_GenMWMax)

                if gridElement in self._thermal_gen_types:
                    grid = scale_generators_by_id(ct, grid, gridElement, scale_Thermal)

            if 'branch_id' in scale_info.keys():
                if gridElement == 'branch':
                    grid = scale_branches_by_id(ct, grid, scale_Branch)

            if gridElement == 'dcline' in list(ct.keys()):
                grid = scale_dc_line(ct, grid)

    return grid

# scale generators by location

def scale_location_by_gentype(ct, grid, gentype, grid_transform):
    try:
        for zoneid, value in ct[gentype]['zone_id'].items():
            plant_ids = get_plant_ids_by_gentype(grid, zoneid, gentype)
            grid = grid_transform(grid, plant_ids, value)
    except KeyError:
        pass
    return grid

def get_plant_ids_by_gentype(grid, zoneid, gentype):
    plant_ids = grid.plant.groupby(['zone_id', 'type']).get_group((zoneid, gentype)).index.values.tolist()
    return plant_ids

# scale generators by id

def scale_generators_by_id(ct, grid, gentype, grid_transform):
    try:
        for plant_ids, scaling in ct[gentype]['plant_id'].items():
            grid_transform(grid, plant_ids, scaling)
    except KeyError:
        pass
    return grid

# scale non-thermal generators

def scale_GenMWMax(grid, plant_ids, value):
    grid.plant.loc[plant_ids, 'GenMWMax'] *= value
    return grid

# scale thermal generators

def scale_Thermal(grid, plant_ids, value):
    grid.plant.loc[plant_ids, 'Pmax'] *= value
    grid.plant.loc[plant_ids, 'Pmin'] *= value
    grid.gencost.loc[plant_ids, 'c0'] *= value
    if value != 0:
        grid.gencost.loc[plant_ids, 'c2'] /= value
    return grid

# scale branches

def scale_branches_by_location(ct, grid, grid_transform):
    try:
        for zoneid, value in ct['branch']['zone_id'].items():
            branch_ids = find_branches_within_zone(grid, zoneid)
            grid_transform(grid, branch_ids, value)
    except KeyError:
        pass
    return grid

def find_branches_within_zone(grid, zoneid):
    branch_ids = grid.branch.groupby(['from_zone_id', 'to_zone_id']).get_group((zoneid, zoneid)).index.values.tolist()
    return branch_ids

def scale_branches_by_id(ct, grid, grid_transform):
    try:
        for branchid, value in ct['branch']['branch_id'].items():
            grid_transform(grid, branchid, value)
    except KeyError:
        pass
    return grid

def scale_Branch(grid, branch_ids, value):
    grid.branch.loc[branch_ids, 'rateA'] *= value
    grid.branch.loc[branch_ids, 'x'] /= value

# scale dc lines

def scale_dc_line(ct, grid):
    for key, value in ct['dcline']['dcline_id'].items():
        if value == 0.0:
            grid.dcline.loc[key, 'status'] = 0
        else:
            grid.dcline.loc[key, 'Pmax'] *= value
    return grid