import fs
from fs.multifs import MultiFS

from powersimdata.data_access.ssh_fs import WrapSSHFS
from powersimdata.utility import server_setup


def get_blob_fs(container):
    """Create fs for the given blob storage container

    :param str container: the container name
    :return: (*fs.base.FS*) -- filesystem instance
    """
    account = "besciences"
    return fs.open_fs(f"azblob://{account}@{container}")


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


def get_profile_version(_fs, grid_model, kind):
    """Returns available raw profile from the given filesystem

    :param fs.base.FS _fs: filesystem instance
    :param str grid_model: grid model.
    :param str kind: *'demand'*, *'hydro'*, *'solar'*, *'wind'*,
        *'demand_flexibility_up'*, *'demand_flexibility_dn'*,
        *'demand_flexibility_cost_up'*, or *'demand_flexibility_cost_dn'*.
    :return: (*list*) -- available profile version.
    """
    _fs = _fs.makedirs(f"raw/{grid_model}", recreate=True)
    matching = [f for f in _fs.listdir(".") if kind in f]

    # Don't include demand flexibility profiles as possible demand profiles
    if kind == "demand":
        matching = [p for p in matching if "demand_flexibility" not in p]
    return [f.lstrip(f"{kind}_").rstrip(".csv") for f in matching]
