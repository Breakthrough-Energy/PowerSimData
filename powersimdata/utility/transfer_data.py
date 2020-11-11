import glob
import os
import posixpath
from subprocess import Popen

import paramiko
from tqdm import tqdm

from powersimdata.utility import server_setup


class DataAccess:
    """Interface to a local or remote data store."""

    def copy_from(self, file_name, from_dir, to_dir):
        """Copy a file from data store to userspace.

        :param str file_name: file name to copy.
        :param str from_dir: data store directory to copy file from.
        :param str to_dir: userspace directory to copy file to.
        """
        raise NotImplementedError

    def copy_to(self, file_name, from_dir, to_dir, change_name_to=None):
        """Copy a file from userspace to data store.

        :param str file_name: file name to copy.
        :param str from_dir: userspace directory to copy file from.
        :param str to_dir: data store directory to copy file to.
        :param str change_name_to: new name for file when copied to data store.
        """
        raise NotImplementedError

    def execute_command(self, command):
        """Execute a command locally at the data access.

        :param list command: list of str to be passed to command line.
        """
        raise NotImplementedError

    def execute_command_async(self, command):
        """Execute a command locally at the DataAccess, without waiting for completion.

        :param list command: list of str to be passed to command line.
        """
        raise NotImplementedError

    def close(self):
        """Perform any necessary cleanup for the object."""
        pass

    def clear_local_cache(self):
        """Clear the local cache folder."""
        cached_files = glob.glob(os.path.join(server_setup.LOCAL_DIR, "*"))
        for f in cached_files:
            os.remove(f)


class SSHDataAccess(DataAccess):
    """Interface to a remote data store, accessed via SSH."""

    def __init__(self):
        """Constructor"""
        self._setup_server_connection()

    def _setup_server_connection(self):
        """This function setup the connection to the server."""
        client = paramiko.SSHClient()
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
        client.connect(server_setup.SERVER_ADDRESS, username=server_user, timeout=60)

        self.ssh = client

    def copy_from(self, file_name, from_dir, to_dir):
        """Copy a file from data store to userspace.

        :param str file_name: file name to copy.
        :param str from_dir: data store directory to copy file from.
        :param str to_dir: userspace directory to copy file to.
        """
        if not os.path.exists(to_dir):
            os.makedirs(to_dir)

        from_path = posixpath.join(from_dir, file_name)
        stdin, stdout, stderr = self.ssh.exec_command("ls " + from_path)
        if len(stderr.readlines()) != 0:
            raise FileNotFoundError(f"{file_name} not found in {from_dir} on server")
        else:
            print("Transferring %s from server" % file_name)
            to_path = os.path.join(to_dir, file_name)
            sftp = self.ssh.open_sftp()
            try:
                cbk, bar = progress_bar(ascii=True, unit="b", unit_scale=True)
                sftp.get(from_path, to_path, callback=cbk)
            finally:
                sftp.close()
                bar.close()

    def copy_to(self, file_name, from_dir, to_dir, change_name_to=None):
        """Copy a file from userspace to data store.

        :param str file_name: file name to copy.
        :param str from_dir: userspace directory to copy file from.
        :param str to_dir: data store directory to copy file to.
        :param str change_name_to: new name for file when copied to data store.
        """
        from_path = os.path.join(from_dir, file_name)

        if os.path.isfile(from_path) is False:
            raise FileNotFoundError(
                "%s not found in %s on local machine" % (file_name, from_dir)
            )
        else:
            if bool(change_name_to):
                to_path = posixpath.join(to_dir, change_name_to)
            else:
                to_path = posixpath.join(to_dir, file_name)
            stdin, stdout, stderr = self.ssh.exec_command("ls " + to_path)
            if len(stderr.readlines()) == 0:
                raise IOError("%s already exists in %s on server" % (file_name, to_dir))
            else:
                print("Transferring %s to server" % file_name)
                sftp = self.ssh.open_sftp()
                try:
                    sftp.put(from_path, to_path)
                finally:
                    sftp.close()

    def execute_command(self, command):
        """Execute a command locally at the data access.

        :param list command: list of str to be passed to command line.
        :return: (*tuple*) -- stdin, stdout, stderr of executed command.
        """
        return self.ssh.exec_command(command)

    def execute_command_async(self, command):
        """Execute a command via ssh, without waiting for completion.

        :param list command: list of str to be passed to command line.
        """
        username = server_setup.get_server_user()
        cmd_ssh = ["ssh", username + "@" + server_setup.SERVER_ADDRESS]
        full_command = cmd_ssh + command
        process = Popen(full_command)
        return process

    def close(self):
        """Close the connection that was opened when the object was created."""
        self.ssh.close()


def progress_bar(*args, **kwargs):
    """Creates progress bar

    :param args: variable length argument list passed to the tqdm constructor.
    :param kwargs: arbitrary keyword arguments passed to the tqdm constructor.
    """
    bar = tqdm(*args, **kwargs)
    last = [0]

    def show(a, b):
        bar.total = int(b)
        bar.update(int(a - last[0]))
        last[0] = a

    return show, bar
