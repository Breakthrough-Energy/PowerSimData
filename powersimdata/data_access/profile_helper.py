import os

import fs
import requests
from tqdm.auto import tqdm

from powersimdata.utility import server_setup


class ProfileHelper:
    BASE_URL = "https://besciences.blob.core.windows.net/profiles"

    @staticmethod
    def get_file_components(scenario_info, field_name):
        """Get the file name and relative path for the given profile and
        scenario.

        :param dict scenario_info: metadata for a scenario.
        :param str field_name: the kind of profile.
        :return: (*tuple*) -- file name and list of path components.
        """
        version = scenario_info["base_" + field_name]
        file_name = field_name + "_" + version + ".csv"
        grid_model = scenario_info["grid_model"]
        return file_name, ("raw", grid_model)

    @staticmethod
    def download_file(file_name, from_dir):
        """Download the profile from blob storage at the given path.

        :param str file_name: profile csv.
        :param tuple from_dir: tuple of path components.
        :return: (*str*) -- path to downloaded file.
        """
        print(f"--> Downloading {file_name} from blob storage.")
        url_path = "/".join(from_dir)
        url = f"{ProfileHelper.BASE_URL}/{url_path}/{file_name}"
        dest = os.path.join(server_setup.LOCAL_DIR, *from_dir, file_name)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        resp = requests.get(url, stream=True)
        content_length = int(resp.headers.get("content-length", 0))
        with open(dest, "wb") as f:
            with tqdm(
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
                miniters=1,
                total=content_length,
            ) as pbar:
                for chunk in resp.iter_content(chunk_size=4096):
                    f.write(chunk)
                    pbar.update(len(chunk))

        return dest

    @staticmethod
    def parse_version(grid_model, kind, version):
        """Parse available versions from the given spec.

        :param str grid_model: grid model.
        :param str kind: *'demand'*, *'hydro'*, *'solar'* or *'wind'*.
        :param dict version: version information per grid model.
        :return: (*list*) -- available profile version.
        """
        if grid_model in version and kind in version[grid_model]:
            return version[grid_model][kind]
        print("No %s profiles available." % kind)
        return []

    @staticmethod
    def get_profile_version_cloud(grid_model, kind):
        """Returns available raw profile from blob storage.

        :param str grid_model: grid model.
        :param str kind: *'demand'*, *'hydro'*, *'solar'* or *'wind'*.
        :return: (*list*) -- available profile version.
        """

        resp = requests.get(f"{ProfileHelper.BASE_URL}/version.json")
        return ProfileHelper.parse_version(grid_model, kind, resp.json())

    @staticmethod
    def get_profile_version_local(grid_model, kind):
        """Returns available raw profile from local file.

        :param str grid_model: grid model.
        :param str kind: *'demand'*, *'hydro'*, *'solar'* or *'wind'*.
        :return: (*list*) -- available profile version.
        """
        profile_dir = fs.path.join(server_setup.LOCAL_DIR, "raw", grid_model)
        lfs = fs.open_fs(profile_dir)
        matching = [f for f in lfs.listdir(".") if kind in f]
        return [f.lstrip(f"{kind}_").rstrip(".csv") for f in matching]
