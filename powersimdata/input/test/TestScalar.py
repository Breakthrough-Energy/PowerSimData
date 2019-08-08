import unittest
from ScalarRefactor import *
from GridMock import *
import numpy as np
import pandas as pd
import copy

class TestScalarMethods(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._gen_types = ['coal', 'dfo', 'geothermal', 'ng', 'nuclear', 'hydro', 'solar', 'wind']
        cls._thermal_gen_types = ['coal', 'dfo', 'geothermal', 'ng', 'nuclear']

    def setUp(self):
        self._original_grid = GridMock(['plant','gencost'])

    def test_typeandlocation_scaling(self):
        baseGrid = GridMock(['plant'])
        self.ct = {'solar': {'zone_id': {1: 2, 3: 3}},'wind':{'zone_id': {2: 5}}}

        newGrid = scale_generators_by_location(self, GridMock(['plant']))

        self.assertEqual(newGrid.plant['GenMWMax'].tolist(),[2*200,5*150,100,300,120],'Scaling was not applied!')

        self.assertEqual(newGrid.plant[['zone_id','Pmin','Pmax']].values.tolist(),\
                         baseGrid.plant[['zone_id','Pmin','Pmax']].values.tolist(),\
                                        'Scaling affected other generator properties!')

    def test_thermal_scaling(self):
        baseGrid = GridMock(['plant','gencost'])
        self.ct = {'coal': {'zone_id': {1: 2, 3: 3}},'ng':{'zone_id': {3: 5}}}

        newGrid = scale_generators_by_location(self, GridMock(['plant','gencost']))

        self.assertEqual(newGrid.plant['GenMWMax'].tolist(),[200,150,5*100,2*300,120],'Scaling was not applied to GenMWMax!')
        self.assertEqual(newGrid.plant['Pmax'].tolist(),[40,80,5*50,2*150,80],'Scaling was not applied to Pmax!')
        self.assertEqual(newGrid.plant['Pmin'].tolist(),[20,30,5*25,2*100,20],'Scaling was not applied!')

        self.assertEqual(newGrid.plant[['zone_id','type']].values.tolist(),\
                         baseGrid.plant[['zone_id','type']].values.tolist(),\
                         'Scaling affected other generator properties!')

        self.assertEqual(newGrid.gencost['c0'].tolist(),[10,20,5*30,2*40,50],'Scaling was not applied!')
        self.assertEqual(newGrid.gencost['c2'].tolist(),[1,2,3/5,4/2,5],'Scaling was not applied!')

    def test_grid_scaling(self):
        baseGrid = GridMock(['plant'])
        self.ct = {'solar': {'zone_id': {1: 2, 3: 3}},'wind':{'zone_id': {2: 5}}}

        newGrid = get_grid(self)

        self.assertEqual(newGrid.plant['GenMWMax'].tolist(),[2*200,5*150,100,300,120],'Scaling was not applied!')

        self.assertEqual(newGrid.plant[['zone_id','Pmin','Pmax']].values.tolist(),\
                         baseGrid.plant[['zone_id','Pmin','Pmax']].values.tolist(),\
                                        'Scaling affected other generator properties!')

    def test_grid_thermal_scaling(self):
        baseGrid = GridMock(['plant','gencost'])
        self.ct = {'coal': {'zone_id': {1: 2, 3: 3}},'ng':{'zone_id': {3: 5}}}

        newGrid = get_grid(self)

        self.assertEqual(newGrid.plant['GenMWMax'].tolist(),[200,150,5*100,2*300,120],'Scaling was not applied to GenMWMax!')
        self.assertEqual(newGrid.plant['Pmax'].tolist(),[40,80,5*50,2*150,80],'Scaling was not applied to Pmax!')
        self.assertEqual(newGrid.plant['Pmin'].tolist(),[20,30,5*25,2*100,20],'Scaling was not applied!')

        self.assertEqual(newGrid.plant[['zone_id','type']].values.tolist(),\
                         baseGrid.plant[['zone_id','type']].values.tolist(),\
                         'Scaling affected other generator properties!')

        self.assertEqual(newGrid.gencost['c0'].tolist(),[10,20,5*30,2*40,50],'Scaling was not applied!')
        self.assertEqual(newGrid.gencost['c2'].tolist(),[1,2,3/5,4/2,5],'Scaling was not applied!')

    def test_branch_scaling(self):
        baseGrid = GridMock(['branch'])
        self.ct = {'branch': {'zone_id': {1: 2, 3: 3}}}

        newGrid = scale_branches_by_location(self, GridMock(['branch']))

        self.assertEqual(newGrid.branch['rateA'].tolist(),[2*10,20,30,40,3*50],'Scaling was not applied to branch rateA field!')
        self.assertEqual(newGrid.branch['x'].tolist(),[0.1/2,0.2,0.3,0.4,0.5/3],'Scaling was not applied to branch x field!')

        self.assertEqual(newGrid.branch[['from_zone_id','to_zone_id','branch_id']].values.tolist(),\
                         baseGrid.branch[['from_zone_id','to_zone_id','branch_id']].values.tolist(),\
                         'Scaling affected other generator properties!')

if __name__ == '__main__':
    unittest.main()