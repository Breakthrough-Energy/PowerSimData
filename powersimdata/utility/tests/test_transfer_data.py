from powersimdata.utility.transfer_data import (setup_server_connection,
                                                get_scenario_table,
                                                get_execute_table)

from getpass import getuser
from numpy.testing import assert_array_equal
import pandas as pd


def test_setup_server_connection():
    ssh_client = setup_server_connection()
    _, stdout, _ = ssh_client.exec_command('whoami')
    assert stdout.read().decode("utf-8").strip() == getuser()
    ssh_client.close()


def test_get_scenario_file_from_server_type():
    ssh_client = setup_server_connection()
    table = get_scenario_table(ssh_client)
    ssh_client.close()
    assert isinstance(table, pd.DataFrame)


def test_get_scenario_file_from_server_header():
    header = ['id',
              'plan',
              'name',
              'state',
              'interconnect',
              'base_demand',
              'base_hydro',
              'base_solar',
              'base_wind',
              'change_table',
              'start_date',
              'end_date',
              'interval',
              'engine',
              'runtime',
              'infeasibilities']
    ssh_client = setup_server_connection()
    table = get_scenario_table(ssh_client)
    ssh_client.close()
    assert_array_equal(table.columns, header)


def test_get_execute_file_from_server_type():
    ssh_client = setup_server_connection()
    table = get_execute_table(ssh_client)
    ssh_client.close()
    assert isinstance(table, pd.DataFrame)


def test_get_execute_file_from_server_header():
    header = ['id',
              'status']
    ssh_client = setup_server_connection()
    table = get_execute_table(ssh_client)
    ssh_client.close()
    assert_array_equal(table.columns, header)
