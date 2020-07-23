import os
import posixpath
from pathlib import Path

SERVER_ADDRESS = "becompute01.gatesventures.com"
DATA_ROOT_DIR = "/mnt/bes/pcm"
SCENARIO_LIST = posixpath.join(DATA_ROOT_DIR, "ScenarioList.csv")
EXECUTE_LIST = posixpath.join(DATA_ROOT_DIR, "ExecuteList.csv")
EXECUTE_DIR = posixpath.join(DATA_ROOT_DIR, "tmp")
BASE_PROFILE_DIR = posixpath.join(DATA_ROOT_DIR, "raw")
INPUT_DIR = posixpath.join(DATA_ROOT_DIR, "data/input")
OUTPUT_DIR = posixpath.join(DATA_ROOT_DIR, "data/output")
LOCAL_DIR = os.path.join(str(Path.home()), "ScenarioData", "")
MODEL_DIR = "/home/bes/pcm"
