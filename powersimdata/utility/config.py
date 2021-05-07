import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
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
    SERVER_ADDRESS = os.getenv("BE_SERVER_ADDRESS", "becompute01.gatesventures.com")
    SERVER_SSH_PORT = os.getenv("BE_SERVER_SSH_PORT", 22)
    MODEL_DIR = "/home/bes/pcm"


@dataclass(frozen=True)
class ContainerConfig(Config):
    SERVER_ADDRESS = os.getenv("BE_SERVER_ADDRESS", "reisejl")


@dataclass(frozen=True)
class LocalConfig(Config):
    DATA_ROOT_DIR = Config.LOCAL_DIR
    ENGINE_DIR = os.getenv("ENGINE_DIR")


class DeploymentMode:
    Server = "SERVER"
    Container = "CONTAINER"
    Local = "LOCAL"

    CONFIG_MAP = {Server: ServerConfig, Container: ContainerConfig, Local: LocalConfig}


def get_deployment_mode():
    mode = os.getenv("DEPLOYMENT_MODE")
    if mode is None:
        return DeploymentMode.Server
    if mode == "1" or mode.lower() == "container":
        return DeploymentMode.Container
    if mode == "2" or mode.lower() == "local":
        return DeploymentMode.Local


def get_config():
    mode = get_deployment_mode()
    return DeploymentMode.CONFIG_MAP[mode]()
