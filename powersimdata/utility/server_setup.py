import os

from powersimdata.utility.config import get_config, get_deployment_mode

config = get_config()
SERVER_ADDRESS = config.SERVER_ADDRESS
SERVER_SSH_PORT = config.SERVER_SSH_PORT
BACKUP_DATA_ROOT_DIR = config.BACKUP_DATA_ROOT_DIR
DATA_ROOT_DIR = config.DATA_ROOT_DIR
EXECUTE_DIR = config.EXECUTE_DIR
INPUT_DIR = config.INPUT_DIR
OUTPUT_DIR = config.OUTPUT_DIR
LOCAL_DIR = config.LOCAL_DIR
MODEL_DIR = config.MODEL_DIR
ENGINE_DIR = config.ENGINE_DIR
DEPLOYMENT_MODE = get_deployment_mode()
BLOB_TOKEN_RO = "?sv=2021-06-08&ss=b&srt=co&sp=rl&se=2050-08-06T01:31:08Z&st=2022-08-05T17:31:08Z&spr=https&sig=ORHiRQQCocyaHXV2phhSN92GFhRnaHuGOecskxsmG3U%3D"

os.makedirs(LOCAL_DIR, exist_ok=True)


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
