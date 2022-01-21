import os
import pickle
import posixpath
import time
from subprocess import Popen

import fs as fs2
import pandas as pd
from fs.multifs import MultiFS
from fs.tempfs import TempFS
from scipy.io import savemat

from powersimdata.data_access.profile_helper import (
    get_profile_version_cloud,
    get_profile_version_local,
)
from powersimdata.data_access.ssh_fs import WrapSSHFS
from powersimdata.utility import server_setup


def get_blob_fs(container):
    account = "besciences"
    return fs2.open_fs(f"azblob://{account}@{container}")


def get_ssh_fs(root=""):
    host = server_setup.SERVER_ADDRESS
    port = server_setup.SERVER_SSH_PORT
    username = server_setup.get_server_user()
    base_fs = fs2.open_fs(f"ssh://{username}@{host}:{port}")
    return WrapSSHFS(base_fs, root)


def get_multi_fs(root):
    scenario_data = get_blob_fs("scenariodata")
    profiles = get_blob_fs("profiles")
    ssh_fs = get_ssh_fs(root)
    mfs = MultiFS()
    mfs.add_fs("ssh_fs", ssh_fs, write=True, priority=1)
    mfs.add_fs("profile_fs", profiles, priority=2)
    mfs.add_fs("scenario_fs", scenario_data, priority=3)
    return mfs


class DataAccess:
    """Interface to a local or remote data store."""

    def __init__(self, root):
        """Constructor"""
        self.root = root
        self.join = fs2.path.join
        self.local_fs = None

    def read(self, filepath):
        """Reads data from data store.

        :param str filepath: path to file, with extension either 'pkl', 'csv', or 'mat'.
        :return: (*pandas.DataFrame* or *dict*) -- pkl and csv files will be returned as
            a data frame, while a mat file will be returned as a dictionary
        :raises ValueError: if extension is unknown.
        """

        if self.local_fs.exists(filepath):
            return self._read(self.local_fs, filepath)
        return self._read(self.fs, filepath)

    def _read(self, fs, filepath):
        ext = os.path.basename(filepath).split(".")[-1]
        with fs.open(filepath, mode="rb") as file_object:
            if ext == "pkl":
                data = pd.read_pickle(file_object)
            elif ext == "csv":
                data = pd.read_csv(file_object, index_col=0, parse_dates=True)
            elif ext == "mat":
                # Try to load the matfile, just to check if it exists locally
                open(filepath, "r")
                data = filepath
            else:
                raise ValueError("Unknown extension! %s" % ext)

        return data

    def write(self, filepath, data, save_local=True):
        """Write a file to data store.

        :param str filepath: path to save data to, with extension either 'pkl', 'csv', or 'mat'.
        :param (*pandas.DataFrame* or *dict*) data: data to save
        :param bool save_local: whether a copy should also be saved to the local filesystem, if
            such a filesystem is configured. Defaults to True.
        """
        self._check_file_exists(filepath, should_exist=False)
        print("Writing %s" % filepath)
        self._write(self.fs, filepath, data)

        if save_local and self.local_fs is not None:
            self._write(self.local_fs, filepath, data)

    def _write(self, fs, filepath, data):
        """Write a file to given data store.

        :param fs fs: pyfilesystem to which to write data
        :param str filepath: path to save data to, with extension either 'pkl', 'csv', or 'mat'.
        :param (*pandas.DataFrame* or *dict*) data: data to save
        :raises ValueError: if extension is unknown.
        """
        ext = os.path.basename(filepath).split(".")[-1]
        dirpath = fs2.path.dirname(filepath)
        fs.makedirs(dirpath, recreate=True)

        with fs.openbin(filepath, "w") as f:
            if ext == "pkl":
                pickle.dump(data, f)
            elif ext == "csv":
                data.to_csv(f)
            elif ext == "mat":
                savemat(f, data, appendmat=False)
            else:
                raise ValueError("Unknown extension! %s" % ext)

    def copy_from(self, file_name, from_dir):
        """Copy a file from data store to userspace.

        :param str file_name: file name to copy.
        :param str from_dir: data store directory to copy file from.
        """
        raise NotImplementedError

    def tmp_folder(self, scenario_id):
        """Get path to temporary scenario folder

        :param int/str scenario_id: the scenario id
        :return: (*str*) -- the specified path
        """
        return self.join(server_setup.EXECUTE_DIR, f"scenario_{scenario_id}")

    def copy(self, src, dest):
        """Copy file to new location

        :param str src: path to file
        :param str dest: destination folder
        """
        if self.fs.isdir(dest):
            dest = self.join(dest, fs2.path.basename(src))

        self.fs.copy(src, dest)

    def remove(self, pattern, confirm=True):
        """Delete files in current environment

        :param str pattern: glob specifying files to remove
        :param bool confirm: prompt before executing command
        """
        if confirm:
            confirmed = input(f"Delete '{pattern}'? [y/n] (default is 'n')")
            if confirmed.lower() != "y":
                print("Operation cancelled.")
                return
        self.fs.glob(pattern).remove()
        print("--> Done!")

    def _check_file_exists(self, path, should_exist=True):
        """Check that file exists (or not) at the given path

        :param str path: the relative path to the file
        :param bool should_exist: whether the file is expected to exist
        :raises OSError: if the expected condition is not met
        """
        exists = self.fs.exists(path)
        if should_exist and not exists:
            raise OSError(f"{path} not found on {self.description}")
        if not should_exist and exists:
            raise OSError(f"{path} already exists on {self.description}")

    def execute_command_async(self, command):
        """Execute a command locally at the DataAccess, without waiting for completion.

        :param list command: list of str to be passed to command line.
        """
        raise NotImplementedError

    def checksum(self, relative_path):
        """Return the checksum of the file path

        :param str relative_path: path relative to root
        :return: (*str*) -- the checksum of the file
        """
        return self.fs.hash(relative_path, "sha256")

    def push(self, file_name, checksum, rename):
        """Push the file from local to remote root folder, ensuring integrity

        :param str file_name: the file name, located at the local root
        :param str checksum: the checksum prior to download
        :param str rename: the new filename
        """
        raise NotImplementedError

    def get_profile_version(self, grid_model, kind):
        """Returns available raw profile from blob storage

        :param str grid_model: grid model.
        :param str kind: *'demand'*, *'hydro'*, *'solar'* or *'wind'*.
        :return: (*list*) -- available profile version.
        """
        blob_version = get_profile_version_cloud(grid_model, kind)
        local_version = get_profile_version_local(grid_model, kind)
        return list(set(blob_version + local_version))


class LocalDataAccess(DataAccess):
    """Interface to shared data volume"""

    def __init__(self, root=server_setup.LOCAL_DIR):
        super().__init__(root)
        self.description = "local machine"
        self.fs = fs2.open_fs(root)
        self.local_fs = self.fs

    def copy_from(self, file_name, from_dir=None):
        """Copy a file from data store to userspace.

        :param str file_name: file name to copy.
        :param str from_dir: data store directory to copy file from.
        """
        pass

    def push(self, file_name, checksum, rename):
        """Rename the file.

        :param str file_name: the file name, located at the local root
        :param str checksum: the checksum prior to download
        :param str rename: the new filename
        """
        if checksum != self.checksum(rename):
            raise ValueError("Checksums do not match")
        self.fs.move(file_name, rename, overwrite=True)


class SSHDataAccess(DataAccess):
    """Interface to a remote data store, accessed via SSH."""

    _last_attempt = 0

    def __init__(self, root=server_setup.DATA_ROOT_DIR):
        """Constructor"""
        super().__init__(root)
        self._fs = None
        self._retry_after = 5
        self.local_root = server_setup.LOCAL_DIR
        self.local_fs = fs2.open_fs(self.local_root)
        self.description = "server"

    @property
    def fs(self):
        """Get or create the filesystem object, with attempts rate limited.

        :raises IOError: if connection failed or still within retry window
        :return: (*fs.multifs.MultiFS*) -- filesystem instance
        """
        if self._fs is None:
            should_attempt = (
                time.time() - SSHDataAccess._last_attempt > self._retry_after
            )
            if should_attempt:
                try:
                    self._fs = get_multi_fs(self.root)
                    return self._fs
                except:  # noqa
                    SSHDataAccess._last_attempt = time.time()
            msg = f"Could not connect to server, will try again after {self._retry_after} seconds"
            raise IOError(msg)

        return self._fs

    def copy_from(self, file_name, from_dir=None):
        """Copy a file from data store to userspace.

        :param str file_name: file name to copy.
        :param str from_dir: data store directory to copy file from.
        """
        from_dir = "" if from_dir is None else from_dir
        from_path = self.join(from_dir, file_name)
        self._check_file_exists(from_path, should_exist=True)

        print(f"Transferring {file_name} from server")
        with TempFS() as tmp_fs:
            self.local_fs.makedirs(from_dir, recreate=True)
            tmp_fs.makedirs(from_dir, recreate=True)
            fs2.copy.copy_file(self.fs, from_path, tmp_fs, from_path)
            fs2.move.move_file(tmp_fs, from_path, self.local_fs, from_path)

    def execute_command_async(self, command):
        """Execute a command via ssh, without waiting for completion.

        :param list command: list of str to be passed to command line.
        :return: (*subprocess.Popen*) -- the local ssh process
        """
        username = server_setup.get_server_user()
        cmd_ssh = ["ssh", username + "@" + server_setup.SERVER_ADDRESS]
        full_command = cmd_ssh + command
        process = Popen(full_command)
        return process

    def checksum(self, relative_path):
        """Return the checksum of the file path

        :param str relative_path: path relative to root
        :return: (*str*) -- the checksum of the file
        """
        self._check_file_exists(relative_path)
        full_path = self.join(self.root, relative_path)
        return self.fs.checksum(full_path)

    def push(self, file_name, checksum, rename):
        """Push file to server and verify the checksum matches a prior value

        :param str file_name: the file name, located at the local root
        :param str checksum: the checksum prior to download
        :param str rename: the new filename
        :raises IOError: if command generated stderr
        """
        backup = f"{rename}.temp"

        self._check_file_exists(backup, should_exist=False)
        print(f"Transferring {rename} to server")
        fs2.move.move_file(self.local_fs, file_name, self.fs, backup)

        values = {
            "original": posixpath.join(self.root, rename),
            "updated": posixpath.join(self.root, backup),
            "lockfile": posixpath.join(self.root, "scenario.lockfile"),
            "checksum": checksum,
        }

        template = "(flock -x 200; \
                prev='{checksum}'; \
                curr=$(sha1sum {original}); \
                if [[ $prev == $curr ]]; then mv {updated} {original} -b; \
                else echo CONFLICT_ERROR 1>&2; fi) \
                200>{lockfile}"

        command = template.format(**values)
        _, _, stderr = self.fs.exec_command(command)

        errors = stderr.readlines()
        if len(errors) > 0:
            for e in errors:
                print(e)
            raise IOError("Failed to push file - most likely a conflict was detected.")


class MemoryDataAccess(SSHDataAccess):
    """Mimic a client server architecture using in memory filesystems"""

    def __init__(self):
        self.local_fs = fs2.open_fs("mem://")
        self._fs = fs2.open_fs("mem://")
        self.description = "in-memory"
        self.local_root = self.root = "dummy"
        self.join = fs2.path.join

    def push(self, file_name, checksum, rename):
        """Push file from local to remote filesystem, bypassing checksum since this is
        in memory.

        :param str file_name: the file name, located at the local root
        :param str checksum: the checksum prior to download
        :param str rename: the new filename
        """
        fs2.move.move_file(self.local_fs, file_name, self.fs, rename)
