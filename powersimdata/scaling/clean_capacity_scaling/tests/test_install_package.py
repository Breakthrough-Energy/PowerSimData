import unittest
import sys
import subprocess
import os


class MyTestCase(unittest.TestCase):
    @staticmethod
    def test_install_package():
        subprocess.check_call([sys.executable, "-m", "pip", "install", os.path.join("..", "..", "..", ".")])


if __name__ == '__main__':
    unittest.main()
