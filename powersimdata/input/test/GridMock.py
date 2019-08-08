import numpy as np
import pandas as pd

class GridMock:
    def __init__(self, fieldNames):
        if 'plant' in fieldNames:
            self.plant = pd.DataFrame( {'type': ['solar','wind','ng','coal','thermal'],\
                                        'zone_id': [1,2,3,1,3],\
                                        'GenMWMax':[200,150,100,300,120],\
                                        'Pmin':    [20,30,25,100,20],\
                                        'Pmax':    [40,80,50,150,80]})

        if 'branch' in fieldNames:
            self.branch = pd.DataFrame({'from_zone_id': [1,2,3,1,3],\
                                        'to_zone_id':   [1,3,2,2,3],\
                                        'branch_id':    [11,12,13,14,15],\
                                        'rateA':        [10,20,30,40,50],\
                                        'x':            [0.1,0.2,0.3,0.4,0.5]})

        if 'dcline' in fieldNames:
            self.dcline = pd.DataFrame({'dcline_id': [101,102,103,104,105],\
                                        'status':    [1,1,1,1,1],\
                                        'Pmax':      [100,200,300,400,500]})
        if 'gencost' in fieldNames:
            self.gencost = pd.DataFrame({'c0': [10,20,30,40,50],\
                                         'c2': [1,2,3,4,5]})