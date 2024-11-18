import sys
import asyncio
import json
from dataclasses import asdict

from yaml import load, Loader


from actions import GetControllers, UpdateControllers, ValidateControllers
from core import CustomEncoder, colors
from dtos import Config, ReportConfig, WebsocketsConfig
from writer import ReportWriter


"""
План:
* Получаем список подключенных контроллеров
* Для каждого контроллера отправляем команду на получение информации о версии ПО
* Если контроллер отдает информацию о версиях, отправляем команду на обновление прошивки
"""


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
    def already_confirmed(cls) -> bool:
        """
        Return True, if `-y` was provided as command attribute
        """
        return "-y" in sys.argv

    @classmethod
    def read_config_file(cls, file_path: str = "config.yaml") -> Config:
        print("Loading", file_path, "...")
        with open(file_path, "r") as file:
            data: dict = load(file, Loader=Loader)
        if data is None:
            raise Exception
        if not isinstance(data.get("websockets"), dict):
            raise Exception
        ws = WebsocketsConfig(**data.pop("websockets"))
        report_conf = ReportConfig(**data.pop("report_writer", {}))
        conf = Config(websockets=ws, report_writer=report_conf, **data)
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


class App:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.writer = ReportWriter(config.report_writer)

    async def run_actions(self):
        controllers = await GetControllers(
            self.config, self.writer).run()
        controllers_uids = await ValidateControllers(
            self.config, self.writer).run(controllers)
        if not controllers_uids:
            print(colors.yellow("No controllers to update."),
                  "Exit.", sep="\n")
            return
        if not ConfigProdiser.already_confirmed():
            input("Push Enter to launch update sequence or Ctrl+C to exit.")
        print("\nUpdate connected controllers:")
        await UpdateControllers(
            self.config, self.writer).run(controllers_uids)


async def main():
    config = ConfigProdiser.get_config()
    if not config:
        return
    print("Loaded configuration:")
    print(json.dumps(asdict(config), indent=1, cls=CustomEncoder).replace('"', "").replace('{', "").replace('}', "").replace(',', ""))
    if not ConfigProdiser.already_confirmed():
        input("Push Enter to continue or Ctrl+C to exit.")
    ws = App(config)
    await ws.run_actions()


if __name__ == "__main__":
    asyncio.run(main())
