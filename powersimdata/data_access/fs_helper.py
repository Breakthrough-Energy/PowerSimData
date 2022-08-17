import fs
from fs.multifs import MultiFS

from powersimdata.data_access.ssh_fs import WrapSSHFS
from powersimdata.utility import server_setup


def get_blob_fs(container):
    """Create fs for the given blob storage container

    :param str container: the container name
    :return: (*fs.base.FS*) -- filesystem instance
    """
    account = "esmi"
    sas_token = server_setup.BLOB_TOKEN_RO
    return fs.open_fs(f"azblobv2://{account}:{sas_token}@{container}")


def get_ssh_fs(root=""):
    """Create fs for the given directory on the server

    :param str root: root direcory on server
    :return: (*fs.base.FS*) -- filesystem instance
    """
    host = server_setup.SERVER_ADDRESS
    port = server_setup.SERVER_SSH_PORT
    username = server_setup.get_server_user()
    base_fs = fs.open_fs(f"ssh://{username}@{host}:{port}")
    return WrapSSHFS(base_fs, root)


def get_multi_fs(root):
    """Create filesystem combining the server (if connected) with profile and scenario
    containers in blob storage. The priority is in descending order, so the server will
    be used first if possible

    :param str root: root directory on server
    :return: (*fs.base.FS*) -- filesystem instance
    """
    scenario_data = get_blob_fs("scenariodata")
    profiles = get_blob_fs("profiles")
    mfs = MultiFS()
    try:
        ssh_fs = get_ssh_fs(root)
        mfs.add_fs("ssh_fs", ssh_fs, write=True, priority=3)
    except:  # noqa
        print("Could not connect to ssh server")
    mfs.add_fs("profile_fs", profiles, priority=2)
    mfs.add_fs("scenario_fs", scenario_data, priority=1)
    remotes = ",".join([f[0] for f in mfs.iterate_fs()])
    print(f"Initialized remote filesystem with {remotes}")
    return mfs


def get_scenario_fs():
    """Create filesystem combining the server (if connected) with blob storage,
    prioritizing the server if connected.

    :return: (*fs.base.FS*) -- filesystem instance
    """
    scenario_data = get_blob_fs("scenariodata")
    mfs = MultiFS()
    try:
        ssh_fs = get_ssh_fs(server_setup.DATA_ROOT_DIR)
        mfs.add_fs("ssh_fs", ssh_fs, write=True, priority=2)
    except:  # noqa
        print("Could not connect to ssh server")
    mfs.add_fs("scenario_fs", scenario_data, priority=1)
    remotes = ",".join([f[0] for f in mfs.iterate_fs()])
    print(f"Initialized remote filesystem with {remotes}")
    return mfs
