import json
import os

import requests

from powersimdata.data_access.blob_storage import BASE_URL, BlobClient
from powersimdata.utility import server_setup


class ProfileHelper:
    @staticmethod
    def get_file_components(scenario_info, field_name):
        """Get the file name and relative path for the given profile and
        scenario.

        :param dict scenario_info: a ScenarioInfo instance
        :param str field_name: the kind of profile
        :return: (*tuple*) -- file name and path
        """
        version = scenario_info["base_" + field_name]
        file_name = field_name + "_" + version + ".csv"
        grid_model = scenario_info["grid_model"]
        from_dir = os.path.join("raw", grid_model)
        return file_name, from_dir

    @staticmethod
    def download_file(file_name, from_dir):
        """Download the profile from blob storage at the given path

        :param str file_name: profile csv
        :param str from_dir: the path relative to the blob container
        :return: (*str*) -- path to downloaded file
        """
        url_path = "/".join(os.path.split(from_dir)) + f"/{file_name}"
        dest = os.path.join(server_setup.LOCAL_DIR, from_dir, file_name)
        return BlobClient("profiles").download(url_path, dest)

    @staticmethod
    def parse_version(grid_model, kind, version):
        """Parse available versions from the given spec

        :param str grid_model: grid model.
        :param str kind: *'demand'*, *'hydro'*, *'solar'* or *'wind'*.
        :param dict version: version information per grid model
        :return: (*list*) -- available profile version.
        """
        if grid_model in version and kind in version[grid_model]:
            return version[grid_model][kind]
        print("No %s profiles available." % kind)
        return []

    @staticmethod
    def get_profile_version_cloud(grid_model, kind):
        """Returns available raw profile from blob storage

        :param str grid_model: grid model.
        :param str kind: *'demand'*, *'hydro'*, *'solar'* or *'wind'*.
        :return: (*list*) -- available profile version.
        """
        blob_container = f"{BASE_URL}/profiles"
        resp = requests.get(f"{blob_container}/version.json")
        return ProfileHelper.parse_version(grid_model, kind, resp.json())

    @staticmethod
    def get_profile_version_local(grid_model, kind):
        """Returns available raw profile from local file

        :param str grid_model: grid model.
        :param str kind: *'demand'*, *'hydro'*, *'solar'* or *'wind'*.
        :return: (*list*) -- available profile version.
        """

        version_file = os.path.join(server_setup.LOCAL_DIR, "version.json")
        if not os.path.exists(version_file):
            return []
        with open(version_file) as f:
            version = json.load(f)
            return ProfileHelper.parse_version(grid_model, kind, version)
