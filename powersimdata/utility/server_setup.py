import os
import posixpath
from pathlib import Path

SERVER_ADDRESS = "becompute01.gatesventures.com"
DATA_ROOT_DIR = "/mnt/bes/pcm"

SCENARIO_LIST = posixpath.join(DATA_ROOT_DIR, "ScenarioList.csv")
EXECUTE_LIST = posixpath.join(DATA_ROOT_DIR, "ExecuteList.csv")

REL_EXECUTE_DIR = "tmp"
REL_BASE_PROFILE_DIR = "raw"
REL_INPUT_DIR = "data/input"
REL_OUTPUT_DIR = "data/output"

EXECUTE_DIR = posixpath.join(DATA_ROOT_DIR, REL_EXECUTE_DIR)
BASE_PROFILE_DIR = posixpath.join(DATA_ROOT_DIR, REL_BASE_PROFILE_DIR)
INPUT_DIR = posixpath.join(DATA_ROOT_DIR, REL_INPUT_DIR)
OUTPUT_DIR = posixpath.join(DATA_ROOT_DIR, REL_OUTPUT_DIR)

LOCAL_DIR = os.path.join(str(Path.home()), "ScenarioData", "")

LOCAL_EXECUTE_DIR = os.path.join(LOCAL_DIR, REL_EXECUTE_DIR)
LOCAL_BASE_PROFILE_DIR = os.path.join(LOCAL_DIR, REL_BASE_PROFILE_DIR)
LOCAL_INPUT_DIR = os.path.join(LOCAL_DIR, REL_INPUT_DIR)
LOCAL_OUTPUT_DIR = os.path.join(LOCAL_DIR, REL_OUTPUT_DIR)

MODEL_DIR = "/home/bes/pcm"


def get_server_user():
    """Returns the first username found using the following sources:

    - BE_SERVER_USER environment variable
    - powersimdata/utility/.server_user
    - username of the active login.

    :return: (*str*) -- user name to be used to log into server.
    """
    server_user = os.getenv("BE_SERVER_USER")
    if server_user is not None:
        return server_user

    dir_path = os.path.dirname(os.path.realpath(__file__))
    try:
        with open(os.path.join(dir_path, ".server_user")) as f:
            server_user = f.read().strip()
    except FileNotFoundError:
        server_user = os.getlogin()

    return server_user
