import pickle

from powersimdata.input.transform_profile import TransformProfile


def export_grid(grid, file_path):
    """Save a grid object locally.

    :param powersimdata.input.grid.Grid grid: a Grid object
    :param str file_path: path to save the result, including the filename
    """
    print(f"Writing grid object to {file_path} on local machine")
    with open(file_path, "a") as f:
        pickle.dump(grid, f)


def export_transformed_profile(kind, scenario_info, grid, ct, file_path, slice=True):
    """Apply transformation to the given kind of profile and save the result locally.

    :param str kind: which profile to export. This parameter is passed to
        :meth:`TransformProfile.get_profile`.
    :param dict scenario_info: a dict containing the profile version, with
        key in the form base_{kind}
    :param powersimdata.input.grid.Grid grid: a Grid object previously
        transformed.
    :param dict ct: change table.
    :param str file_path: path to save the result, including the filename
    :param bool slice: whether to slice the profiles by the Scenario's time range.
    """
    tp = TransformProfile(scenario_info, grid, ct, slice)
    profile = tp.get_profile(kind)
    print(f"Writing scaled {kind} profile to {file_path} on local machine")
    profile.to_csv(file_path)
