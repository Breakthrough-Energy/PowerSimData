This adds cost calculations for all new (added since base_grid) transmission, generation, and storage capacity.

`create_mapping_files.py` contains functions that help create shapefiles and map lat/lon points to regions from shapefiles. 
`investment_costs.py` uses these mappings to find the regional cost multipliers (for both generation/storage and ac transmission).

### Fundamental calculations
There are 3 separate cost calculations: one for dclines, one for branches (AC transmission), one for plants.

#### branches: calculate_ac_inv_costs

For all capacity added on a **line**, the investment cost is:
`Cost ($today) = rateA (MW) * lengthMi (miles) * costMWmi ($2010/MW-mi) * mult (regional cost multiplier) * inflation($2010 to today)`
Then all lines are summed.

For all capacity added on a **transformer**, the investment cost is:
`Cost ($today) = rateA (MW) * perMWcost ($2020/MW) * mult (regional cost multiplier) * inflation($2020 to today)`

#### dclines: calculate_dc_inv_costs

For all capacity added on a dcline, the investment cost is:
`Cost ($today) = Pmax (MW) * (lengthMi (miles) * costMWmi ($2015/MW-mi) * inflation(2015 to today) + 2 * terminal_cost_per_MW ($2020) * inflation($2020 to today))`
Then all line costs are summed.

#### plant: calculate_gen_inv_costs

For all capacity added on a plant, the investment cost is:
`Cost ($today) = Pmax (MW) * CAPEX ($2018/MW) * reg_cap_cost_mult (regional capital cost multiplier) * inflation($2018 to today)`
Then all costs are summed by technology (so you can ignore the non-renewables/storage if you want).


### Methods

#### branches: calculate_ac_inv_costs

- Find new upgrades for each line/transformer (change in MW rating): `grid.branch.rateA - base_grid.branch.rateA`
- Drop unchanged branches.
- Map branches to corresponding kV.
- Separate lines and transformers (TransformerWindings dropped).
- Lines: Find closest kV present in the corresponding cost table using `select_kv` . Labeled "kV_cost." 
- Lines: Find MW closest to the line's rateA that exists within the corresponding kV_cost sub-table. Then use that costMWmi base cost value.
- Lines: Import bus to NEEM mapping file. Check that no buses you need are missing. Check that buses have the same lat/lon values as the pre-made mapping file. If any issues, re-map NEEM regions to those points.
- Lines: Map regional multipliers onto lines' to_bus and from_bus by NEEM region.
- Lines: Regional multiplier is then the average of the 2 buses' regional multipliers.
- Lines: Inflation is applied to scale from 2010 dollars to present.
- Lines: final calculations
- Xfmrs: Find closest kV present in the corresponding cost table, for each side of the transformer, to get per-MW values.
- Xfmrs: Multiply per-MW value by upgraded MW.
- Xfmrs: Regional multiplier is then applied.
- Xfmrs: Inflation is applied to scale from 2020 dollars to present.

#### dcline: calculate_dc_inv_costs

- Find new capacity for each dcline (change in capacity): `grid.dcline.Pmax - base_grid.dcline.Pmax`
- Drop dcline if no changes.
- Map using buses to get the from/to lat/lon's of line.
- Find line length. Find MWmi.
- Only one costMWmi value, so multiply this by MWmi.
- Add per-MW terminal costs for each side of the new line.
- Apply inflation to scale to present dollars.

#### plant: calculate_gen_inv_costs

- Find new capacity for each plant (change in generation capacity): `grid.plant.Pmax - base_grid.plant.Pmax`
- Drop plants < 0.1 MW.
- Drop "dfo" and "other" because no ATB cost data available.
- Load in base CAPEX costs from ATB data and select cost year/cost_case out of "Conservative", "Moderate", and "Advanced."
- Select (arbitrary) TechDetail (sub-technology) because we can't differentiate between these yet in our plants.
- Map base costs to plants by "Technology".
- Map plant location to ReEDS region (for regional cost multipliers).
- If a technology is wind or wind_offshore or csp, regions are in rs (wind resource region), so keep rs is kept as the region to map. If technology is another tech, regions are in rb (BA region), so keep rb as the region to map.
- Map ["Technology", "r" (region)] to ReEDS regional capital cost multipliers. Keep (arbitrary) subclasses for renewables.
- Apply inflation to scale 2018 dollars to present.
- Final calculations.


### Mapping functions

`sjoin_nearest`: joins a geodataframe of Points and Polygons/Multipolygons. Used in `points_to_polys`.

`points_to_polys`: joins a dataframe (which includes lat and lon columns) with a shapefile. Used in `bus_to_neem_reg` and `plant_to_reeds_reg`.

#### Functions used for AC regional multiplier mapping

`bus_to_neem_reg`: maps bus locations to NEEM regions. Used in `write_bus_neem_map` and (if there are errors in the mapping file produced in `write_bus_neem_map`), this function is also used in `_calculate_ac_inv_costs`.

`write_bus_neem_map`: maps all base_grid bus locations to NEEM regions and produces a csv mapping file: regionsNEEM.shp. This csv is used in `_calculate_ac_inv_costs`.


#### Functions used for generation/storage regional multiplier mapping

`write_poly_shapefile`: using a csv with specified geometry, creates the shapefile for ReEDS wind resource regions: rs.shp. This shp is used in `plant_to_reeds_reg`.

`plant_to_reeds_reg`: maps plant locations to ReEDS regions. Used in `_calculate_gen_inv_costs`.


### Sources

See [ATTRIBUTION.md](../../../ATTRIBUTION.md).

#### Potential improvements:

- If we want to have financial information other than the default ATB values, a separate financials module will be useful for CAPEX/other calculations.

- Find correct wind and solar classes (based on wind speed, irradiance) to map to ATB costs and ReEDS regional cost multipliers.
