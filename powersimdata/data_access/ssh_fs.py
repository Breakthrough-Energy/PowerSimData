from fsspec.implementations.sftp import SFTPFileSystem
from tqdm import tqdm

from powersimdata.utility.helpers import CommandBuilder


class CustomSSHFileSystem(SFTPFileSystem):
    def put(self, lpath, rpath):
        cbk, bar = progress_bar(ascii=True, unit="b", unit_scale=True)
        self.ftp.put(lpath, rpath, callback=cbk)
        bar.close()

    def get(self, rpath, lpath):
        cbk, bar = progress_bar(ascii=True, unit="b", unit_scale=True)
        self.ftp.get(rpath, lpath, callback=cbk)
        bar.close()

    def cp(self, src, dest, recursive=False):
        """Wrapper around cp command which creates dest path if needed

        :param str src: path to original
        :param str dest: destination path
        :param bool recursive: create directories recursively
        :raises IOError: if command generated stderr
        """
        self.makedirs(dest, exist_ok=True)
        command = CommandBuilder.copy(src, dest, recursive)
        _, _, stderr = self.client.exec_command(command)
        if len(stderr.readlines()) != 0:
            raise IOError(f"Failed to execute {command}")

    def checksum(self, filepath):
        """Return the checksum of the file path (using sha1sum)
        :param str filepath: path to file
        :return: (*str*) -- the checksum of the file
        """
        command = f"sha1sum {filepath}"
        _, stdout, _ = self.client.exec_command(command)
        lines = stdout.readlines()
        return lines[0].strip()


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
