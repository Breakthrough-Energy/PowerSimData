import hashlib
import json
import os
import shutil
from contextlib import contextmanager
from zipfile import ZipFile

import requests
from tqdm import tqdm

url = "https://zenodo.org/api/records/"


class Zenodo:
    """Get data from a Zenodo archive.

    :param str record_id: zenodo record id
    """

    def __init__(self, record_id):
        """Constructor"""
        self.record_id = record_id
        self.content = self._get_record_content()

    def _get_record_content(self):
        """Make HTTP request to zenodo API and retrieve content.

        :return: (*dict*) -- content of the response in unicode.
        :raises Exception: if connection times out.
        :raises ValueError: if record is invalid.
        """
        try:
            r = requests.get(url + self.record_id, timeout=10)
        except requests.exceptions.ConnectTimeout:
            raise ConnectionError("Connection to zenodo.org timed out")

        if not r.ok:
            raise ValueError(f"Record could not be accessed. Status: {r.status_code}")

        content = json.loads(r.text)
        metadata = content["metadata"]
        print(f"Title: {metadata['title']}")
        print(f"Publication date: {metadata['publication_date']}")
        print(f"Version: {metadata['version']}")
        print(f"DOI: {metadata['doi']}")

        return content

    def _get_remote_checksum(self, f):
        """Get checksum of local copy of a file

        :param dict f: dictionary containing information on the remote copy of a file.
        :return: (*str*) -- checksum
        """
        return f["checksum"].split(":")[1]

    def _get_local_checksum(self, f):
        """Get remote copy of a file.

        :param dict f: dictionary containing information on the local copy of a file.
        :return: (*str*) -- checksum if file exists
        """
        filename = os.path.join(self.dir, f["key"])
        if not os.path.exists(filename):
            return "invalid"
        else:
            h = hashlib.new(f["checksum"].split(":")[0])
            with open(filename, "rb") as file:
                bytes = file.read()
            h.update(bytes)
            return h.hexdigest()

    @contextmanager
    def _change_dir(self):
        work_dir = os.getcwd()
        os.chdir(os.path.expanduser(self.dir))
        try:
            yield
        finally:
            os.chdir(work_dir)

    def _download_data(self, f):
        """Fetch data.

        :param dict f: information on the file to download.
        """
        with requests.get(f["links"]["self"], stream=True) as r:
            r.raise_for_status()
            with open(f["key"], "wb") as file:
                with tqdm(
                    unit="B",
                    unit_scale=True,
                    unit_divisor=1024,
                    miniters=1,
                    total=f["size"],
                ) as pbar:
                    for chunk in r.iter_content(chunk_size=8192):
                        file.write(chunk)
                        pbar.update(len(chunk))

    def _delete_data(self, f):
        """Delete data.

        :param dict f: information on the file to delete.
        """
        os.remove(f["key"])
        if f["type"] == "zip":
            shutil.rmtree(f["key"][:-4])

    def _unzip_data(self, f):
        """Unzip data.

        :param dict f: information on the file to unzip.
        """
        if f["type"] == "zip":
            with ZipFile(f["key"], "r") as file:
                file.extractall()

    def load_data(self, model_dir):
        """Download file(s)

        :param str model_dir: path to directory of the grid model.
        :raises FileNotFoundError: if ``model_dir`` does not exist.
        """
        if not os.path.isdir(model_dir):
            raise FileNotFoundError(f"{model_dir} does not exist")
        else:
            version = self.content["metadata"]["version"]
            self.dir = os.path.join(model_dir, f"data_{version}")
            try:
                os.mkdir(self.dir)
                for f in self.content["files"]:
                    with self._change_dir():
                        self._download_data(f)
                        self._unzip_data(f)
            except FileExistsError:
                for f in self.content["files"]:
                    if self._get_local_checksum(f) != self._get_remote_checksum(f):
                        with self._change_dir():
                            self._delete_data(f)
                            self._download_data(f)
                            self._unzip_data(f)
                    else:
                        print(f"{f['key']} has been downloaded previously")
