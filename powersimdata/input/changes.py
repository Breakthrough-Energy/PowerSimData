import pandas as pd


class Change():
    """Enclose changes that need to be applied to the original grid as wll \ 
        as to the original demand, hydro, solar and wind profiles. 

    :param str name: name of scenario.
    """

    def __init__(self, name, interconnect):
        self.name = name

        # Check interconnect exists
        self._check_interconnect(interconnect)

        # Set attribute
        self.interconnect = interconnect

    @staticmethod
    def _check_interconnect(interconnect):
        possible = ['Western', 'TexasWestern', 'USA']
        if interconnect not in possible:
            print("%s is incorrect. Possible interconnect are: %s" % possible)
            raise Exception('Invalid resource(s)')
