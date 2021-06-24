import os
import shutil


class MockFilesystem:
    def exists(self, path):
        return os.path.exists(path)

    def makedirs(self, path, exist_ok):
        pass

    def get(self, from_path, to_path):
        shutil.copy(from_path, to_path)

    def put(self, from_path, to_path):
        shutil.copy(from_path, to_path)
