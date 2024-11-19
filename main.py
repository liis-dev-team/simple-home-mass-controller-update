import asyncio
import json
from dataclasses import asdict

from actions import GetControllers, UpdateControllers, ValidateControllers
from core import CustomEncoder
from dtos import Config
from writer import ReportWriter
from config_produser import ConfigProdiser


class App:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.writer = ReportWriter(config.report_writer)

    async def run_actions(self):
        controllers = await GetControllers(
            self.config, self.writer).run()
        controllers_uids = await ValidateControllers(
            self.config, self.writer).run(controllers)
        await UpdateControllers(
            self.config, self.writer).run(controllers_uids)


async def main():
    config = ConfigProdiser.get_config()
    if not config:
        return
    print("Loaded configuration:")
    print(json.dumps(asdict(config), indent=1, cls=CustomEncoder))
    if not ConfigProdiser.already_confirmed():
        input("Push Enter to continue or Ctrl+C to exit.")
    ws = App(config)
    await ws.run_actions()


if __name__ == "__main__":
    asyncio.run(main())
