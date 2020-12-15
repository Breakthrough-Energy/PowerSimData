## Third Party Data
This package contains a variety of materials, including data sets and related materials. The third party data sets and related materials are provided by their respective publishers, and may be subject to separate and additional terms and conditions. The following summarizes the sources of the applicable data, and details regarding the applicable provider. Additional terms and conditions, including certain restrictions on commercial use, redistribution, or other similar restrictions, may apply to the applicable data sets. If you cannot comply with the terms of the applicable data collection, you may not use that data, and your ability to make use of this software package, and/or the results or output you are able to generate through its use may be impacted. Please review the information provided below, and the terms and conditions provided by the publisher at the original source for more information.


### Electric Grid
#### Network
##### Source
* Name: USATestSystem
* Author: Y. Xu et al.
* Description: High spatial and temporal resolution test system on the footprint of continental United States.
* DOI: 10.5281/zenodo.3530898
* Source: https://zenodo.org/record/3530898

##### Destination
* Modifications to source files(s): None
* Location: ***powersimdata/network/usa_tamu/data/****

##### General Purpose
The dataset is used to generate simulation inputs

##### Note
https://creativecommons.org/licenses/by/4.0/legalcode


---
### Investment Costs
#### Generator Base Costs

##### Source
* Name: Annual Technology Baseline
* Author: National Renewable Energy Laboratory
* Description: The ATB is a populated framework to identify technology-specific cost and performance parameters or other investment decision metrics across a range of fuel price conditions as well as site-specific conditions for electric generation technologies at present and with projections through 2050.
* Documentation: https://atb.nrel.gov/electricity/2020/about.php
* Source: https://atb.nrel.gov/

##### Destination
* Modifications to source files(s): None
* Location: ***powersimdata/design/investment/data/2020-ATB-Summary_CAPEX.csv***

##### General Purpose
Base generator and storage costs are used to estimate the cost of new generation capacity.

#### Generator Regional Multipliers
##### Source
* Name: Regional Energy Deployment System (ReEDS) 2.0
* Author: National Renewable Energy Laboratory
* Description: The Regional Energy Deployment System (ReEDS) is a capacity planning and dispatch model for the North American electricity system.
* Documentation: https://www.nrel.gov/docs/fy20osti/74111.pdf
* Source: https://github.com/NREL/ReEDS_OpenAccess

##### Destination
* Modifications to source files(s): None
* Location:
  * Shapes: ***powersimdata/design/investment/data/mapping/gis_rs.csv***
  * Coefficients: ***powersimdata/design/investment/data/reg_cap_cost_mult_default.csv***

##### General Purpose
The shapes and coefficients are used to estimate 'multipliers' on base costs for new generation.

#### AC Transformers Base Costs

##### Source
* Name: Transmission Cost Estimation Guide
* Author: Midcontinent Independent System Operator
* Description: Cost per MVA for power transformers, by voltage
* Documentation: https://cdn.misoenergy.org/20200211%20PSC%20Item%2005c%20Cost%20Estimation%20Guide%20for%20MTEP20%20DRAFT%20Redline425617.pdf
* Source: Section 3.2 with Documentation, table: "Power transformer ($/MVA)"

##### Destination
* Modifications to source files(s): None
* Location: ***powersimdata/design/investment/data/transformer_cost.csv***

##### General Purpose
Base costs for AC transformers, by voltage, are used to estimate the cost of transmission upgrade projects.

#### Transmission Line Base Costs

##### Source
* Name: Phase 2 Report: Interregional Transmission Development and Analysis for Three Stakeholder Selected ScenariosAndGas-Electric System Interface Study
* Author: Eastern Interconnection Planning Collaborative
* Description: Costs for New Lines (AC) and HVDC Facilities
* Documentation: https://static1.squarespace.com/static/5b1032e545776e01e7058845/t/5cb37389c830257d563c0034/1555264398511/02+Phase+II.pdf
* Source: Table 5-1 (AC Lines) and 5-5 (HVDC facilities) within Documentation

##### Destination
* Modifications to source files(s): None
* Location: ***powersimdata/design/investment/const.py***, variables `ac_line_cost` and `hvdc_line_cost`.

##### General Purpose
Base costs for AC and HVDC transmission lines are used to estimate the cost of transmission upgrade projects.

#### HVDC Terminal Costs

##### Source
* Name: Transmission Cost Estimation Guide
* Author: Midcontinent Independent System Operator
* Description: Estimated cost per MW for Line Commutated Converter (LCC) converter station (one end)
* Documentation: https://cdn.misoenergy.org/20200211%20PSC%20Item%2005c%20Cost%20Estimation%20Guide%20for%20MTEP20%20DRAFT%20Redline425617.pdf
* Source: Section 3.3 within Documentation, table: "Converter Station Line Commutated Converter (LCC) – one end"

##### Destination
* Modifications to source files(s): None
* Location: ***powersimdata/design/investment/const.py***, variable `hvdc_terminal_cost_per_MW`.

##### General Purpose
Converter station per-MW costs are used to estimate the cost of new HVDC projects.

#### Transmission Regional Multiplier Shapes

##### Source
* Name: Energy Zones Mapping Tool
* Author: Eastern Interconnection States' Planning Council
* Description: The Energy Zones Mapping Tool is a free online mapping tool to identify potential energy resource areas and energy corridors in the United States.
* Documentation: https://ezmt.anl.gov/about_the_study
* Source: https://ezmt.anl.gov/

##### Destination
* Modifications to source files(s): Boundaries simplified in QGIS using the Douglas-Peucker method with 1 km distance.
* Location: ***powersimdata/design/investment/data/NEEM/***
  * ***NEEMregions.cpg***
  * ***NEEMregions.dbf***
  * ***NEEMregions.prj***
  * ***NEEMregions.qpj***
  * ***NEEMregions.shp***
  * ***NEEMregions.shx***

##### General Purpose
Transmission region shapes are used to assign regional multipliers to transmission upgrade projects.

#### Transmission Regional Multipliers (Eastern Interconnection)

##### Source
* Name: Phase 2 Report: Interregional Transmission Development and Analysis for Three Stakeholder Selected ScenariosAndGas-Electric System Interface Study
* Author: Eastern Interconnection Planning Collaborative
* Description: NEEM Regional Multipliers for New Lines
* Documentation: https://static1.squarespace.com/static/5b1032e545776e01e7058845/t/5cb37389c830257d563c0034/1555264398511/02+Phase+II.pdf
* Source: Table 5-2 within Documentation.

##### Destination
* Modifications to source files(s): None
* Location: ***powersimdata/design/investment/data/LineRegMult.csv***

##### General Purpose
Regional multipliers are used to multiply transmission base costs for transmission upgrade projects.

#### Transmission Regional Multipliers (Western Interconnection, ERCOT)

##### Source
* Name: Regional Energy Deployment System (ReEDS) Model Documentation: Version 2018
* Author: National Renewable Energy Laboratory
* Description: The Regional Energy Deployment System (ReEDS) is a capacity planning and dispatch model for the North American electricity system.
* Documentation: https://www.nrel.gov/docs/fy19osti/72023.pdf
* Source: Section 5.2 within Documentation

##### Destination
* Modifications to source files(s): None
* Location: ***powersimdata/design/investment/data/LineRegMult.csv***

##### General Purpose
Regional multipliers are used to multiply transmission base costs for transmission upgrade projects.

---
### Note for Data from the National Renewable Energy Laboratory
Access to or use of any data or software made available on this server ("Data") shall impose the following obligations on the user, and use of the Data constitutes user's agreement to these terms.
The user is granted the right, without any fee or cost, to use or copy the Data, provided that this entire notice appears in all copies of the Data.
Further, the user agrees to credit the U.S. Department of Energy (DOE)/NREL/ALLIANCE in any publication that results from the use of the Data.
The names DOE/NREL/ALLIANCE, however, may not be used in any advertising or publicity to endorse or promote any products or commercial entities unless specific written permission is obtained from DOE/NREL/ ALLIANCE.
The user also understands that DOE/NREL/ALLIANCE are not obligated to provide the user with any support, consulting, training or assistance of any kind with regard to the use of the Data or to provide the user with any updates, revisions or new versions thereof.
DOE, NREL, and ALLIANCE do not guarantee or endorse any results generated by use of the Data, and user is entirely responsible for the results and any reliance on the results or the Data in general.

USER AGREES TO INDEMNIFY DOE/NREL/ALLIANCE AND ITS SUBSIDIARIES, AFFILIATES, OFFICERS, AGENTS, AND EMPLOYEES AGAINST ANY CLAIM OR DEMAND, INCLUDING REASONABLE ATTORNEYS' FEES, RELATED TO USER’S USE OF THE DATA.
THE DATA ARE PROVIDED BY DOE/NREL/ALLIANCE "AS IS," AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING BUT NOT LIMITED TO THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
IN NO EVENT SHALL DOE/NREL/ALLIANCE BE LIABLE FOR ANY SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER, INCLUDING BUT NOT LIMITED TO CLAIMS ASSOCIATED WITH THE LOSS OF DATA OR PROFITS, THAT MAY RESULT FROM AN ACTION IN CONTRACT, NEGLIGENCE OR OTHER TORTIOUS CLAIM THAT ARISES OUT OF OR IN CONNECTION WITH THE ACCESS, USE OR PERFORMANCE OF THE DATA.
