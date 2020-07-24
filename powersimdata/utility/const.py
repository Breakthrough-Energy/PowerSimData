import os
import posixpath
from pathlib import Path

SERVER_ADDRESS = "becompute01.gatesventures.com"
DATA_ROOT_DIR = "/mnt/bes/pcm"
SCENARIO_LIST = posixpath.join(DATA_ROOT_DIR, "ScenarioList.csv")
EXECUTE_LIST = posixpath.join(DATA_ROOT_DIR, "ExecuteList.csv")
EXECUTE_DIR = posixpath.join(DATA_ROOT_DIR, "tmp")
BASE_PROFILE_DIR = posixpath.join(DATA_ROOT_DIR, "raw")
INPUT_DIR = posixpath.join(DATA_ROOT_DIR, "data/input")
OUTPUT_DIR = posixpath.join(DATA_ROOT_DIR, "data/output")
LOCAL_DIR = os.path.join(str(Path.home()), "ScenarioData", "")
MODEL_DIR = "/home/bes/pcm"


def get_server_user():
    """Returns either the content of powersimdata/utility/.server_user, or the
    username of the active login.

    :return: (*str*) -- user name to be used to log into server.
    """
    dir_path = os.path.dirname(os.path.realpath(__file__))
    try:
        with open(os.path.join(dir_path, ".server_user")) as f:
            server_user = f.read()
    except FileNotFoundError:
        server_user = os.getlogin()

    return server_user
