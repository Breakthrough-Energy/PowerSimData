from postreise.process import const
from postreise.process.transferdata import download
from powersimdata.input.profiles import _read_data
from powersimdata.scenario.helpers import interconnect2name

def _find_branches_connected_to_bus(branch, bus_idx):
    """Find all branches connected to a given bus.

    :param pandas.DataFrame branch: branch DataFrame from Grid object.
    :param int bus_idx: index of bus to find neighbors of.
    :return: (*set*) -- set of bus indexes (integers).
    """
    branches_from = branch.index[branch['from_bus_id'] == bus_idx].tolist()
    branches_to = branch.index[branch['to_bus_id'] == bus_idx].tolist()

    branches_connected = set(branches_from) | set(branches_to)

    return branches_connected


def _find_first_degree_branches(branch, branch_idx):
    """Find all branches connected to a given branch.

    :param pandas.DataFrame branch: branch DataFrame from Grid object.
    :param int branch_idx: index of branches to find neighbors of.
    :return: (*set*) -- set of branch indexes (integers).
    """
    from_bus = branch.loc[branch_idx,'from_bus_id']
    to_bus = branch.loc[branch_idx,'to_bus_id']
    endpoints = (from_bus, to_bus)
    to_endpoints = branch.index[branch['to_bus_id'].isin(endpoints)]
    from_endpoints = branch.index[branch['from_bus_id'].isin(endpoints)]
    first_degree_branch_idxs = set(to_endpoints) | set(from_endpoints)

    return first_degree_branch_idxs


def _find_stub_degree(branch, bus_id):
    """Find degree of stubbiness, and stub branches.

    :param pandas.DataFrame branch: branch DataFrame from Grid object.
    :param int bus_idx: index of bus to find subbiness of.
    :return: (*tuple*) -- tuple containing:
        stub_degree (*int*) -- How stubby (non-negative integer).
        connected_branches (*set*) -- set of branch indexes (integers).
    """
    connected_branch_idxs = _find_branches_connected_to_bus(branch, bus_id)
    if len(connected_branch_idxs) == 1:
        second_degree_branch_idxs = _find_first_degree_branches(
            branch, tuple(connected_branch_idxs)[0])
        if len(second_degree_branch_idxs) == 2:
            #We could keep going recursively, but this is the max in Western
            return 2, second_degree_branch_idxs
        else:
            return 1, connected_branch_idxs
    else:
        return 0, set()


def _find_capacity_at_bus(plant, bus_id, gentypes):
    """Find total capacity of plants with the given type(s) at the given bus.

    :param pandas.DataFrame branch: branch DataFrame from Grid object.
    :param int bus_idx: index of bus to find generators at.
    :param [list/tuple/set/str] gentypes: list/tuple/set of strs, or one str,
        containing the type of generators to sum capacity for.
    :return: (*float*) -- total capacity at bus.
    """

    if isinstance(gentypes, str):
        gentypes = (gentypes,)
    gentype_plants = plant[plant['type'].isin(gentypes)]
    at_bus = gentype_plants['bus_id'] == bus_id
    gentype_plants_at_bus = gentype_plants[at_bus]
    gentype_capacity = gentype_plants_at_bus['GenMWMax'].sum()

    return gentype_capacity


def scale_renewable_stubs(grid, ct, fuzz=1, inplace=True, verbose=True):
    """Identify renewable gens behind 'stub' branches, scale up branch capacity
        (via change_table entries) to match generator capacity.

    :param powersimdata.input.grid.Grid grid: grid instance.
    :param dict ct: dict from ChangeTable object.
    :param float/int fuzz: adds just a little extra capacity to avoid binding.
    :param bool inplace: if True, modify ct inplace and return None. If False,
        copy ct and return modified copy.
    :param bool verbose: if True, print when zone/type not in change table.
    :return: (*None*/*dict*) -- if inplace == True, return modified ct dict.
    """

    if not inplace:
        ct = ct.copy()
    ref_plant = grid.plant
    ref_branch = grid.branch
    ref_bus = grid.bus
    if 'branch' not in ct:
        ct['branch'] = {}
    if 'branch_id' not in ct['branch']:
        ct['branch']['branch_id'] = {}
    branch_id_ct = ct['branch']['branch_id']
    
    ren_types = ('solar', 'wind')
    for r in ren_types:
        ren_plants = ref_plant[ref_plant['type'] == r]
        for p in ren_plants.index:
            bus_id = ref_plant.loc[p,'bus_id']
            stub_degree, stub_branches = _find_stub_degree(ref_branch, bus_id)
            if stub_degree > 0:
                ren_capacity = _find_capacity_at_bus(ref_plant, bus_id, r)
                assert ren_capacity > 0
                zone_id = ref_bus.loc[bus_id, 'zone_id']
                try:
                    gen_scale_factor = ct[r]['zone_id'][zone_id]
                except KeyError:
                    if verbose:
                        print(f'no entry for zone {zone_id} in ct: {r}')
                    gen_scale_factor = 1
                for b in stub_branches:
                    if ref_branch.loc[b,'rateA'] == 0:
                        continue
                    old_branch_cap = ref_branch.loc[b,'rateA']
                    if old_branch_cap < ren_capacity * gen_scale_factor:
                        new_branch_cap = ren_capacity * gen_scale_factor + fuzz
                        branch_id_ct[b] = new_branch_cap / old_branch_cap

    if not inplace:
        return ct
