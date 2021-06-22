from fsspec.implementations.sftp import SFTPFileSystem
from tqdm import tqdm


class CustomSSHFileSystem(SFTPFileSystem):
    def put(self, lpath, rpath):
        cbk, bar = progress_bar(ascii=True, unit="b", unit_scale=True)
        self.ftp.put(lpath, rpath, callback=cbk)
        bar.close()

    def get(self, rpath, lpath):
        cbk, bar = progress_bar(ascii=True, unit="b", unit_scale=True)
        self.ftp.get(rpath, lpath, callback=cbk)
        bar.close()


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
