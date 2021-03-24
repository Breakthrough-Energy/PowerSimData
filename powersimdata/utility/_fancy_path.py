import os
from importlib import import_module

BE_SERVER_OS = os.getenv("BE_SERVER_OS", "unix")


def get_path_module():
    if BE_SERVER_OS == "unix":
        fancy_path = import_module("posixpath")
    elif BE_SERVER_OS == "windows":
        fancy_path = import_module("ntpath")
    else:
        raise ValueError(f"Unknown platform {BE_SERVER_OS}")
    return fancy_path
