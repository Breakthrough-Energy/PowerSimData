import os
from pathlib import Path

SERVER_ADDRESS = 'zeus.intvenlab.com'
HOME_DIR = '/home/EGM/v2'
SCENARIO_LIST = '/home/EGM/v2/ScenarioList.csv'
EXECUTE_LIST = '/home/EGM/v2/ExecuteList.csv'
EXECUTE_DIR = '/home/EGM/v2/tmp'
BASE_PROFILE_DIR = '/home/EGM/v2/raw'
INPUT_DIR = '/home/EGM/v2/data/input'
OUTPUT_DIR = '/home/EGM/v2/data/output'
LOCAL_DIR = os.path.join(str(Path.home()), 'ScenarioData', '')
