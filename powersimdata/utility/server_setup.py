import os
from pathlib import Path

SERVER_ADDRESS = os.getenv("BE_SERVER_ADDRESS", "becompute01.gatesventures.com")
SERVER_SSH_PORT = os.getenv("BE_SERVER_SSH_PORT", 22)
BACKUP_DATA_ROOT_DIR = "/mnt/RE-Storage/v2"
DATA_ROOT_DIR = "/mnt/bes/pcm"
EXECUTE_DIR = "tmp"
INPUT_DIR = ("data", "input")
OUTPUT_DIR = ("data", "output")
LOCAL_DIR = os.path.join(Path.home(), "ScenarioData", "")
MODEL_DIR = "/home/bes/pcm"


class DeploymentMode:
    Server = "SERVER"
    Container = "CONTAINER"


def get_deployment_mode():
    mode = os.getenv("DEPLOYMENT_MODE")
    if mode is None:
        return DeploymentMode.Server
    return DeploymentMode.Container


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
