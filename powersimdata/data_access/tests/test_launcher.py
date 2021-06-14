import pytest

from powersimdata.data_access.launcher import _check_solver, _check_threads


def test_check_solver():
    _check_solver(None)
    _check_solver("gurobi")
    _check_solver("GLPK")
    with pytest.raises(TypeError):
        _check_solver(123)
    with pytest.raises(ValueError):
        _check_solver("not-a-real-solver")


def test_check_threads():
    _check_threads(None)
    _check_threads(1)
    _check_threads(8)
    with pytest.raises(TypeError):
        _check_threads("4")
    with pytest.raises(ValueError):
        _check_threads(0)
