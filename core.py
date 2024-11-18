import base64
import json
from typing import Any

from dtos import Config


class CustomEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, set):
            return list(o)
        return super().default(o)


class colors:
    RED = "\033[31m"
    YELLOW = "\033[33m"
    GREEN = "\033[32m"
    BLUE = "\033[34m"
    ENDC = '\033[0m'

    @classmethod
    def red(cls, s) -> str:
        return f"{cls.RED}{s}{cls.ENDC}"

    @classmethod
    def yellow(cls, s) -> str:
        return f"{cls.YELLOW}{s}{cls.ENDC}"

    @classmethod
    def green(cls, s) -> str:
        return f"{cls.GREEN}{s}{cls.ENDC}"

    @classmethod
    def blue(cls, s) -> str:
        return f"{cls.BLUE}{s}{cls.ENDC}"


def get_auth_header(config: Config) -> str:
    login = config.websockets.login
    password = config.websockets.password
    token = base64.b64encode(
        "{}:{}"
        .format(login, password)
        .encode("ascii")).decode("ascii")
    return "Basic {}".format(token)
