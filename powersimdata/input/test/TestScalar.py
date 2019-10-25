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

    def test_grid_nonthermal_scaling(self):
        baseGrid = GridMock(['plant'])
        ct = {'solar': {'zone_id': {1: 2}},'wind':{'zone_id': {2: 5}}}

        newGrid = GridMock(['plant'])
        newGrid = apply_change_table(self, ct, newGrid)

        self.assertEqual(newGrid.plant['GenMWMax'].tolist(),[2*200,5*150,100,300,120],'Scaling was not applied!')

        self.assertEqual(newGrid.plant[['zone_id','Pmin','Pmax']].values.tolist(),\
                         baseGrid.plant[['zone_id','Pmin','Pmax']].values.tolist(),\
                                        'Scaling affected other generator properties!')

    def test_grid_thermal_scaling(self):
        baseGrid = GridMock(['plant','gencost'])
        ct = {'coal': {'zone_id': {1: 2}},'ng':{'zone_id': {3: 5}}}

        newGrid = GridMock(['plant','gencost'])
        newGrid = apply_change_table(self, ct, newGrid)

        self.assertEqual(newGrid.plant['GenMWMax'].tolist(),[200,150,5*100,2*300,120],'Scaling was not applied to GenMWMax!')
        self.assertEqual(newGrid.plant['Pmax'].tolist(),[40,80,5*50,2*150,80],'Scaling was not applied to Pmax!')
        self.assertEqual(newGrid.plant['Pmin'].tolist(),[20,30,5*25,2*100,20],'Scaling was not applied!')

        self.assertEqual(newGrid.plant[['zone_id','type']].values.tolist(),\
                         baseGrid.plant[['zone_id','type']].values.tolist(),\
                         'Scaling affected other generator properties!')

        self.assertEqual(newGrid.gencost['c0'].tolist(),[10,20,5*30,2*40,50],'Scaling was not applied!')
        self.assertEqual(newGrid.gencost['c2'].tolist(),[1,2,3/5,4/2,5],'Scaling was not applied!')

    def test_grid_mixed_generator_scaling(self):
        baseGrid = GridMock(['plant','gencost'])
        ct = {'solar': {'zone_id': {1: 2}},'ng':{'zone_id': {3: 5}}}

        newGrid = GridMock(['plant','gencost'])
        newGrid = apply_change_table(self, ct, newGrid)

        self.assertEqual(newGrid.plant['GenMWMax'].tolist(),[2*200,150,5*100,300,120],'Scaling was not applied to GenMWMax!')
        self.assertEqual(newGrid.plant['Pmax'].tolist(),[40,80,5*50,150,80],'Scaling was not applied to Pmax!')
        self.assertEqual(newGrid.plant['Pmin'].tolist(),[20,30,5*25,100,20],'Scaling was not applied!')

        self.assertEqual(newGrid.plant[['zone_id','type']].values.tolist(),\
                         baseGrid.plant[['zone_id','type']].values.tolist(),\
                         'Scaling affected other generator properties!')

        self.assertEqual(newGrid.gencost['c0'].tolist(),[10,20,5*30,40,50],'Scaling was not applied!')
        self.assertEqual(newGrid.gencost['c2'].tolist(),[1,2,3/5,4,5],'Scaling was not applied!')


    def test_nonthermal_scaling(self):
        baseGrid = GridMock(['plant'])
        ct = {'solar': {'zone_id': {1: 2}},'wind':{'zone_id': {2: 5}}}

        newGrid = GridMock(['plant'])
        newGrid = scale_location_by_gentype(ct, newGrid, 'solar', scale_GenMWMax)
        newGrid = scale_location_by_gentype(ct, newGrid, 'wind', scale_GenMWMax)

        self.assertEqual(newGrid.plant['GenMWMax'].tolist(),[2*200,5*150,100,300,120],'Scaling was not applied!')

        self.assertEqual(newGrid.plant[['zone_id','Pmin','Pmax']].values.tolist(),\
                         baseGrid.plant[['zone_id','Pmin','Pmax']].values.tolist(),\
                                        'Scaling affected other generator properties!')

    def test_thermal_scaling(self):
        baseGrid = GridMock(['plant','gencost'])
        ct = {'coal': {'zone_id': {1: 2}},'ng':{'zone_id': {3: 5}}}

        newGrid = GridMock(['plant','gencost'])

        newGrid = scale_location_by_gentype(ct, newGrid, 'coal', scale_GenMWMax)
        newGrid = scale_location_by_gentype(ct, newGrid, 'coal', scale_Thermal)
       
        newGrid = scale_location_by_gentype(ct, newGrid, 'ng', scale_GenMWMax)
        newGrid = scale_location_by_gentype(ct, newGrid, 'ng', scale_Thermal)

        self.assertEqual(newGrid.plant['GenMWMax'].tolist(),[200,150,5*100,2*300,120],'Scaling was not applied to GenMWMax!')
        self.assertEqual(newGrid.plant['Pmax'].tolist(),[40,80,5*50,2*150,80],'Scaling was not applied to Pmax!')
        self.assertEqual(newGrid.plant['Pmin'].tolist(),[20,30,5*25,2*100,20],'Scaling was not applied!')

        self.assertEqual(newGrid.plant[['zone_id','type']].values.tolist(),\
                         baseGrid.plant[['zone_id','type']].values.tolist(),\
                         'Scaling affected other generator properties!')

        self.assertEqual(newGrid.gencost['c0'].tolist(),[10,20,5*30,2*40,50],'Scaling was not applied!')
        self.assertEqual(newGrid.gencost['c2'].tolist(),[1,2,3/5,4/2,5],'Scaling was not applied!')

    def test_mixed_generator_scaling(self):
        baseGrid = GridMock(['plant','gencost'])
        ct = {'solar': {'zone_id': {1: 2}},'ng':{'zone_id': {3: 5}}}

        newGrid = GridMock(['plant','gencost'])

        newGrid = scale_location_by_gentype(ct, newGrid, 'solar', scale_GenMWMax)
        newGrid = scale_location_by_gentype(ct, newGrid, 'ng', scale_GenMWMax)
        newGrid = scale_location_by_gentype(ct, newGrid, 'ng', scale_Thermal)

        self.assertEqual(newGrid.plant['GenMWMax'].tolist(),[2*200,150,5*100,300,120],'Scaling was not applied to GenMWMax!')
        self.assertEqual(newGrid.plant['Pmax'].tolist(),[40,80,5*50,150,80],'Scaling was not applied to Pmax!')
        self.assertEqual(newGrid.plant['Pmin'].tolist(),[20,30,5*25,100,20],'Scaling was not applied!')

        self.assertEqual(newGrid.plant[['zone_id','type']].values.tolist(),\
                         baseGrid.plant[['zone_id','type']].values.tolist(),\
                         'Scaling affected other generator properties!')

        self.assertEqual(newGrid.gencost['c0'].tolist(),[10,20,5*30,40,50],'Scaling was not applied!')
        self.assertEqual(newGrid.gencost['c2'].tolist(),[1,2,3/5,4,5],'Scaling was not applied!')

    def test_branch_scaling(self):
        baseGrid = GridMock(['branch'])
        ct = {'branch': {'zone_id': {1: 2, 3: 3}}}

        newGrid = scale_branches_by_location(ct, GridMock(['branch']), scale_Branch)

        self.assertEqual(newGrid.branch['rateA'].tolist(),[2*10,20,30,40,3*50],'Scaling was not applied to branch rateA field!')
        self.assertEqual(newGrid.branch['x'].tolist(),[0.1/2,0.2,0.3,0.4,0.5/3],'Scaling was not applied to branch x field!')

        self.assertEqual(newGrid.branch[['from_zone_id','to_zone_id']].values.tolist(),\
                         baseGrid.branch[['from_zone_id','to_zone_id']].values.tolist(),\
                         'Scaling affected other generator properties!')

    def test_genId_nonThermal_scaling(self):
        baseGrid = GridMock(['plant'])
        ct = {'solar': {'plant_id': {101: 7, 102: 3}}}

        newGrid = GridMock(['plant'])
        newGrid = scale_generators_by_id(ct, newGrid, 'solar', scale_GenMWMax)

        self.assertEqual(newGrid.plant['GenMWMax'].tolist(),[7*200,3*150,100,300,120],'Scaling was not applied!')

        self.assertEqual(newGrid.plant[['zone_id','Pmin','Pmax']].values.tolist(),\
                         baseGrid.plant[['zone_id','Pmin','Pmax']].values.tolist(),\
                                        'Scaling affected other generator properties!')

    def test_genId_thermal_scaling(self):
        baseGrid = GridMock(['plant','gencost'])
        ct = {'ng': {'plant_id': {103: 5, 104: 6, 105: 8}}}

        newGrid = GridMock(['plant','gencost'])

        newGrid = scale_generators_by_id(ct, newGrid, 'ng', scale_GenMWMax)
        newGrid = scale_generators_by_id(ct, newGrid, 'ng', scale_Thermal)

        self.assertEqual(newGrid.plant['GenMWMax'].tolist(),[200,150,5*100,6*300,8*120],'Scaling was not applied!')
        self.assertEqual(newGrid.plant['Pmax'].tolist(),[40,80,5*50,6*150,8*80],'Scaling was not applied to Pmax!')
        self.assertEqual(newGrid.plant['Pmin'].tolist(),[20,30,5*25,6*100,8*20],'Scaling was not applied!')

        self.assertEqual(newGrid.plant[['zone_id','type']].values.tolist(),\
                         baseGrid.plant[['zone_id','type']].values.tolist(),\
                         'Scaling affected other generator properties!')

        self.assertEqual(newGrid.gencost['c0'].tolist(),[10,20,5*30,6*40,8*50],'Scaling was not applied!')
        self.assertEqual(newGrid.gencost['c2'].tolist(),[1,2,3/5,4/6,5/8],'Scaling was not applied!')

if __name__ == '__main__':
    unittest.main()