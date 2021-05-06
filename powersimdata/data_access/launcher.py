import posixpath
import sys

import requests

from powersimdata.utility import server_setup


def _check_threads(threads):
    """Validate threads argument

    :param int threads: the number of threads to be used
    :raises TypeError: if threads is not an int
    :raises ValueError: if threads is not a positive value
    """
    if threads:
        if not isinstance(threads, int):
            raise TypeError("threads must be an int")
        if threads < 1:
            raise ValueError("threads must be a positive value")


def _check_solver(solver):
    """Validate solver argument

    :param str solver: the solver used for the optimization
    :raises ValueError: if invalid solver provided
    """
    solvers = ("gurobi", "glpk")
    if solver is not None and solver.lower() not in solvers:
        raise ValueError(f"Invalid solver: options are {solvers}")


class Launcher:
    def __init__(self, scenario):
        self.scenario = scenario

    def _launch(self, threads=None, solver=None, extract_data=True):
        raise NotImplementedError

    def extract_simulation_output(self):
        """Extracts simulation outputs {PG, PF, LMP, CONGU, CONGL} on server."""
        pass

    def launch_simulation(self, threads=None, solver=None, extract_data=True):
        _check_threads(threads)
        _check_solver(solver)
        return self._launch(threads, solver, extract_data)


class SSHLauncher(Launcher):
    def _run_script(self, script, extra_args=None):
        """Returns running process

        :param str script: script to be used.
        :param list extra_args: list of strings to be passed after scenario id.
        :return: (*subprocess.Popen*) -- process used to run script
        """
        if extra_args is None:
            extra_args = []

        engine = self.scenario._scenario_info["engine"]
        path_to_package = posixpath.join(server_setup.MODEL_DIR, engine)
        folder = "pyreise" if engine == "REISE" else "pyreisejl"

        path_to_script = posixpath.join(path_to_package, folder, "utility", script)
        cmd_pythonpath = [f'export PYTHONPATH="{path_to_package}:$PYTHONPATH";']
        cmd_pythoncall = [
            "nohup",
            "python3",
            "-u",
            path_to_script,
            self.scenario.scenario_id,
        ]
        cmd_io_redirect = ["</dev/null >/dev/null 2>&1 &"]
        cmd = cmd_pythonpath + cmd_pythoncall + extra_args + cmd_io_redirect
        process = self.scenario._data_access.execute_command_async(cmd)
        print("PID: %s" % process.pid)
        return process

    def _launch(self, threads=None, solver=None, extract_data=True):
        """Launch simulation on server, via ssh.

        :param int/None threads: the number of threads to be used. This defaults to None,
            where None means auto.
        :param str solver: the solver used for optimization. This defaults to
            None, which translates to gurobi
        :param bool extract_data: whether the results of the simulation engine should
            automatically extracted after the simulation has run. This defaults to True.
        :raises TypeError: if extract_data is not a boolean
        :return: (*subprocess.Popen*) -- new process used to launch simulation.
        """
        extra_args = []
        if threads is not None:
            # Use the -t flag as defined in call.py in REISE.jl
            extra_args.append("--threads " + str(threads))

        if solver is not None:
            extra_args.append("--solver " + solver)

        if not isinstance(extract_data, bool):
            raise TypeError("extract_data must be a boolean: 'True' or 'False'")
        if extract_data:
            extra_args.append("--extract-data")

        return self._run_script("call.py", extra_args=extra_args)

    def extract_simulation_output(self):
        """Extracts simulation outputs {PG, PF, LMP, CONGU, CONGL} on server.

        :return: (*subprocess.Popen*) -- new process used to extract output
            data.
        """
        print("--> Extracting output data on server")
        return self._run_script("extract_data.py")

    def check_progress(self):
        print("Information is available on the server.")


class HttpLauncher(Launcher):
    def _launch(self, threads=None, solver=None, extract_data=True):
        """Launches simulation in container via http call

        :param int/None threads: the number of threads to be used. This defaults to None,
            where None means auto.
        :param str solver: the solver used for optimization. This defaults to
            None, which translates to gurobi
        :param bool extract_data: always True
        :return: (*requests.Response*) -- http response from the engine, with a json
            body as is returned by check_progress
        """
        scenario_id = self.scenario.scenario_id
        url = f"http://{server_setup.SERVER_ADDRESS}:5000/launch/{scenario_id}"
        resp = requests.post(url, params={"threads": threads, "solver": solver})
        if resp.status_code != 200:
            print(
                f"Failed to launch simulation: status={resp.status_code}. See response for details"
            )
        return resp

    def check_progress(self):
        """Get the status of an ongoing simulation, if possible

        :return: (*dict*) -- contains "output", "errors", "scenario_id", and "status"
            keys which map to stdout, stderr, and the respective scenario attributes
        """
        scenario_id = self.scenario.scenario_id
        url = f"http://{server_setup.SERVER_ADDRESS}:5000/status/{scenario_id}"
        resp = requests.get(url)
        return resp.json()


class NativeLauncher(Launcher):
    def _launch(self, threads=None, solver=None, extract_data=True):
        """Launches simulation by importing from REISE.jl

        :param int/None threads: the number of threads to be used. This defaults to None,
            where None means auto.
        :param str solver: the solver used for optimization. This defaults to
            None, which translates to gurobi
        :param bool extract_data: always True
        :return: (*dict*) -- contains "output", "errors", "scenario_id", and "status"
            keys which map to stdout, stderr, and the respective scenario attributes
        """
        sys.path.append(server_setup.ENGINE_DIR)
        from pyreisejl.utility import app

        return app.launch_simulation(self.scenario.scenario_id, threads, solver)

    def check_progress(self):
        """Get the status of an ongoing simulation, if possible

        :return: (*dict*) -- contains "output", "errors", "scenario_id", and "status"
            keys which map to stdout, stderr, and the respective scenario attributes
        """
        sys.path.append(server_setup.ENGINE_DIR)
        from pyreisejl.utility import app

        return app.check_progress()
