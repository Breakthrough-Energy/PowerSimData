import shutil
from contextlib import contextmanager
from subprocess import PIPE, Popen


class MockConnection:
    @contextmanager
    def open_sftp(self):
        yield self

    def get(self, from_path, to_path, callback=None):
        shutil.copy(from_path, to_path)

    def put(self, from_path, to_path):
        shutil.copy(from_path, to_path)

    def exec_command(self, command):
        print(command)
        proc = Popen(command, shell=True, stderr=PIPE)
        return None, None, proc.stderr

    def close(self):
        pass
