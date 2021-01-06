import os
import sys
import tempfile
from pathlib import Path

import pytest

from powersimdata.data_access.data_access import SSHDataAccess
from powersimdata.tests.mock_ssh import MockConnection
from powersimdata.utility.server_setup import get_server_user

CONTENT = b"content"


@pytest.fixture
def data_access():
    data_access = SSHDataAccess()
    yield data_access
    data_access.close()


@pytest.fixture
def temp_fs(tmp_path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()
    return src_dir, dest_dir


@pytest.fixture
def mock_data_access(monkeypatch, temp_fs):
    data_access = SSHDataAccess()
    monkeypatch.setattr(data_access, "_ssh", MockConnection())
    data_access.root = temp_fs[0]
    data_access.dest_root = temp_fs[1]
    yield data_access
    data_access.close()


@pytest.fixture
def make_temp(temp_fs):
    files = []

    def _make_temp(rel_path=None, remote=True):
        rel_path = Path("" if rel_path is None else rel_path)
        root = temp_fs[0] if remote else temp_fs[1]
        location = root / rel_path
        test_file = tempfile.NamedTemporaryFile(dir=location)
        files.append(test_file)
        test_file.write(CONTENT)
        test_file.seek(0)
        return os.path.basename(test_file.name)

    yield _make_temp
    for f in files:
        # NOTE: the tmp_path fixture will handle remaining cleanup
        try:
            f.close()
        except:  # noqa: ignore failure if file already deleted
            pass


def _check_content(filepath):
    assert os.path.exists(filepath)
    with open(filepath, "rb") as f:
        assert CONTENT == f.read()


@pytest.mark.integration
@pytest.mark.ssh
def test_setup_server_connection(data_access):
    _, stdout, _ = data_access.execute_command("whoami")
    assert stdout.read().decode("utf-8").strip() == get_server_user()


def test_mocked_correctly(mock_data_access):
    assert isinstance(mock_data_access.ssh, MockConnection)


@pytest.mark.skipif(sys.platform.startswith("win"), reason="Does not run on windows")
def test_copy_from(mock_data_access, temp_fs, make_temp):
    fname = make_temp()
    mock_data_access.copy_from(fname)
    _check_content(os.path.join(temp_fs[1], fname))


@pytest.mark.skipif(sys.platform.startswith("win"), reason="Does not run on windows")
def test_copy_from_multi_path(mock_data_access, temp_fs, make_temp):
    rel_path = Path("foo", "bar")
    src_path = temp_fs[0] / rel_path
    src_path.mkdir(parents=True)
    fname = make_temp(rel_path)
    mock_data_access.copy_from(fname, rel_path)
    _check_content(os.path.join(temp_fs[1], rel_path, fname))


@pytest.mark.skipif(sys.platform.startswith("win"), reason="Does not run on windows")
def test_copy_to(mock_data_access, make_temp):
    fname = make_temp(remote=False)
    mock_data_access.copy_to(fname)
    _check_content(os.path.join(mock_data_access.root, fname))


@pytest.mark.skipif(sys.platform.startswith("win"), reason="Does not run on windows")
def test_copy_to_multi_path(mock_data_access, make_temp):
    rel_path = Path("foo", "bar")
    remote_path = mock_data_access.root / rel_path
    remote_path.mkdir(parents=True)
    fname = make_temp(remote=False)
    mock_data_access.copy_to(fname, rel_path)
    _check_content(os.path.join(remote_path, fname))


@pytest.mark.skipif(sys.platform.startswith("win"), reason="Does not run on windows")
def test_copy_to_rename(mock_data_access, make_temp):
    fname = make_temp(remote=False)
    new_fname = "new_fname"
    mock_data_access.copy_to(fname, change_name_to=new_fname)
    _check_content(os.path.join(mock_data_access.root, new_fname))


def test_check_filename(mock_data_access):
    with pytest.raises(ValueError):
        mock_data_access.copy_from("dir/foo.txt", "dir")
    with pytest.raises(ValueError):
        mock_data_access.copy_to("dir/foo.txt", "asdf")
