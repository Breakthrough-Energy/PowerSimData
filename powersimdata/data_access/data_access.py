import posixpath
from contextlib import contextmanager
from subprocess import Popen

import fs
from fs import errors
from fs.glob import Globber
from fs.multifs import MultiFS
from fs.path import basename, dirname
from fs.tempfs import TempFS

from powersimdata.data_access.fs_helper import get_blob_fs, get_multi_fs
from powersimdata.utility import server_setup


class DataAccess:
    """Interface to a local or remote data store."""

    def __init__(self):
        """Constructor"""
        self.join = fs.path.join
        self.local_fs = None

    @contextmanager
    def get(self, filepath):
        """Copy file from remote filesystem if needed and read into memory

        :param str filepath: path to file
        :return: (*tuple*) -- file object and filepath to be handled by caller
        """
        if not self.local_fs.exists(filepath):
            print(f"{filepath} not found on local machine")
            from_dir, filename = dirname(filepath), basename(filepath)
            self.copy_from(filename, from_dir)

        with self.local_fs.openbin(filepath) as f:
            filepath = self.local_fs.getsyspath(filepath)
            yield f, filepath

    @contextmanager
    def write(self, filepath, save_local=True):
        """Write a file to data store.

        :param str filepath: path to save data to
        :param bool save_local: whether a copy should also be saved to the local filesystem, if
            such a filesystem is configured. Defaults to True.
        """
        self._check_file_exists(filepath, should_exist=False)

        print("Writing %s" % filepath)
        with fs.open_fs("mem://") as mem_fs:
            mem_fs.makedirs(dirname(filepath), recreate=True)
            with mem_fs.open(filepath, "wb") as f:
                yield f
            self._copy(mem_fs, self.fs, filepath)
            if save_local:
                self._copy(mem_fs, self.local_fs, filepath)

    def _copy(self, src_fs, dst_fs, filepath):
        """Copy file from one filesystem to another.

        :param fs.base.FS src_fs: source filesystem
        :param fs.base.FS dst_fs: destination filesystem
        :param str filepath: path to file
        """
        dst_fs.makedirs(dirname(filepath), recreate=True)
        fs.copy.copy_file(src_fs, filepath, dst_fs, filepath)

    def copy_from(self, file_name, from_dir=None):
        """Copy a file from data store to userspace.

        :param str file_name: file name to copy.
        :param str from_dir: data store directory to copy file from.
        """
        from_dir = "" if from_dir is None else from_dir
        from_path = self.join(from_dir, file_name)
        self._check_file_exists(from_path, should_exist=True)

        location, _ = self.fs.which(from_path)
        print(f"Transferring {file_name} from {location}")
        with TempFS() as tmp_fs:
            self.local_fs.makedirs(from_dir, recreate=True)
            tmp_fs.makedirs(from_dir, recreate=True)
            fs.copy.copy_file(self.fs, from_path, tmp_fs, from_path)
            fs.move.move_file(tmp_fs, from_path, self.local_fs, from_path)

    def tmp_folder(self, scenario_id):
        """Get path to temporary scenario folder

        :param int/str scenario_id: the scenario id
        :return: (*str*) -- the specified path
        """
        return self.join(server_setup.EXECUTE_DIR, f"scenario_{scenario_id}")

    def remove(self, base_dir, pattern, confirm=True):
        """Delete files in current environment

        :param str base_dir: root within which to search
        :param str pattern: glob specifying files to remove
        :param bool confirm: prompt before executing command
        :return: (*bool*) -- True if the operation is completed
        """
        if confirm:
            target = self.join(base_dir, pattern)
            confirmed = input(f"Delete '{target}'? [y/n] (default is 'n')")
            if confirmed.lower() != "y":
                print("Operation cancelled.")
                return False

        for _fs in (self.fs.write_fs, self.local_fs):
            try:
                Globber(_fs.opendir(base_dir), pattern).remove()
            except errors.ResourceNotFound:
                print(f"Skipping {base_dir} not found on {_fs}")
        print("--> Done!")
        return True

    def _check_file_exists(self, path, should_exist=True):
        """Check that file exists (or not) at the given path

        :param str path: the relative path to the file
        :param bool should_exist: whether the file is expected to exist
        :raises OSError: if the expected condition is not met
        """
        location, _ = self.fs.which(path)
        exists = location is not None
        if should_exist and not exists:
            remotes = [f[0] for f in self.fs.iterate_fs()]
            raise OSError(f"{path} not found on any of {remotes}")
        if not should_exist and exists:
            raise OSError(f"{path} already exists on {location}")

    def get_profile_version(self, callback):
        """Returns available raw profile from blob storage or local disk

        :param callable callback: a function taking a fs instance that returns the
            available profiles on that fs
        :return: (*list*) -- available profile version.
        """
        bfs = get_blob_fs("profiles")
        blob_version = callback(bfs)
        local_version = callback(self.local_fs)
        return list(set(blob_version + local_version))

    def checksum(self, relative_path):
        """Return the checksum of the file path

        :param str relative_path: path relative to root
        :return: (*str*) -- the checksum of the file
        """
        return self.fs.hash(relative_path, "sha256")

    def push(self, file_name, checksum):
        """Push the file from local to remote root folder, ensuring integrity

        :param str file_name: the file name, located at the local root
        :param str checksum: the checksum prior to download
        """
        raise NotImplementedError


class LocalDataAccess(DataAccess):
    """Interface to shared data volume"""

    def __init__(self, _fs=None):
        super().__init__()
        self.local_fs = fs.open_fs(server_setup.LOCAL_DIR)
        self.fs = _fs if _fs is not None else self._get_fs()

    def _get_fs(self):
        mfs = MultiFS()
        profiles = get_blob_fs("profiles")
        mfs.add_fs("profile_fs", profiles, priority=2)
        mfs.add_fs("local_fs", self.local_fs, write=True, priority=3)
        return mfs

    @contextmanager
    def push(self, file_name, checksum):
        """Write file if checksum matches

        :param str file_name: the file name, located at the local root
        :param str checksum: the checksum prior to download
        """
        if checksum != self.checksum(file_name):
            raise ValueError("Checksums do not match")
        with fs.open_fs("temp://") as tfs:
            with tfs.openbin(file_name, "w") as f:
                yield f
            fs.move.move_file(tfs, file_name, self.local_fs, file_name)


class SSHDataAccess(DataAccess):
    """Interface to a remote data store, accessed via SSH."""

    def __init__(self, _fs=None):
        """Constructor"""
        super().__init__()
        self.root = server_setup.DATA_ROOT_DIR
        self._fs = _fs
        self.local_fs = fs.open_fs(server_setup.LOCAL_DIR)

    @property
    def fs(self):
        """Get or create a filesystem object, defaulting to a MultiFS that combines the
        server and blob containers.

        :return: (*fs.base.FS*) -- filesystem instance
        """
        if self._fs is None:
            self._fs = get_multi_fs(self.root)
        return self._fs

    def exec_command(self, command):
        ssh_fs = self.fs.get_fs("ssh_fs")
        return ssh_fs.exec_command(command)

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
        ssh_fs = self.fs.get_fs("ssh_fs")
        return ssh_fs.checksum(full_path)

    @contextmanager
    def push(self, file_name, checksum):
        """Push file to server and verify the checksum matches a prior value

        :param str file_name: the file name, located at the local root
        :param str checksum: the checksum prior to download
        :raises IOError: if command generated stderr
        """
        backup = f"{file_name}.temp"

        self._check_file_exists(backup, should_exist=False)
        print(f"Transferring {file_name} to server")
        with fs.open_fs("temp://") as tfs:
            with tfs.openbin(file_name, "w") as f:
                yield f
            fs.move.move_file(tfs, file_name, self.local_fs, file_name)
            fs.copy.copy_file(self.local_fs, file_name, self.fs, backup)

        values = {
            "original": posixpath.join(self.root, file_name),
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
        ssh_fs = self.fs.get_fs("ssh_fs")
        _, _, stderr = ssh_fs.exec_command(command)

        errors = stderr.readlines()
        if len(errors) > 0:
            for e in errors:
                print(e)
            raise IOError("Failed to push file - most likely a conflict was detected.")


class _DataAccessTemplate(SSHDataAccess):
    """Template for data access object using temp or in memory filesystems"""

    def __init__(self, fs_url):
        self.local_fs = fs.open_fs(fs_url)
        self._fs = self._get_fs(fs_url)
        self.root = "foo"
        self.join = fs.path.join

    def _get_fs(self, fs_url):
        mfs = MultiFS()
        mfs.add_fs("remotefs", fs.open_fs(fs_url), write=True, priority=3)
        return mfs

    def checksum(self, relative_path):
        """Return the checksum of the file path

        :param str relative_path: path relative to root
        :return: (*str*) -- the checksum of the file
        """
        return self.fs.hash(relative_path, "sha256")

    @contextmanager
    def push(self, file_name, checksum):
        """Push file from local to remote filesystem, bypassing checksum since this is
        in memory.

        :param str file_name: the file name, located at the local root
        :param str checksum: the checksum prior to download
        """
        with self.local_fs.openbin(file_name, "w") as f:
            yield f
        fs.move.move_file(self.local_fs, file_name, self.fs, file_name)


class TempDataAccess(_DataAccessTemplate):
    """Mimic a client server architecture using temp filesystems"""

    def __init__(self):
        super().__init__("temp://")


class MemoryDataAccess(_DataAccessTemplate):
    """Mimic a client server architecture using in memory filesystems"""

    def __init__(self):
        super().__init__("mem://")
