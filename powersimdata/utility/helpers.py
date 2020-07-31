import os
import sys


class PrintManager(object):
    """Manages print messages.

    """

    def __init__(self):
        """Constructor

        """
        self.stdout = sys.stdout

    @staticmethod
    def block_print():
        """Suppresses print

        """
        sys.stdout = open(os.devnull, "w")

    def enable_print(self):
        """Enables print

        """
        sys.stdout = self.stdout
