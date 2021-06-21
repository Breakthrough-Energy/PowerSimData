import glob
import operator
import os
import posixpath
import shutil
import time
from subprocess import Popen
from tempfile import mkstemp

import fsspec
import paramiko
from tqdm import tqdm

from powersimdata.data_access.profile_helper import ProfileHelper
from powersimdata.utility import server_setup
from powersimdata.utility.helpers import CommandBuilder

_dirs = {
    "tmp": (server_setup.EXECUTE_DIR,),
    "input": server_setup.INPUT_DIR,
    "output": server_setup.OUTPUT_DIR,
}


class DataAccess:
    """Interface to a local or remote data store."""

    def __init__(self, root=None, backup_root=None):
        """Constructor"""
        self.root = server_setup.DATA_ROOT_DIR if root is None else root
        self.backup_root = (
            server_setup.BACKUP_DATA_ROOT_DIR if backup_root is None else backup_root
        )
        self.join = None

    def copy_from(self, file_name, from_dir):
        """Copy a file from data store to userspace.

        :param str file_name: file name to copy.
        :param str from_dir: data store directory to copy file from.
        """
        raise NotImplementedError

    def move_to(self, file_name, to_dir, change_name_to=None):
        """Copy a file from userspace to data store.

        :param str file_name: file name to copy.
        :param str to_dir: data store directory to copy file to.
        :param str change_name_to: new name for file when copied to data store.
        """
        raise NotImplementedError

    def get_base_dir(self, kind, backup=False):
        """Get path to given kind relative to instance root

        :param str kind: one of {input, output, tmp}
        :param bool backup: pass True if relative to backup root dir
        :raises ValueError: if kind is invalid
        :return: (*str*) -- the specified path
        """
        _allowed = list(_dirs.keys())
        if kind not in _allowed:
            raise ValueError(f"Invalid 'kind', must be one of {_allowed}")

        root = self.root if not backup else self.backup_root
        return self.join(root, *_dirs[kind])

    def match_scenario_files(self, scenario_id, kind, backup=False):
        """Get path matching the given kind of scenario data

        :param int/str scenario_id: the scenario id
        :param str kind: one of {input, output, tmp}
        :param bool backup: pass True if relative to backup root dir
        :return: (*str*) -- the specified path
        """
        base_dir = self.get_base_dir(kind, backup)
        if kind == "tmp":
            return self.join(base_dir, f"scenario_{scenario_id}")
        return self.join(base_dir, f"{scenario_id}_*")

    def copy(self, src, dest, recursive=False, update=False):
        """Wrapper around cp command which creates dest path if needed

        :param str src: path to original
        :param str dest: destination path
        :param bool recursive: create directories recursively
        :param bool update: only copy if needed
        """
        raise NotImplementedError

    def remove(self, target, recursive=False, confirm=True):
        """Wrapper around rm command

        :param str target: path to remove
        :param bool recursive: delete directories recursively
        :param bool confirm: prompt before executing command
        """
        raise NotImplementedError

    def _exists(self, filepath):
        """Return whether the file exists

        :param str filepath: the path to the file
        :return: (*bool*) -- whether the file exists
        """
        raise NotImplementedError

    def _check_file_exists(self, filepath, should_exist=True):
        """Check that file exists (or not) at the given path

        :param str filepath: the full path to the file
        :param bool should_exist: whether the file is expected to exist
        :raises OSError: if the expected condition is not met
        """
        result = self._exists(filepath)
        compare = operator.ne if should_exist else operator.eq
        if compare(result, True):
            msg = "not found" if should_exist else "already exists"
            raise OSError(f"{filepath} {msg} on {self.description}")

    def _check_filename(self, filename):
        """Check that filename is only the name part

        :param str filename: the filename to verify
        :raises ValueError: if filename contains path segments
        """
        if len(os.path.dirname(filename)) != 0:
            raise ValueError(f"Expecting file name but got path {filename}")

    def makedir(self, full_path):
        """Create path, including parents

        :param str full_path: the path, excluding filename
        """
        raise NotImplementedError

    def execute_command_async(self, command):
        """Execute a command locally at the DataAccess, without waiting for completion.

        :param list command: list of str to be passed to command line.
        """
        raise NotImplementedError

    def checksum(self, relative_path):
        """Return the checksum of the file path, and write the content if the
        server is remote

        :param str relative_path: path relative to root
        :return: (*str*) -- the checksum of the file
        """
        raise NotImplementedError

    def push(self, file_name, checksum, change_name_to=None):
        """Push the file from local to remote root folder, ensuring integrity

        :param str file_name: the file name, located at the local root
        :param str checksum: the checksum prior to download
        :param str change_name_to: new name for file when copied to data store.
        """
        raise NotImplementedError

    def get_profile_version(self, grid_model, kind):
        """Returns available raw profile from blob storage

        :param str grid_model: grid model.
        :param str kind: *'demand'*, *'hydro'*, *'solar'* or *'wind'*.
        :return: (*list*) -- available profile version.
        """
        return ProfileHelper.get_profile_version_cloud(grid_model, kind)

    def close(self):
        """Perform any necessary cleanup for the object."""
        pass


class LocalDataAccess(DataAccess):
    """Interface to shared data volume"""

    def __init__(self, root=None):
        super().__init__(root)
        self.description = "local machine"
        self.join = os.path.join

    def copy_from(self, file_name, from_dir=None):
        """Copy a file from data store to userspace.

        :param str file_name: file name to copy.
        :param str from_dir: data store directory to copy file from.
        """
        pass

    def push(self, file_name, checksum, change_name_to=None):
        """Nothing to be done due to symlink

        :param str file_name: the file name, located at the local root
        :param str checksum: the checksum prior to download
        :param str change_name_to: new name for file when copied to data store.
        """
        pass

    def checksum(self, relative_path):
        """Return dummy value since this is only required for remote
        environment

        :param str relative_path: path relative to root
        :return: (*str*) -- the checksum of the file
        """
        return "dummy_value"

    def move_to(self, file_name, to_dir, change_name_to=None):
        """Copy a file from userspace to data store.

        :param str file_name: file name to copy.
        :param str to_dir: data store directory to copy file to.
        :param str change_name_to: new name for file when copied to data store.
        """
        self._check_filename(file_name)
        src = self.join(server_setup.LOCAL_DIR, file_name)
        file_name = file_name if change_name_to is None else change_name_to
        dest = self.join(self.root, to_dir, file_name)
        print(f"--> Moving file {src} to {dest}")
        self._check_file_exists(dest, should_exist=False)
        self.makedir(os.path.dirname(dest))
        shutil.move(src, dest)

    def makedir(self, full_path):
        """Create path on local machine

        :param str full_path: the path, excluding filename
        """
        os.makedirs(full_path, exist_ok=True)

    @staticmethod
    def _fapply(func, pattern):
        files = [f for f in glob.glob(pattern) if os.path.isfile(f)]
        for f in files:
            func(f)

    def copy(self, src, dest, recursive=False, update=False):
        """Wrapper around cp command which creates dest path if needed

        :param str src: path to original
        :param str dest: destination path
        :param bool recursive: create directories recursively
        :param bool update: ignored
        """
        if recursive:
            shutil.copytree(src, dest)
        else:
            self.makedir(dest)
            func = lambda s: shutil.copy(s, dest)  # noqa: E731
            LocalDataAccess._fapply(func, src)

    def remove(self, target, recursive=False, confirm=True):
        """Remove target using rm semantics

        :param str target: path to remove
        :param bool recursive: delete directories recursively
        :param bool confirm: prompt before executing command
        """
        if confirm:
            confirmed = input(f"Delete {target}? [y/n] (default is 'n')")
            if confirmed.lower() != "y":
                print("Operation cancelled.")
                return
        if recursive:
            shutil.rmtree(target)
        else:
            LocalDataAccess._fapply(os.remove, target)
        print("--> Done!")

    def get_profile_version(self, grid_model, kind):
        """Returns available raw profile from blob storage or local disk

        :param str grid_model: grid model.
        :param str kind: *'demand'*, *'hydro'*, *'solar'* or *'wind'*.
        :return: (*list*) -- available profile version.
        """
        blob_version = super().get_profile_version(grid_model, kind)
        local_version = ProfileHelper.get_profile_version_local(grid_model, kind)
        return list(set(blob_version + local_version))

    def _exists(self, filepath):
        """Return whether the file exists

        :param str filepath: the path to the file
        :return: (*bool*) -- whether the file exists
        """
        return os.path.exists(filepath)


class SSHDataAccess(DataAccess):
    """Interface to a remote data store, accessed via SSH."""

    _last_attempt = 0

    def __init__(self, root=None, backup_root=None):
        """Constructor"""
        super().__init__(root, backup_root)
        self._ssh = None
        self._fs = None
        self._retry_after = 5
        self.local_root = server_setup.LOCAL_DIR
        self.description = "server"
        self.join = posixpath.join

    @property
    def sshfs(self):
        """Get or create the filesystem object, with attempts rate limited.

        :raises IOError: if connection failed or still within retry window
        :return: (*fsspec.implementations.sftp.SFTPFileSystem*) -- filesystem instance
        """
        should_attempt = time.time() - SSHDataAccess._last_attempt > self._retry_after

        if self._fs is None:
            if should_attempt:
                try:
                    server_user = server_setup.get_server_user()
                    self._fs = fsspec.filesystem(
                        "ssh", host=server_setup.SERVER_ADDRESS, username=server_user
                    )
                    return self._fs
                except:  # noqa
                    SSHDataAccess._last_attempt = time.time()
            msg = f"Could not connect to server, will try again after {self._retry_after} seconds"
            raise IOError(msg)

        return self._fs

    @property
    def ssh(self):
        """Get or create the ssh connection object, with attempts rate limited.

        :raises IOError: if connection failed or still within retry window
        :return: (*paramiko.SSHClient*) -- the client instance
        """
        should_attempt = time.time() - SSHDataAccess._last_attempt > self._retry_after

        if self._ssh is None:
            if should_attempt:
                try:
                    self._setup_server_connection()
                    return self._ssh
                except:  # noqa
                    SSHDataAccess._last_attempt = time.time()
            msg = f"Could not connect to server, will try again after {self._retry_after} seconds"
            raise IOError(msg)

        return self._ssh

    def _setup_server_connection(self):
        """This function setup the connection to the server."""
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.load_system_host_keys()
        except IOError:
            print("Could not find ssh host keys.")
            ssh_known_hosts = input("Provide ssh known_hosts key file =")
            while True:
                try:
                    client.load_system_host_keys(str(ssh_known_hosts))
                    break
                except IOError:
                    print("Cannot read file, try again")
                    ssh_known_hosts = input("Provide ssh known_hosts key file =")

        server_user = server_setup.get_server_user()
        client.connect(
            server_setup.SERVER_ADDRESS,
            username=server_user,
            port=server_setup.SERVER_SSH_PORT,
            timeout=10,
        )

        self._ssh = client

    def copy_from(self, file_name, from_dir=None):
        """Copy a file from data store to userspace.

        :param str file_name: file name to copy.
        :param str from_dir: data store directory to copy file from.
        """
        self._check_filename(file_name)
        from_dir = "" if from_dir is None else from_dir
        to_dir = os.path.join(self.local_root, from_dir)
        os.makedirs(to_dir, exist_ok=True)

        from_path = self.join(self.root, from_dir, file_name)
        to_path = os.path.join(to_dir, file_name)
        self._check_file_exists(from_path, should_exist=True)

        with self.ssh.open_sftp() as sftp:
            print(f"Transferring {file_name} from server")
            cbk, bar = progress_bar(ascii=True, unit="b", unit_scale=True)
            tmp_file, tmp_path = mkstemp()
            sftp.get(from_path, tmp_path, callback=cbk)
            bar.close()
            os.close(tmp_file)
        # wait for file handle to be available
        shutil.move(tmp_path, to_path)

    def move_to(self, file_name, to_dir=None, change_name_to=None):
        """Copy a file from userspace to data store.

        :param str file_name: file name to copy.
        :param str to_dir: data store directory to copy file to.
        :param str change_name_to: new name for file when copied to data store.
        :raises FileNotFoundError: if specified file does not exist
        """
        self._check_filename(file_name)
        from_path = os.path.join(self.local_root, file_name)

        if not os.path.isfile(from_path):
            raise FileNotFoundError(
                f"{file_name} not found in {self.local_root} on local machine"
            )

        file_name = file_name if change_name_to is None else change_name_to
        to_dir = self.join(self.root, "" if to_dir is None else to_dir)
        to_path = self.join(to_dir, file_name)
        self.makedir(to_dir)
        self._check_file_exists(to_path, should_exist=False)

        with self.ssh.open_sftp() as sftp:
            print(f"Transferring {file_name} to server")
            sftp.put(from_path, to_path)

        os.remove(from_path)

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
        """Return the checksum of the file path (using sha1sum)

        :param str relative_path: path relative to root
        :return: (*str*) -- the checksum of the file
        """
        full_path = self.join(self.root, relative_path)
        self._check_file_exists(full_path)

        command = f"sha1sum {full_path}"
        _, stdout, _ = self.ssh.exec_command(command)
        lines = stdout.readlines()
        return lines[0].strip()

    def push(self, file_name, checksum, change_name_to=None):
        """Push file to server and verify the checksum matches a prior value

        :param str file_name: the file name, located at the local root
        :param str checksum: the checksum prior to download
        :param str change_name_to: new name for file when copied to data store.
        :raises IOError: if command generated stderr
        """
        new_name = file_name if change_name_to is None else change_name_to
        backup = f"{new_name}.temp"
        self.move_to(file_name, change_name_to=backup)

        values = {
            "original": self.join(self.root, new_name),
            "updated": self.join(self.root, backup),
            "lockfile": self.join(self.root, "scenario.lockfile"),
            "checksum": checksum,
        }

        template = "(flock -x 200; \
                prev='{checksum}'; \
                curr=$(sha1sum {original}); \
                if [[ $prev == $curr ]]; then mv {updated} {original} -b; \
                else echo CONFLICT_ERROR 1>&2; fi) \
                200>{lockfile}"

        command = template.format(**values)
        _, _, stderr = self.ssh.exec_command(command)

        errors = stderr.readlines()
        if len(errors) > 0:
            for e in errors:
                print(e)
            raise IOError("Failed to push file - most likely a conflict was detected.")

    def makedir(self, full_path):
        """Create path on server

        :param str full_path: the path, excluding filename
        :raises IOError: if command generated stderr
        """
        _, _, stderr = self.ssh.exec_command(f"mkdir -p {full_path}")
        errors = stderr.readlines()
        if len(errors) > 0:
            raise IOError(f"Failed to create {full_path} on server")

    def copy(self, src, dest, recursive=False, update=False):
        """Wrapper around cp command which creates dest path if needed

        :param str src: path to original
        :param str dest: destination path
        :param bool recursive: create directories recursively
        :param bool update: only copy if needed
        :raises IOError: if command generated stderr
        """
        self.makedir(dest)
        command = CommandBuilder.copy(src, dest, recursive, update)
        _, _, stderr = self.ssh.exec_command(command)
        if len(stderr.readlines()) != 0:
            raise IOError(f"Failed to execute {command}")

    def remove(self, target, recursive=False, confirm=True):
        """Run rm command on server

        :param str target: path to remove
        :param bool recursive: delete directories recursively
        :param bool confirm: prompt before executing command
        :raises IOError: if command generated stderr
        """
        command = CommandBuilder.remove(target, recursive)
        if confirm:
            confirmed = input(f"Execute '{command}'? [y/n] (default is 'n')")
            if confirmed.lower() != "y":
                print("Operation cancelled.")
                return
        _, _, stderr = self.ssh.exec_command(command)
        if len(stderr.readlines()) != 0:
            raise IOError(f"Failed to delete target={target} on server")
        print("--> Done!")

    def _exists(self, filepath):
        """Return whether the file exists

        :param str filepath: the path to the file
        :return: (*bool*) -- whether the file exists
        """
        _, _, stderr = self.ssh.exec_command(f"ls {filepath}")
        return len(stderr.readlines()) == 0

    def close(self):
        """Close the connection if one is open"""
        if self._ssh is not None:
            self._ssh.close()


def progress_bar(*args, **kwargs):
    """Creates progress bar

    :param \\*args: variable length argument list passed to the tqdm constructor.
    :param \\*\\*kwargs: arbitrary keyword arguments passed to the tqdm constructor.
    """
    bar = tqdm(*args, **kwargs)
    last = [0]

    def show(a, b):
        bar.total = int(b)
        bar.update(int(a - last[0]))
        last[0] = a

    return show, bar
