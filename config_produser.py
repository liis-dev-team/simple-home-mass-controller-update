from functools import cache
import sys

from yaml import load, FullLoader

from core import colors
from dtos import Config


class ConfigProdiser:

    @classmethod
    def get_config_path(cls) -> str | None:
        try:
            c = sys.argv.index("-c")
            return sys.argv[c+1]
        except (ValueError, IndexError):
            print(colors.yellow("Config file path was not provided"))

    @classmethod
    def get_build_url(cls) -> str | None:
        try:
            c = sys.argv.index("-u")
            return sys.argv[c+1]
        except ValueError:
            return
        except IndexError:
            print(colors.yellow("Build url was not provided"))

    @classmethod
    @cache
    def already_confirmed(cls) -> bool:
        """
        Return True, if `-y` was provided as command attribute
        """
        return "-y" in sys.argv

    @classmethod
    def read_config_file(cls, file_path: str = "config.yaml") -> Config:
        print("Loading", file_path, "...")
        with open(file_path, "r") as file:
            data: dict = load(file, Loader=FullLoader)
        if data is None:
            raise Exception("Fail to load config file")
        conf = Config(**data)
        return conf

    @classmethod
    def get_config(cls) -> Config | None:
        config_path = cls.get_config_path()
        if config_path is None:
            return
        kwargs = {}
        if config_path:
            kwargs["file_path"] = config_path
        config = cls.read_config_file(**kwargs)
        build_url = cls.get_build_url()
        if build_url:
            config.software_build_url = build_url
        return config
