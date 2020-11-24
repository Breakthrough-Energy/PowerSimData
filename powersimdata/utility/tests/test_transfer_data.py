import pytest

from powersimdata.utility.server_setup import get_server_user
from powersimdata.utility.transfer_data import SSHDataAccess


@pytest.fixture
def data_access():
    data_access = SSHDataAccess()
    yield data_access
    data_access.close()


@pytest.mark.integration
@pytest.mark.ssh
def test_setup_server_connection(data_access):
    _, stdout, _ = data_access.execute_command("whoami")
    assert stdout.read().decode("utf-8").strip() == get_server_user()
