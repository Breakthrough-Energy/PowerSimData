from powersimdata.input.const import casemat_const

# The index name of each data frame
indices = {
    "sub": "sub_id",
    "bus2sub": "bus_id",
    "branch": "branch_id",
    "bus": "bus_id",
    "dcline": "dcline_id",
    "plant": "plant_id",
}

# AC lines
augment_col_name_branch = [
    "branch_device_type",
    "interconnect",
    "from_zone_id",
    "to_zone_id",
    "from_zone_name",
    "to_zone_name",
    "from_lat",
    "from_lon",
    "to_lat",
    "to_lon",
]
augment_col_type_branch = [
    "str",
    "str",
    "int",
    "int",
    "str",
    "str",
    "float",
    "float",
    "float",
    "float",
]
col_name_branch = casemat_const.col_name_branch + augment_col_name_branch
col_type_branch = casemat_const.col_type_branch + augment_col_type_branch


# bus
augment_col_name_bus = ["interconnect", "lat", "lon"]
augment_col_type_bus = ["str", "float", "float"]
col_name_bus = casemat_const.col_name_bus + augment_col_name_bus
col_type_bus = casemat_const.col_type_bus + augment_col_type_bus


# bus to substations
col_name_bus2sub = casemat_const.col_name_bus2sub
col_type_bus2sub = casemat_const.col_type_bus2sub


# DC lines
augment_col_name_dcline = ["from_interconnect", "to_interconnect"]
augment_col_type_dcline = ["str", "str"]
col_name_dcline = casemat_const.col_name_dcline + augment_col_name_dcline
col_type_dcline = casemat_const.col_type_dcline + augment_col_type_dcline


# Generation Cost
augment_col_name_gencost = ["interconnect"]
augment_col_type_gencost = ["str"]
col_name_gencost = casemat_const.col_name_gencost + augment_col_name_gencost
col_type_gencost = casemat_const.col_type_gencost + augment_col_type_gencost


# Generator
augment_col_name_plant = [
    "type",
    "interconnect",
    "GenFuelCost",
    "GenIOB",
    "GenIOC",
    "GenIOD",
    "zone_id",
    "zone_name",
    "lat",
    "lon",
]
augment_col_type_plant = [
    "str",
    "str",
    "float",
    "float",
    "float",
    "int",
    "int",
    "str",
    "float",
    "float",
]
col_name_plant = casemat_const.col_name_plant + augment_col_name_plant
col_type_plant = casemat_const.col_type_plant + augment_col_type_plant


# substations
col_name_sub = casemat_const.col_name_sub
col_type_sub = casemat_const.col_type_sub


# storage
col_name_storage_storagedata = casemat_const.col_name_storage_storagedata
col_type_storage_storagedata = casemat_const.col_type_storage_storagedata
