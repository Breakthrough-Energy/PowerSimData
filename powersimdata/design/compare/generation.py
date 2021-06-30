from powersimdata.design.compare.helpers import _reindex_as_necessary
from powersimdata.input.check import _check_data_frame


def calculate_plant_difference(plant1, plant2):
    """Calculate the capacity differences between two plant data frames. If capacity in
    ``plant2`` is larger than capacity in ``plant1``, the return will be positive.

    :param pandas.DataFrame plant1: first plant data frame.
    :param pandas.DataFrame plant2: second plant data frame.
    :return: (*pandas.DataFrame*) -- merged data frames with a new 'diff' column.
    """
    _check_data_frame(plant1, "plant1")
    _check_data_frame(plant2, "plant2")
    # Reindex so that we don't get NaN when calculating upgrades for new generators
    plant1, plant2 = _reindex_as_necessary(plant1, plant2, ["bus_id", "type"])
    plant_merge = plant1.merge(
        plant2, how="outer", right_index=True, left_index=True, suffixes=(None, "_2")
    )
    plant_merge["diff"] = plant_merge.Pmax_2.fillna(0) - plant_merge.Pmax.fillna(0)
    # Ensure that lats & lons get filled in as necessary from plant2 entries
    for l in ["lat", "lon"]:
        plant_merge[l].fillna(plant_merge[f"{l}_2"], inplace=True)

    return plant_merge
