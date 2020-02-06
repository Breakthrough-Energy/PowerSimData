import matlab.engine


def test_default_gurobi_interface():
    eng = matlab.engine.start_matlab()
    eng.TestGurobiDefaultPool() 

def test_specific_gurobi_interface():
    eng = matlab.engine.start_matlab()
    eng.TestGurobiSpecificPool() 