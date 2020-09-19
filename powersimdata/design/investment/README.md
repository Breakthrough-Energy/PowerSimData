Note: Not all tests are done. 

This adds cost calculations for all new (added since base_grid) transmission, generation, and storage capacity.

`create_mapping_files.py` contains functions that help create shapefiles and map lat/lon points to regions from shapefiles. 
`investment_costs.py` uses these mappings to find the regional cost multipliers (for both generation/storage and ac transmission).

### Fundamental calculations
There are 3 separate cost calculations: one for dclines, one for branches, one for plants.


**branches: calculate_ac_inv_costs**

For all capacity added on a **line**, the investment cost is:
`Cost ($2010) = rateA (MW) * lengthMi (miles) * costMWmi ($2010/MW-mi) * mult (regional cost multiplier, unitless)`
Then all lines are summed.

For all capacity added on a **transformer**, the investment cost is:
`Cost (per transformer at a given kV level, $2010)`

Now that I'm thinking about this again, this is a flawed method because if we're only slightly scaling a transformer, this is overestimating the cost. Might be better to apply to completely new transformers only? Either ignore this cost or reevaluate its calculation.



**dclines: calculate_dc_inv_costs**

For all capacity added on a dcline, the investment cost is:
`Cost ($2015) = Pmax (MW) * lengthMi (miles) * costMWmi ($2015/MW-mi) + dc_term_cost (DC terminal cost $2015)`
Then all line costs are summed.

**plant: calculate_gen_inv_costs**

For all capacity added on a plant, the investment cost is:
`Cost ($2018) = Pmax (MW) * CAPEX ($2018/MW) * reg_cap_cost_mult (regional capital cost multiplier, unitless)`
Then all costs are summed by technology (so you can ignore the non-renewables/storage if you want).



### Methods



**branches: calculate_ac_inv_costs**

- Find new upgrades for each line/transformer (change in MW rating): `grid.branch.rateA - base_grid.branch.rateA`
- Drop unchanged branches.
- Map branches to corresponding kV.
- Separate lines and transformers (TransformerWindings dropped).
- Lines: Find closest kV present in the corresponding cost table using `select_kv` . Labeled "kV_cost." 
- Lines: Find MW closest to the line's rateA that exists within the corresponding kV_cost sub-table. Then use that costMWmi base cost value.
- (messy) Lines: Import bus to NEEM mapping file. Check that no buses you need are missing. Check that buses have the same lat/lon values as the pre-made mapping file. If any issues, re-map NEEM regions to those points.
- Lines: Map regional multipliers onto lines' to_bus and from_bus by NEEM region.
- Lines: Regional multiplier is then the average of the 2 buses' regional multipliers.
- Lines: final calculations
- Xfmrs: Find closest kV present in the corresponding cost table using `select_kv` . Labeled "kV_cost." 
- Xfmrs: Map kV_cost to corresponding transformer cost.

**Warning**: Now that I think about this again, I bet the transformer costs are too high with this method. If we upgrade the rating just slightly, it's going to count this as an entirely new transformer. We could just drop this investment cost altogether, or just include on totally new transformers? Not sure.

**dcline: calculate_dc_inv_costs**

- Find new capacity for each dcline (change in capacity): `grid.dcline.Pmax - base_grid.dcline.Pmax`
- Drop dcline if no changes.
- Map using buses to get the from/to lat/lon's of line.
- Find line length. Find MWmi.
- Only one costMWmi value, so multiply this by MWmi.
- Add HVDC terminal cost term.

**plant: calculate_gen_inv_costs**

- Find new capacity for each plant (change in generation capacity): `grid.plant.Pmax - base_grid.plant.Pmax`
- Drop plants < 0.1 MW.
- Drop "dfo" and "other" because no ATB cost data available.
- Load in base CAPEX costs from ATB data and select cost year/cost_case out of "Conservative", "Moderate", and "Advanced."
- Select (arbitrary) TechDetail (sub-technology) because we can't differentiate between these yet in our plants.
- Map base costs to plants by "Technology".
- Map plant location to ReEDS region (for regional cost multipliers).
- (messy) If a technology is wind or wind_offshore or csp, regions are in rs (wind resource region), so keep rs is kept as the region to map. If technology is another tech, regions are in rb (BA region), so keep rb as the region to map.
- Map ["Technology","r" (region)] to ReEDS regional capital cost multipliers. Keep (arbitrary) subclasses for renewables.
- Final calculations.

**Warning**: there's a lot of messy code here right now because I'm manually dropping a lot of subtypes of technologies so we only have one type.

## Mapping functions

**sjoin_nearest**: joins a geodataframe of Points and Polygons/Multipolygons. Used in `points_to_polys`.

**points_to_polys**: joins a dataframe (which includes lat and lon columns) with a shapefile. Used in `bus_to_neem_reg` and `plant_to_reeds_reg`.



**Functions used for AC regional multiplier mapping**

**bus_to_neem_reg**: maps bus locations to NEEM regions. Used in `write_bus_neem_map` and (if there are errors in the mapping file produced in `write_bus_neem_map`), this function is also used in `_calculate_ac_inv_costs`.

**write_bus_neem_map**: maps all base_grid bus locations to NEEM regions and produces a csv mapping file: regionsNEEM.shp. This csv is used in `_calculate_ac_inv_costs`.



**Functions used for generation/storage regional multiplier mapping**

**write_poly_shapefile**: Using a csv with specified geometry, creates the shapefile for ReEDS wind resource regions: rs.shp. This shp is used in `plant_to_reeds_reg`.

**plant_to_reeds_reg**: maps plant locations to ReEDS regions. Used in `_calculate_gen_inv_costs`.


### Sources (more specifics in data folder README.md)

**branches: calculate_ac_inv_costs**

- base costs: EIPC
- regional multipliers: EIPC/NEEM

**branches: calculate_dc_inv_costs**

- base costs: EIPC

**plant: calculate_gen_inv_costs**

- base costs: NREL's 2020 ATB
- regional multipliers: ReEDS 2.0 Version 2019

**To do:**

- requirements.txt not necessarily correct -- will need to fix pipfile.

- Untested on storage scenarios.

- Write tests for calculate_gen_inv_costs.

- $Dollar-years are inconsistent. Need a function to convert to inflate to proper year.

- If we want to have financial information other than the default ATB values, a separate financials module will be useful for CAPEX/other calculations.

- Figure out issue with transformers described above.

- Find correct wind and solar classes (based on wind speed, irradience) to map to ATB costs and ReEDS regional cost multipliers.