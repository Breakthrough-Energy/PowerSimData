import configparser
import os
import shutil
from dataclasses import dataclass
from pathlib import Path

from powersimdata.utility import templates

INI_FILE = "config.ini"
if Path(INI_FILE).exists():
    conf = configparser.ConfigParser()
    conf.read(INI_FILE)
    for k, v in conf["PowerSimData"].items():
        os.environ[k.upper()] = v


@dataclass(frozen=True)
class Config:
    """Base class for configuration data. It should contain all expected keys,
    defaulting to None when not universally applicable.
    """

    SERVER_ADDRESS = None
    SERVER_SSH_PORT = None
    BACKUP_DATA_ROOT_DIR = None
    MODEL_DIR = None
    ENGINE_DIR = None
    DATA_ROOT_DIR = "/mnt/bes/pcm"
    EXECUTE_DIR = "tmp"
    INPUT_DIR = ("data", "input")
    OUTPUT_DIR = ("data", "output")
    LOCAL_DIR = os.path.join(Path.home(), "ScenarioData", "")


@dataclass(frozen=True)
class ServerConfig(Config):
    """Values specific to internal client/server usage"""

    SERVER_ADDRESS = os.getenv("BE_SERVER_ADDRESS", "becompute01.gatesventures.com")
    SERVER_SSH_PORT = os.getenv("BE_SERVER_SSH_PORT", 22)
    MODEL_DIR = "/home/bes/pcm"


@dataclass(frozen=True)
class ContainerConfig(Config):
    """Values specific to containerized environment"""

    SERVER_ADDRESS = os.getenv("BE_SERVER_ADDRESS", "reisejl")


@dataclass(frozen=True)
class LocalConfig(Config):
    """Values specific to native installation"""

    DATA_ROOT_DIR = Config.LOCAL_DIR
    ENGINE_DIR = os.getenv("ENGINE_DIR")

    def initialize(self):
        """Create data directory with blank templates"""
        confirmed = input(
            f"Provision directory {self.LOCAL_DIR}? [y/n] (default is 'n')"
        )
        if confirmed.lower() != "y":
            print("Operation cancelled.")
            return
        os.makedirs(self.LOCAL_DIR, exist_ok=True)
        for fname in ("ScenarioList.csv", "ExecuteList.csv"):
            orig = os.path.join(templates.__path__[0], fname)
            dest = os.path.join(self.LOCAL_DIR, fname)
            shutil.copy(orig, dest)
        print("--> Done!")


class DeploymentMode:
    """Constants representing the type of installation being used"""

    Server = "SERVER"
    Container = "CONTAINER"
    Local = "LOCAL"

    CONFIG_MAP = {Server: ServerConfig, Container: ContainerConfig, Local: LocalConfig}


def get_deployment_mode():
    """Get the deployment mode used to determine various configuration values

    :return: (*str*) -- the deployment mode
    """
    mode = os.getenv("DEPLOYMENT_MODE")
    if mode is None:
        return DeploymentMode.Server
    if mode == "1" or mode.lower() == "container":
        return DeploymentMode.Container
    if mode == "2" or mode.lower() == "local":
        return DeploymentMode.Local


def get_config():
    """Get a config instance based on the DEPLOYMENT_MODE environment variable

    :return: (*powersimdata.utility.config.Config*) -- a config instance
    """
    mode = get_deployment_mode()
    return DeploymentMode.CONFIG_MAP[mode]()
