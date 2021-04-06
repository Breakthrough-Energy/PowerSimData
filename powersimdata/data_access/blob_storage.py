import os

import requests
from tqdm.auto import tqdm

BASE_URL = "https://bescienceswebsite.blob.core.windows.net"


class BlobClient:
    def __init__(self, container):
        self.base_url = f"{BASE_URL}/{container}"

    def download(self, blob_path, dest):
        print(f"--> Downloading {os.path.basename(blob_path)} from blob storage.")
        url = self.base_url + "/" + blob_path
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
