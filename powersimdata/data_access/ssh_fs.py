from fs.subfs import SubFS
from tqdm import tqdm


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


class WrapSSHFS(SubFS):
    """Wrapper around another filesystem which is rooted at the given path and adds
    progress bar for download

    :param fs.base.FS parent_fs: the filesystem instance to wrap
    :param str path: the path which will be the root of the wrapped filesystem
    """

    def __init__(self, parent_fs, path):
        self.client = parent_fs._client
        super().__init__(parent_fs, path)

    def download(self, path, file, chunk_size=None, **options):
        """Wrapper around pyfilesystem download with progress bar"""

        cbk, bar = progress_bar(ascii=True, unit="b", unit_scale=True)
        super().download(path, file, chunk_size=chunk_size, callback=cbk, **options)
        bar.close()

    def exec_command(self, command):
        """Wrapper around paramiko exec_command

        :param str command: the command to execute
        :return: (*tuple*) -- standard streams
        """
        return self.client.exec_command(command)

    def checksum(self, filepath):
        """Return the checksum of the file path (using sha1sum)

        :param str filepath: path to file
        :return: (*str*) -- the checksum of the file
        """
        command = f"sha1sum {filepath}"
        _, stdout, _ = self.exec_command(command)
        lines = stdout.readlines()
        return lines[0].strip()
