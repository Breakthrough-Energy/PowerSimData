import os
import shutil
from subprocess import PIPE, Popen


class MockFilesystem:
    def exists(self, path):
        return os.path.exists(path)

    def makedirs(self, path, exist_ok):
        pass

    def get(self, from_path, to_path):
        shutil.copy(from_path, to_path)

    def put(self, from_path, to_path):
        shutil.copy(from_path, to_path)


class MockConnection:
    def exec_command(self, command):
        print(command)
        proc = Popen(command, shell=True, stderr=PIPE)
        return None, None, proc.stderr

    def close(self):
        pass
