import fs as fs2
import pytest

from powersimdata.data_access.data_access import MemoryDataAccess, SSHDataAccess
from powersimdata.utility import server_setup

FILE_NAME = "test.txt"
CONTENT = b"content"


@pytest.fixture
def ssh_data_access():
    return SSHDataAccess()


@pytest.fixture
def data_access():
    return MemoryDataAccess()


def make_temp(fs, path):
    fs.makedirs(fs2.path.dirname(path), recreate=True)
    with fs.open(path, "wb") as f:
        f.write(CONTENT)


def _check_content(fs, filepath):
    assert fs.exists(filepath), f"File {filepath} not found"
    with fs.open(filepath, "rb") as f:
        assert CONTENT == f.read(), f"File {filepath} content does not match expected"


def _join(*paths):
    return fs2.path.join(*paths)


def test_tmp_folder(ssh_data_access):
    tmp_files = ssh_data_access.tmp_folder(42)
    assert "tmp/scenario_42" == tmp_files


@pytest.mark.integration
@pytest.mark.ssh
def test_setup_server_connection(ssh_data_access):
    _, stdout, _ = ssh_data_access.fs.exec_command("whoami")
    assert stdout.read().decode("utf-8").strip() == server_setup.get_server_user()


def test_copy_from(data_access):
    make_temp(data_access.fs, FILE_NAME)
    data_access.copy_from(FILE_NAME)
    _check_content(data_access.local_fs, FILE_NAME)


def test_copy_from_multi_path(data_access):
    src_path = _join(data_access.root, "foo", "bar")
    filepath = _join(src_path, FILE_NAME)
    make_temp(data_access.fs, filepath)
    data_access.copy_from(FILE_NAME, src_path)
    _check_content(data_access.local_fs, filepath)


def test_move_to(data_access):
    make_temp(data_access.local_fs, FILE_NAME)
    data_access.move_to(FILE_NAME)
    _check_content(data_access.fs, FILE_NAME)


def test_move_to_multi_path(data_access):
    rel_path = _join(data_access.local_root, "foo", "bar")
    filepath = _join(rel_path, FILE_NAME)
    make_temp(data_access.local_fs, FILE_NAME)
    data_access.move_to(FILE_NAME, rel_path)
    _check_content(data_access.fs, filepath)


def test_move_to_rename(data_access):
    make_temp(data_access.local_fs, FILE_NAME)

    new_fname = "foo.txt"
    data_access.move_to(FILE_NAME, change_name_to=new_fname)
    _check_content(data_access.fs, new_fname)
