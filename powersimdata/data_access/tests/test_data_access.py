import fs as fs2
import pytest

from powersimdata.data_access.data_access import SSHDataAccess
from powersimdata.utility import server_setup

FILE_NAME = "test.txt"
CONTENT = b"content"


@pytest.fixture
def data_access():
    return SSHDataAccess()


def mem_fs():
    return fs2.open_fs("mem://")


def make_temp(fs, path):
    fs.makedirs(fs2.path.dirname(path), recreate=True)
    fs.touch(path)
    with fs.open(path, "wb") as f:
        f.write(CONTENT)


@pytest.fixture
def mock_data_access():
    with mem_fs() as fs1, mem_fs() as fs2:
        data_access = SSHDataAccess()
        data_access._fs = fs1
        data_access.local_fs = fs2
        data_access.root = "/"
        data_access.local_root = "/"
        yield data_access


def _check_content(fs, filepath):
    assert fs.exists(filepath)
    with fs.open(filepath, "rb") as f:
        assert CONTENT == f.read()


def _join(*paths):
    return fs2.path.join(*paths)


def test_match_scenario_files(data_access):
    output_files = data_access.match_scenario_files(99, "output")
    assert "data/output/99_*" == output_files

    tmp_files = data_access.match_scenario_files(42, "tmp")
    assert "tmp/scenario_42" == tmp_files


@pytest.mark.integration
@pytest.mark.ssh
def test_setup_server_connection(data_access):
    _, stdout, _ = data_access.ssh.exec_command("whoami")
    assert stdout.read().decode("utf-8").strip() == server_setup.get_server_user()


def test_copy_from(mock_data_access):
    make_temp(mock_data_access.fs, FILE_NAME)
    mock_data_access.copy_from(FILE_NAME)
    _check_content(mock_data_access.local_fs, FILE_NAME)


def test_copy_from_multi_path(mock_data_access):
    src_path = _join(mock_data_access.root, "foo", "bar")
    filepath = _join(src_path, FILE_NAME)
    make_temp(mock_data_access.fs, filepath)
    mock_data_access.copy_from(FILE_NAME, src_path)
    _check_content(mock_data_access.local_fs, filepath)


def test_move_to(mock_data_access):
    make_temp(mock_data_access.local_fs, FILE_NAME)
    mock_data_access.move_to(FILE_NAME)
    _check_content(mock_data_access.fs, FILE_NAME)


def test_move_to_multi_path(mock_data_access):
    rel_path = _join(mock_data_access.local_root, "foo", "bar")
    filepath = _join(rel_path, FILE_NAME)
    make_temp(mock_data_access.local_fs, FILE_NAME)
    mock_data_access.move_to(FILE_NAME, rel_path)
    _check_content(mock_data_access.fs, filepath)


def test_move_to_rename(mock_data_access):
    make_temp(mock_data_access.local_fs, FILE_NAME)

    new_fname = "foo.txt"
    mock_data_access.move_to(FILE_NAME, change_name_to=new_fname)
    _check_content(mock_data_access.fs, new_fname)
