import os
import posixpath

import paramiko
from tqdm import tqdm

from powersimdata.utility import server_setup


def download(ssh_client, file_name, from_dir, to_dir):
    """Download data from server.

    :param paramiko.client.SSHClient ssh_client: session with an SSH server.
    :param str file_name: file name.
    :param str from_dir: remote directory.
    :param str to_dir: local directory. Will be created if does not exist.
    :raises FileNotFoundError: if file not found on server.
    """
    if not os.path.exists(to_dir):
        os.makedirs(to_dir)

    from_path = posixpath.join(from_dir, file_name)
    stdin, stdout, stderr = ssh_client.exec_command("ls " + from_path)
    if len(stderr.readlines()) != 0:
        raise FileNotFoundError("%s not found in %s on server" % (file_name, from_dir))
    else:
        print("Transferring %s from server" % file_name)
        sftp = ssh_client.open_sftp()
        to_path = os.path.join(to_dir, file_name)
        cbk, bar = progress_bar(ascii=True, unit="b", unit_scale=True)
        sftp.get(from_path, to_path, callback=cbk)
        bar.close()
        sftp.close()


def upload(ssh_client, file_name, from_dir, to_dir, change_name_to=None):
    """Uploads data to server.

    :param paramiko.client.SSHClient ssh_client: session with an SSH server.
    :param str file_name: file name on local machine.
    :param str from_dir: local directory.
    :param str to_dir: remote directory.
    :param str change_name_to: file name on remote machine.
    :raises FileNotFoundError: if file not found on local machine.
    :raises IOError: if file already exists on server.
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
        stdin, stdout, stderr = ssh_client.exec_command("ls " + to_path)
        if len(stderr.readlines()) == 0:
            raise IOError("%s already exists in %s on server" % (file_name, to_dir))
        else:
            print("Transferring %s to server" % file_name)
            sftp = ssh_client.open_sftp()
            sftp.put(from_path, to_path)
            sftp.close()


def setup_server_connection():
    """This function setup the connection to the server.

    :return: (*paramiko.client.SSHClient*) -- session with an SSH server.
    """
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

    return client


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
