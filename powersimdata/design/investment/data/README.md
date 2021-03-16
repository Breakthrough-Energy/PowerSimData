### Data sources used for each type of cost

  *	Transmission base costs (converted to $/MW-mile) [EIPC]
    * AC lines: [EIPC] table 5-1
    * DC lines: [EIPC] table 5-5 (assumes 500 kV HVDC)
    * Transformers: [EIPC] table 5-8
  * Generation base costs [ATB]
    * NREL’s 2020 ATB, CAPEX summary page
  * Regional multipliers
    * Generation cost regional multipliers: [ReEDS]
        * I did some mapping using ReEDS regions from: ReEDS/bokehpivot/in/
          * gis_rs.csv
          * /reeds2/region_map.csv
          * /reeds2/hierarchy.csv
    * Regional multiplier values from: ReEDS/inputs/reg_cap_cost_mult/reg_cap_cost_mult_default.csv
      * AC lines cost regional multipliers: 
        * [EIPC] table 5-2 (for Eastern regions)
        * [ReEDS] documentation page for ERCOT, Western regions.
        * [NEEM] for shapefile: mapping buses to NEEM regions

### Source file locations/details

**EIPC**: https://www.dropbox.com/s/qell57fb3e7d5g4/02%2BPhase%2BII.pdf?dl=0

  * This is where ReEDS sourced their transmission cost estimates. But, we have more kV detail than them, so we can get more specific (costs by kV).
  * (unused) substation cost data

EIPC/ReEDS multiplier data manually formatted in xlsx: https://www.dropbox.com/scl/fi/z9bfmfkvmxupvtzhe589q/TransCosts_real.xlsx?dl=0&rlkey=0ds2q2rx384y5kx98rmfcrk8q

Note: I removed underground lines as options unless it was one of the only options (like NY). This should probably be changed. 
Note: I manually added the Western Interconnect and ERCOT NEEM regions. ReEDS documentation says they used line regional multipliers of 1 and California is 2.25 that of the rest of WECC. Their map does not match this documentation, however, so if possible, this should be cross-checked. PowerGenome also seems to believe this documentation (of 2.25 multiplier), as seen here: https://github.com/gschivley/pg_misc/blob/master/create_clusters/site_interconnection_costs.py#L32-L155. Also, it looks like Greg pulled these values from the ReEDS multiplier map, but there are some inconsistencies with Eastern regions (also with ReEDS documentation).
Note: there are also substation costs in this excel sheet

NREL’s 2020 **ATB**: https://atb.nrel.gov
ATB data: (Mac) https://www.dropbox.com/scl/fi/nj542inqw2e0k1lw1ofry/2020-ATB-Data-Mac.xlsm?dl=0&rlkey=zwesaydrm1vi0488qg2q9n7t8
(Other) https://www.dropbox.com/scl/fi/x5np0b25qy1bg8mnlwnh6/2020-ATB-Data-1.xlsm?dl=0&rlkey=tq1e5cd3q7tsq4u81al5vb2s9

**ReEDS**: ReEDS 2.0 Version 2019 (request license): https://github.com/NREL/ReEDS_OpenAccess

**NEEM regions shapefile**:

  * Original shapefile: https://www.dropbox.com/sh/6adq9plptczz6hb/AABseOxIbMsbLDTy-LQD9PK-a?dl=0
  *	Simplified shapefile used in PowerSimData “investment_cost” branch: powersimdata/design/investment/data/NEEM
    * Note, this was simplified (to make point mapping faster) in QGIS using “Distance (Douglas-Peucker) method with 1 km tolerance.
