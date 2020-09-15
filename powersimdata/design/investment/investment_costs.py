import copy as cp
import os
import pandas as pd
import numpy as np

from shapely.geometry import *
import geopandas as gpd
#import osmnx as ox

from powersimdata.scenario.scenario import Scenario
from powersimdata.utility.distance import haversine
from powersimdata.input.grid import Grid

def sjoin_nearest(left_df, right_df, op='intersects', search_dist=0.06, report_dist=False,
                  lsuffix='left', rsuffix='right'):
    """
    Perform a spatial join between two input layers.
    If a geometry in left_df falls outside (all) geometries in right_df, the data from nearest Polygon will be used as a result.
    To make queries faster, "search_dist" -parameter (specified in map units) can be used to limit the search area for geometries around source points.
    If report_dist == True, the distance for closest geometry will be reported in a column called `dist`. If geometries intersect, the distance will be 0.

    """

    # Explode possible MultiGeometries
    right_df = right_df.explode()
    right_df = right_df.reset_index(drop=True)

    if 'index_left' in left_df.columns:
        left_df = left_df.drop('index_left', axis=1)

    if 'index_right' in left_df.columns:
        left_df = left_df.drop('index_right', axis=1)

    if report_dist:
        if 'dist' in left_df.columns:
            raise ValueError("'dist' column exists in the left DataFrame. Remove it, or set 'report_dist' to False.")

    # Get geometries that intersect or do not intersect polygons
    mask = left_df.intersects(right_df.unary_union)
    geoms_intersecting_polygons = left_df.loc[mask]
    geoms_outside_polygons = left_df.loc[~mask]

    # Make spatial join between points that fall inside the Polygons
    if geoms_intersecting_polygons.shape[0] > 0:
        pip_join = gpd.sjoin(left_df=geoms_intersecting_polygons, right_df=right_df, op=op)

        if report_dist:
            pip_join['dist'] = 0

    else:
        pip_join = gpd.GeoDataFrame()

    # Get nearest geometries
    closest_geometries = gpd.GeoDataFrame()

    # A tiny snap distance buffer is needed in some cases
    snap_dist = 0.00000005

    # Closest points from source-points to polygons
    for idx, geom in geoms_outside_polygons.iterrows():
        # Get geometries within search distance
        candidates = right_df.loc[right_df.intersects(geom[left_df.geometry.name].buffer(search_dist))]

        if len(candidates) == 0:
            continue
        unary = candidates.unary_union

        if unary.geom_type == 'Polygon':

            # Get exterior of the Polygon
            exterior = unary.exterior

            # Find a point from Polygons that is closest to the source point
            closest_geom = exterior.interpolate(exterior.project(geom[left_df.geometry.name]))

            if report_dist:
                distance = closest_geom.distance(geom[left_df.geometry.name])

            # Select the Polygon
            closest_poly = right_df.loc[right_df.intersects(closest_geom.buffer(snap_dist))]

        elif unary.geom_type == 'MultiPolygon':
            # Keep track of distance for closest polygon
            distance = 9999999999
            closest_geom = None

            for idx, poly in enumerate(unary):
                # Get exterior of the Polygon
                exterior = poly.exterior

                # Find a point from Polygons that is closest to the source point
                closest_candidate = exterior.interpolate(exterior.project(geom[left_df.geometry.name]))

                # Calculate distance between origin point and the closest point in Polygon
                dist = geom[left_df.geometry.name].distance(closest_candidate)

                # If the point is closer to given polygon update the info
                if dist < distance:
                    distance = dist
                    closest_geom = closest_candidate

            # Select the Polygon that was closest
            closest_poly = right_df.loc[right_df.intersects(closest_geom.buffer(snap_dist))]
        else:
            print("Incorrect input geometry type. Skipping ..")

        # Reset index
        geom = geom.to_frame().T.reset_index(drop=True)

        # Drop geometry from closest polygon
        closest_poly = closest_poly.drop(right_df.geometry.name, axis=1)
        closest_poly = closest_poly.reset_index(drop=True)

        # Join values
        join = geom.join(closest_poly, lsuffix='_%s' % lsuffix, rsuffix='_%s' % rsuffix)

        # Add information about distance to closest geometry if requested
        if report_dist:
            if 'dist' in join.columns:
                raise ValueError("'dist' column exists in the DataFrame. Remove it, or set 'report_dist' to False.")
            join['dist'] = distance

        closest_geometries = closest_geometries.append(join, ignore_index=True, sort=False)

    # Merge everything together
    result = pip_join.append(closest_geometries, ignore_index=True, sort=False)
    return result


def points_to_ReEDS(df, name, DIR):
    # load polygons for ReEDS BAs
    # warning that these polygons are rough and not very detailed - meant for illustrative purposes. Might be worth it later to revisit and try to fine-tune this
    # but since the multipliers aren't super strict by region, it's fine for now.
    polys = gpd.read_file(os.path.join(DIR, 'rs.shp'))
    polys.crs = "EPSG:4326"

    # load buses into Points geodataframe
    pts = gpd.GeoDataFrame(pd.DataFrame({name + '_id': df.index}),
                           geometry=gpd.points_from_xy(df.lon, df.lat), crs='epsg:4326')

    # find which ReEDS region the points belong to
    # (within the region or as close as possible, if in the ocean or something)
    pts_poly = sjoin_nearest(left_df=pts, right_df=polys, search_dist=0.2, report_dist=True)

    # load in rs to rb region mapping file
    region_map = pd.read_csv(os.path.join(DIR, 'region_map.csv'))

    # map rs (wind region) to rb (ba region)
    pts_poly = pts_poly.merge(region_map, left_on='id', right_on='rs', how='left').drop(["id", "index_right", 'dist'],
                                                                                        axis=1)
    return pts_poly

def points_to_NEEM(df, name, DIR):
    '''
    Warning, this function takes ~24 hours to run. Should only need to run once for all buses.
    '''
    # load polygons for ReEDS BAs
    # warning that these polygons are rough and not very detailed - meant for illustrative purposes. Might be worth it later to revisit and try to fine-tune this
    # but since the multipliers aren't super strict by region, it's fine for now.

    polys = gpd.read_file(os.path.join(DIR,'land_neem_regions/ez_gis.land_neem_regions.shp'))
    polys = polys.to_crs("EPSG:4326")

    # load buses into Points geodataframe

    pts = gpd.GeoDataFrame(pd.DataFrame({name + '_id': df.index}),
                           geometry=gpd.points_from_xy(df.lon, df.lat), crs='epsg:4326')

    # find which ReEDS region the points belong to
    # (within the region or as close as possible, if in the ocean or something)
    pts_poly = sjoin_nearest(left_df=pts, right_df=polys, search_dist=0.2, report_dist=True)

    return pts_poly


def calculate_ac_inv_costs(scenario, year):
    """Given a Scenario object, calculate the total cost of building that scenario's
    upgrades of lines and transformers.
    Currently uses NEEM regions to find regional multipliers.
    Currently ignores financials, but all values are in 2010 $-year.
    Need to test that there aren't any na values in regional multipliers
    (some empty parts of table)

    :param powersimdata.scenario.scenario.Scenario scenario: scenario instance.
    :param int/str year: the year of the transmission upgrades.
    :return: (*dict*) -- Total costs (line costs, transformer costs).
    """

    base_grid = Grid(scenario.info["interconnect"].split("_"))
    grid = scenario.state.get_grid()

    # find upgraded AC lines
    grid_new = cp.deepcopy(grid)
    # Reindex so that we don't get NaN when calculating upgrades for new branches
    base_grid.branch = base_grid.branch.reindex(grid_new.branch.index).fillna(0)
    grid_new.branch.rateA = grid.branch.rateA - base_grid.branch.rateA
    grid_new.branch = grid_new.branch[grid_new.branch.rateA != 0.0]

    costs = _calculate_ac_inv_costs(grid_new, year)
    return costs


def _calculate_ac_inv_costs(grid_new, year):
    """Given a grid, calculate the total cost of building that grid's
    lines and transformers.
    This function is separate from calculate_ac_inv_costs() for testing purposes.
    Currently counts Transformer and TransformerWinding as transformers.
    Currently uses NEEM regions to find regional multipliers.
    Currently ignores financials, but all values are in 2010 $-year.

    :param powersimdata.input.grid.Grid grid_new: grid instance.
    :param int/str year: year of builds (used in financials).
    :raises ValueError: if year not 2020 - 2050.
    :raises TypeError: if year gets the wrong type.
    :return: (*dict*) -- Total costs (line costs, transformer costs).
    """

    def select_kV(x, costs):
        '''

        '''
        return costs.loc[np.argmin(np.abs(costs['kV_cost'] - x.kV)), 'kV_cost']

    def select_MW(x, cost_df):
        tmp = cost_df[cost_df['kV_cost'] == x.kV_cost]
        return tmp.iloc[np.argmin(np.abs(tmp['MW'] - x.rateA))][['MW', 'costMWmi']]

    if isinstance(year, (int, str)):
        year = int(year)
        if year not in range(2020,2051):
            raise ValueError("year not in range.")
    else:
        raise TypeError("year must be int or str.")


    DIR = os.path.join(os.path.dirname(__file__), "Data")

    # import data
    ac_cost = pd.read_csv(os.path.join(DIR, "LineBase.csv"))#.astype('float64')
    ac_reg_mult = pd.read_csv(os.path.join(DIR, "LineRegMult.csv"))#.astype('float64')
    xfmr_cost = pd.read_csv(os.path.join(DIR, "Transformers.csv"))#.astype('float64')

    # map kV
    bus = grid_new.bus
    branch = grid_new.branch
    branch.loc[:, "kV"] = branch.apply(
        lambda x: bus.loc[x.from_bus_id, "baseKV"], axis=1
    )

    # separate transformers and lines
    t_mask = branch["branch_device_type"].isin(["Transformer", "TransformerWinding"])
    transformers = branch[t_mask].copy()
    lines = branch[~t_mask].copy()

    lines.loc[:, "kV_cost"] = lines.apply(lambda x: select_kv(x, ac_cost), axis=1)
    lines[["MW", "costMWmi"]] = lines.apply(lambda x: select_mw(x, ac_cost), axis=1)

    # multiply by regional multiplier
    bus_reg = pd.read_csv(
        os.path.join(data_dir, "buses_NEEMregion.csv"), index_col="bus_id"
    )

    # check that all buses included in this file and lat/long values match,
    #   otherwise re-run mapping script on mis-matching buses.

    # these buses are missing in region file
    bus_fix_index = bus[~bus.index.isin(bus_reg.index)].index
    bus_mask = bus[~bus.index.isin(bus_fix_index)]
    bus_mask = bus_mask.merge(bus_reg, how="left", on="bus_id")

    # these buses have incorrect lat/lon values in the region mapping file.
    #   re-running the region mapping script on those buses only.
    bus_fix_index2 = bus_mask[
        ~np.isclose(bus_mask.lat_x, bus_mask.lat_y)
        | ~np.isclose(bus_mask.lon_x, bus_mask.lon_y)
    ].index
    bus_fix_index_all = bus_fix_index.tolist() + bus_fix_index2.tolist()
    bus_fix = bus[bus.index.isin(bus_fix_index_all)]
    bus_fix = bus_to_neem_reg(bus_fix, data_dir)  # converts index to bus_id instead

    bus_reg.loc[
        bus_reg.index.isin(bus_fix.index), ["name_abbr", "lat", "lon"]
    ] = bus_fix[["name_abbr", "lat", "lon"]]
    bus_reg.drop(["lat", "lon"], axis=1, inplace=True)

    # map region multipliers onto lines
    ac_reg_mult = ac_reg_mult.melt(
        id_vars=["kV_cost", "MW"], var_name="name_abbr", value_name="mult"
    )

    lines = lines.merge(bus_reg, left_on="to_bus_id", right_on="bus_id", how="inner")
    lines = lines.merge(ac_reg_mult, on=["name_abbr", "kV_cost", "MW"], how="left")
    lines.rename(columns={"name_abbr": "reg_to", "mult": "mult_to"}, inplace=True)

    lines = lines.merge(bus_reg, left_on="from_bus_id", right_on="bus_id", how="inner")
    lines = lines.merge(ac_reg_mult, on=["name_abbr", "kV_cost", "MW"], how="left")
    lines.rename(columns={"name_abbr": "reg_from", "mult": "mult_from"}, inplace=True)

    # take average between 2 buses' region multipliers
    lines.loc[:, "mult"] = (lines["mult_to"] + lines["mult_from"]) / 2.0

    # calculate MWmi
    lines.loc[:, 'lengthMi'] = lines.apply(lambda x: haversine((x.from_lat, x.from_lon), (x.to_lat, x.to_lon)), axis=1)
    lines.loc[:, 'MWmi'] = lines['lengthMi'] * lines['rateA']

    # calculate cost of each line
    lines.loc[:, 'Cost'] = lines['MWmi'] * lines['costMWmi']  # * lines['mult']

    # sum of all line costs
    lines_sum = float(lines.Cost.sum())

    # calculate transformer costs
    transformers.loc[:, 'kV_cost'] = transformers.apply(lambda x: select_kV(x, xfmr_cost), axis=1)
    transformers = transformers.merge(xfmr_cost, on='kV_cost', how="left")

    #sum of all transformer costs
    transformers_sum = float(transformers.Cost.sum())

    dict1 = {"line_cost": lines_sum,"transformer_cost": transformers_sum}

    return dict1




# DC lines

# dc additions are in $2015
def calculate_dc_inv_costs(scenario, year):
    """Given a Scenario object, calculate the number of upgraded lines and
    transformers, and the total upgrade quantity (in MW and MW-miles).
    Currently only supports change tables that specify branches' id, not
    zone name. Currently lumps Transformer and TransformerWinding upgrades
    together.

    :param powersimdata.scenario.scenario.Scenario scenario: scenario instance.
    :param int/str year: the year of the upgrate to calculate costs
    :return: (*dict*) -- Total costs.
    """
    base_grid = Grid(scenario.info["interconnect"].split("_"))
    grid = scenario.state.get_grid()

    grid_new = cp.deepcopy(grid)
    # Reindex so that we don't get NaN when calculating upgrades for new DC lines
    base_grid.dcline = base_grid.dcline.reindex(grid_new.dcline.index).fillna(0)
    # find upgraded DC lines
    grid_new.dcline.Pmax = grid.dcline.Pmax - base_grid.dcline.Pmax
    grid_new.dcline = grid_new.dcline[grid_new.dcline.Pmax != 0.0]

    costs = _calculate_dc_inv_costs(grid_new, year)
    return costs

def _calculate_dc_inv_costs(grid_new, year):
    DIR = "./Data"

    # import data
    dc_cost = pd.read_excel(os.path.join(DIR, "TransCosts_real.xlsx"), sheet_name="HVDC").astype('float64')
    dc_term_cost = pd.read_excel(os.path.join(DIR, "TransCosts_real.xlsx"), sheet_name="HVDCTerminal").astype(
        'float64')

    bus = grid_new.bus
    dcline = grid_new.dcline

    if len(dcline != 0):
        # find line length
        dcline['from_lat'] = dcline.apply(lambda x: bus.loc[x.from_bus_id, 'lat'], axis=1)
        dcline['from_lon'] = dcline.apply(lambda x: bus.loc[x.from_bus_id, 'lon'], axis=1)

        dcline['to_lat'] = dcline.apply(lambda x: bus.loc[x.to_bus_id, 'lat'], axis=1)
        dcline['to_lon'] = dcline.apply(lambda x: bus.loc[x.to_bus_id, 'lon'], axis=1)

        dcline['lengthMi'] = dcline.apply(lambda x: haversine((x.from_lat, x.from_lon), (x.to_lat, x.to_lon)), axis=1)
        dcline = dcline[dcline['lengthMi'] != 0]

        # calculate MWmi value
        dcline['MWmi'] = dcline['lengthMi'] * dcline['Pmax']

        # find $/MW-mi cost
        dcline.loc[:, 'costMWmi'] = dc_cost['costMWmi'][0]

        # find base cost (excluding terminal cost)
        dcline['Cost'] = dcline['MWmi'] * dcline['costMWmi']

        # add extra terminal cost for dc
        dcline['Cost'] += dc_term_cost['costTerm'][0]

        costs = dcline['Cost'].sum()

    return costs

def calculate_gen_inv_costs(scenario,year,cost_case):
    base_grid = Grid(scenario.info["interconnect"].split("_"))
    grid = scenario.state.get_grid()

    # Find change in generation capacity
    grid_new = cp.deepcopy(grid)
    # Reindex so that we don't get NaN when calculating upgrades for new generators
    base_grid.plant = base_grid.plant.reindex(grid_new.plant.index).fillna(0)
    grid_new.plant.Pmax = grid.plant.Pmax - base_grid.plant.Pmax

    grid_new.plant = grid_new.plant[grid_new.plant.Pmax > 0.01]

    costs = _calculate_gen_inv_costs( grid_new, year, cost_case)
    return costs

def _calculate_gen_inv_costs(grid_new, year,cost_case):
    DIR = "./Data"

    plants =grid_new.plant

    #merge in regions
    pts_plant = pd.DataFrame(points_to_ReEDS(plants,name="plant")).drop("geometry",axis=1)
    plants= plants.merge(pts_plant,on='plant_id',how='inner')

    #keep region 'r' as wind region 'rs' if tech is wind, 'rb' ba region is tech is solar or battery
    plants.loc[:,'r'] = ''

    #wind regions
    rs_tech = ['wind','OfWind','csp']
    plants.loc[plants['type'].isin(rs_tech),'r'] = plants.loc[plants['type'].isin(rs_tech),'rs']
    #grid_new.plant[grid_new.plant['type'].isin(['wind','OfWind'])] = grid_tmp

    #BA regions
    rb_tech =['solar','storage','nuclear','coal','ng','hydro','geothermal','dfo','other']
    plants.loc[plants['type'].isin(rb_tech),'r'] = plants.loc[plants['type'].isin(rb_tech),'rb']

    plants.drop(['rs','rb'],axis=1,inplace=True)

    def load_cost(file_name,year,cost_case,DIR):
        pre = "2020-ATB-Summary"
        if file_name != "":
            pre = pre + "_"
        cost = pd.read_csv(os.path.join(DIR,pre+file_name+".csv"))
        cost = cost.dropna(axis=0,how='all')

        #drop non-useful columns
        cols_drop = cost.columns[~cost.columns.isin(
                [str(x) for x in cost.columns[0:6]]+ ["Metric",str(year)])] 
        cost.drop(cols_drop,axis=1,inplace=True)

        #rename year of interest column
        cost.rename(columns = {str(year): "value"},  
              inplace = True) 

        #get rid of #refs
        cost.drop(cost[cost['value'] == '#REF!'].index,inplace=True)

        #get rid of $s, commas
        cost['value'] = cost['value'].str.replace('$', '')
        cost['value'] = cost['value'].str.replace(',', '').astype('float64')

        #scale from $/kW to $/MW (for CAPEX + FOM)
        if file_name in ['CAPEX','FOM']:
            cost['value'] = 1000 * cost['value']

        cost.rename(columns = {'value': file_name},  
              inplace = True) 

        #select scenario of interest
        cost = cost[cost['CostCase']==cost_case]
        cost.drop(['CostCase'],axis=1,inplace=True)

        return cost


    gen_costs = load_cost("CAPEX",year, cost_case, DIR)
    gen_costs = gen_costs[ gen_costs['TechDetail'].isin(['HydroFlash','NPD1','newAvgCF','Class1' ,'CCAvgCF','OTRG1','LTRG1','4Hr Battery Storage','Seattle'])] #only keep HydroFlash for geothermal
    gen_costs.replace(['OffShoreWind','LandbasedWind','UtilityPV','Battery','CSP','NaturalGas','Hydropower','Nuclear','Biopower','Geothermal','Coal'], ['OfWind','wind','solar','storage','csp','ng','hydro','nuclear','bio','geothermal','coal'],inplace=True)
    gen_costs.drop(['Key','FinancialCase','CRPYears'],axis=1,inplace=True)
    plants = plants[~plants.type.isin(['dfo','other'])]

    plants = plants.merge(gen_costs,right_on='Technology',left_on='type',how='left')

    #regional multiplier merge
    region_multiplier = pd.read_csv("in/reg_cap_cost_mult_default.csv")
    region_multiplier = region_multiplier[ region_multiplier['i'].isin(['wind-ofs_1','wind-ons_1','upv_1','battery','coal-new','Gas-CC','Hydro','Nuclear','geothermal']) ]
    region_multiplier.replace(['wind-ofs_1','wind-ons_1','upv_1','battery','Gas-CC','Nuclear','Hydro','coal-new','csp-ns'],['OfWind','wind','solar','storage','ng','nuclear','hydro','coal','csp'],inplace=True)
    plants = plants.merge(region_multiplier,left_on=['r','Technology'],right_on=['r','i'],how='left')

    plants.loc[:,'CAPEX_total'] = plants['CAPEX']* plants['Pmax'] * plants['reg_cap_cost_mult']
    tech_sum = plants.groupby(['Technology'])['CAPEX_total'].sum()

    return tech_sum



