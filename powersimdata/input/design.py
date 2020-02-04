import numpy as np
import pandas as pd

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


def scale_renewable_stubs(change_table, fuzz=1, inplace=True, verbose=True):
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

    if inplace:
        ct = change_table.ct
    else:
        ct = change_table.ct.copy()
    ref_plant = change_table.grid.plant
    ref_branch = change_table.grid.branch
    ref_bus = change_table.grid.bus
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


def scale_congested_mesh_branches(change_table, ref_scenario, upgrade_n=100,
                                  quantile=0.95, increment=1):
    """Use a reference scenario as a baseline for branch scaling, and further
    increment branch scaling based on observed congestion duals.
    
    :param powersimdata.input.change_table.ChangeTable change_table: the
        change table instance we are operating on.
    :param powersimdata.scenario.scenario.Scenario ref_scenario: the reference
        scenario to be used in bootstrapping the branch scaling factors.
    :param int upgrade_n: the number of branches to upgrade.
    :param float quantile: the quantile to use to judge branch congestion.
    :param [float/int] increment: branch increment, relative to original
        capacity.
    :return: (*None*) -- the change_table is modified in-place.
    """
    # To do: better type checking of inputs.
    # We need a Scenario object that's in Analyze state to get congu/congl,
    # but we can't import Scenario to check against, because circular imports.
    branches_to_upgrade = _identify_mesh_branch_upgrades(
        ref_scenario, upgrade_n=upgrade_n, quantile=quantile)
    _increment_branch_scaling(
        change_table, branches_to_upgrade, ref_scenario, value=increment)


def _identify_mesh_branch_upgrades(ref_scenario, upgrade_n=100, quantile=0.95):
    """Identify the N most congested branches in a previous scenario, based on
    the quantile value of congestion duals. A quantile value of 0.95 obtains
    the branches with highest dual in top 5% of hours.
    
    :param powersimdata.scenario.scenario.Scenario ref_scenario: the reference
        scenario to be used to determine the most congested branches.
    :param int upgrade_n: the number of branches to upgrade.
    :param float quantile: the quantile to use to judge branch congestion.
    :return: (*Set*) -- A set of ints representing branch indices.
    """
    
    # How big does a dual value have to be to be 'real' and not barrier cruft?
    cong_significance_cutoff = 1e-6
    
    # Get raw congestion dual values
    ref_congu = ref_scenario.state.get_congu()
    ref_congl = ref_scenario.state.get_congl()
    ref_cong_abs = pd.DataFrame(
        np.maximum(ref_congu.to_numpy(), ref_congl.to_numpy()),
        index=ref_congu.index,
        columns=ref_congu.columns)
    # Free up some memory, since we don't need two directional arrays anymore
    ref_congu = ''
    ref_congl = ''
    
    # Parse 2-D array to vector of quantile values, filter out non-significant
    quantile_cong_abs = ref_cong_abs.quantile(quantile).sort_values()
    significance_bitmask = (quantile_cong_abs > cong_significance_cutoff)
    quantile_cong_abs = quantile_cong_abs.where(significance_bitmask).dropna()
    
    # Ensure that we have enough congested branches to upgrade
    num_congested = len(quantile_cong_abs)
    if num_congested < upgrade_n:
        err_msg = 'not enough congested branches: '
        err_msg += f'{upgrade_n} desired, but only {num_congested} congested.'
        raise ValueError(err_msg)
    
    quantile_branches = set(quantile_cong_abs.tail(upgrade_n).index)
    return quantile_branches


def _increment_branch_scaling(change_table, branch_ids, ref_scenario, value=1):
    """Modify the ct dict of a ChangeTable object based on branch scaling from
    both a reference scenario and a set of branches to increment by a value.
    
    :param powersimdata.input.change_table.ChangeTable change_table: the
        change table instance we are operating on.
    :param [list/set/tuple] branch_ids: an iterable of branch indices.
    :param powersimdata.scenario.scenario.Scenario ref_scenario: the reference
        scenario to copy branch scaling from.
    :param [int/float] value: branch increment, relative to original capacity.
    :return: (*None*) -- the change_table is modified in-place.
    """
    # Ensure that ct has proper keys
    ct = change_table.ct
    if 'branch' not in ct:
        ct['branch'] = {}
    if 'branch_id' not in ct['branch']:
        ct['branch']['branch_id'] = {}
    branch_scaling = ct['branch']['branch_id']
    
    # Get previous scenario's branch scaling
    ref_ct = ref_scenario.state.get_ct()
    ref_branch_scaling = ref_ct['branch']['branch_id'].copy()
    
    # Merge branch scaling dicts together: this ct + ref ct
    for branch in ref_branch_scaling:
        if branch in branch_scaling:
            new_scale = max(branch_scaling[branch], ref_branch_scaling[branch])
            branch_scaling[branch] = new_scale
        else:
            branch_scaling[branch] = ref_branch_scaling[branch]
    
    # Merge branch scaling dicts together: this ct + new increment
    for branch in branch_ids:
        if branch in branch_scaling:
            branch_scaling[branch] += value
        else:
            branch_scaling[branch] = 1 + value
