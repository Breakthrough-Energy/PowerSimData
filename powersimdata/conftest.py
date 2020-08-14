import pytest
import os.path
import numpy as np


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    # execute all other hooks to obtain the report object
    outcome = yield
    rep = outcome.get_result()

    # we only look at actual failing test calls, not setup/teardown
    if rep.when == "call" and rep.failed:
        print("Numpy pseudorandom seed information to reproduce failure.")
        print("Pass this output to np.random.set_state()")
        print(np.random.get_state())
