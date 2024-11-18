from abc import ABC, abstractmethod
import asyncio
from datetime import datetime
import json
import re
from typing import Any, Generator, Iterable
from uuid import uuid4
from itertools import chain

from websockets import connect

from core import colors, get_auth_header
from dtos import ControllerStatus, WorkerResponse, Config
from executor import PoolExecutor
from writer import ReportWriter


class ActionsAbc(ABC):
    def __init__(self, config: Config, writer: ReportWriter) -> None:
        self.config = config
        self.exec = PoolExecutor(config)
        self.writer = writer

    @abstractmethod
    async def run(self, *args, **kwargs) -> Any:
        ...


class GetControllers(ActionsAbc):
    def __init__(self, config: Config, writer: ReportWriter) -> None:
        super().__init__(config, writer)
        self.url = config.websockets.build_url(controller_uid="null")
        self.headers = {"Authorization": get_auth_header(config)}

    def filter_controllers(
        self,
        controllers: list[ControllerStatus],
    ) -> Generator[ControllerStatus, None, None]:
        if self.config.controllers_whitelist:
            controllers_uid = [c2.uid for c2 in controllers]
            controllers_gen = chain(
                (
                    c for c in controllers
                    if c.uid in self.config.controllers_whitelist
                 ),
                (
                    ControllerStatus(uid=c, status="offline")
                    for c in self.config.controllers_whitelist
                    if c not in controllers_uid
                ),
            )
        else:
            controllers_gen = (
                c for c in controllers
                if c.uid not in self.config.controllers_blacklist
            )
        if self.config.controller_uid_regex:
            pattern = re.compile(self.config.controller_uid_regex)
            controllers_gen = (c for c in controllers_gen if pattern.fullmatch(c.uid))
        return controllers_gen

    async def run(self) -> list[ControllerStatus]:
        print("\nRequest all connected controllers:")
        controllers_states = {"online": [], "inactive": [], "offline": []}
        message = {
            "action": "get_all_controllers",
            "uid": "null",
        }
        controllers: list[ControllerStatus]
        result: list[ControllerStatus] = []
        async with connect(self.url, additional_headers=self.headers) as ws:
            await ws.send(json.dumps(message))
            while True:
                async with asyncio.timeout(5):
                    resp = await ws.recv()
                resp = json.loads(resp)
                if resp.get("action") == "get_all_controllers":
                    controllers = [ControllerStatus(**c)
                                   for c in resp["controllers"]]
                    break
        for cont in self.filter_controllers(controllers):
            match cont.status:
                case "online":
                    controllers_states["online"].append(cont.uid)
                    result.append(cont)
                case "inactive":
                    controllers_states["inactive"].append(cont.uid)
                    result.append(cont)
                case _:
                    controllers_states["offline"].append(cont.uid)
        controllers_states["total_available"] = len(controllers_states["online"]) + len(controllers_states["inactive"])
        controllers_states["total_unavailable"] = len(controllers_states["offline"])
        print(controllers_states["total_available"],
              "controllers available")
        self.writer.write_yaml_file(
            data=controllers_states,
            file_name="controllers_states.yaml")
        return result


class ValidateControllers(ActionsAbc):
    def __init__(self, config: Config, writer: ReportWriter) -> None:
        super().__init__(config, writer)
        self.headers = {"Authorization": get_auth_header(config)}

    async def __worker(self, uid: str) -> WorkerResponse:
        def save_response(resp: str):
            if not self.config.report_writer.detail_report:
                return
            now = datetime.now()
            self.writer.write_text_file(
                data=f"{now.strftime("%d-%m-%Y_%H:%M:%S.%s")} | {resp}",
                file_name=f"{uid}.txt",
                dir_name="get_controller_version")
        get_all_versions = {
            "action": "updater_command",
            "command": "get_all_versions",
            "uid": uid,
        }
        admin_subscribe = {
            "action": "admin_subscribe",
            "uid": uid}
        id_ = str(uuid4())
        url = self.config.websockets.build_url(uid, client_id=f"{uid}_worker_{id_}")
        async with connect(url, additional_headers=self.headers) as websocket:
            await websocket.send(json.dumps(admin_subscribe))
            await asyncio.sleep(.2)
            await websocket.send(json.dumps(get_all_versions))
            resp: dict = {}
            while True:
                try:
                    async with asyncio.timeout(10):
                        resp = await websocket.recv()
                        save_response(resp)
                        resp = json.loads(resp)
                        if resp.get("feedback_type") == "all_software_versions":
                            return WorkerResponse(response=resp,
                                                  uid=uid, status="success")
                except asyncio.TimeoutError:
                    return WorkerResponse(response=None, uid=uid,
                                          status="error")

    async def run(self,
                  controllers: list[ControllerStatus]) -> list[str]:
        """
            Return list of controllers uid, that can be updated
        """
        if not self.config.validate_controllers:
            print(colors.yellow("Skip controllers validation"))
            return
        print("\nValidate connected controllers:")
        approved_controllers = []
        rejected_controllers = []
        active_controllers = [c.uid for c in controllers
                              if c.status != "offline"]
        # a = next(active_controllers)
        # active_controllers = (a for _ in range(100))
        executor = PoolExecutor(config=self.config)
        result = executor.run(func=self.__worker,
                              payload=active_controllers)
        resp: WorkerResponse
        counter = 1
        async for resp in result:
            prefix = f"[{counter}/{len(active_controllers)}]"
            counter += 1
            if resp.status == "error":
                print(prefix, resp.uid, colors.red("REJECTED"))
                rejected_controllers.append(resp.uid)
                continue
            print(prefix, resp.uid, colors.green("APPROVED"))
            approved_controllers.append(resp.uid)
        self.writer.write_yaml_file(
            file_name="controllers_states.yaml",
            data={
                "approved_controllers": approved_controllers,
                "rejected_controllers": rejected_controllers,
                "total_approved_controllers": len(approved_controllers),
                "total_rejected_controllers": len(rejected_controllers)
            },
        )
        print(len(approved_controllers), "controllers approved")
        return approved_controllers


class UpdateControllers(ActionsAbc):
    def __init__(self, config: Config, writer: ReportWriter) -> None:
        super().__init__(config, writer)
        self.headers = {"Authorization": get_auth_header(config)}

    async def __worker(self, uid: str) -> WorkerResponse:
        def save_response(resp: str):
            if not self.config.report_writer.detail_report:
                return
            now = datetime.now()
            self.writer.write_text_file(
                data=f"{now.strftime("%d-%m-%Y_%H:%M:%S.%s")} | {resp}",
                file_name=f"{uid}.txt",
                dir_name="update_software")
        message = {
            "action": "updater_command",
            "command": "update_software",
            "uid": uid,
            "url": self.config.software_build_url,
            "token": self.config.file_service_token
        }
        url = self.config.websockets.build_url(uid, client_id=f"{uid}_worker")
        async with connect(url, additional_headers=self.headers) as websocket:
            await websocket.send(json.dumps(message))
            resp: dict = {}
            while True:
                try:
                    async with asyncio.timeout(5*60):
                        resp_raw = await websocket.recv()
                        resp = json.loads(resp_raw)
                        action = resp.get("action")
                        feedback_type = resp.get("feedback_type")
                        if action != "updater_feedback":
                            continue
                        save_response(resp_raw)
                        if feedback_type == "update_progress":
                            continue
                        if feedback_type == "error":
                            return WorkerResponse(
                                response=resp, uid=uid, status="error"
                            )
                except asyncio.TimeoutError:
                    return WorkerResponse(response=None,
                                          uid=uid,
                                          status="error")

    async def run(self, controllers_uids: Iterable[str]):
        failed_controllers = []
        updated_controllers = []
        executor = PoolExecutor(config=self.config)
        result = executor.run(self.__worker,
                              payload=controllers_uids)
        resp: WorkerResponse
        async for resp in result:
            if resp.status == "error":
                print(resp.uid, "update", colors.red(
                    "FAILED" if resp.response else "TIMEOUT"))
                failed_controllers.append(resp.uid)
                continue
            print(resp.uid, colors.green("UPDATED"))
            updated_controllers.append(resp.uid)
        self.writer.write_yaml_file(
            file_name="update_result.yaml",
            data={
                "updated_controllers": updated_controllers,
                "failed_controllers": failed_controllers,
                "total_updated_controllers": len(updated_controllers),
                "total_failed_controllers": len(failed_controllers)
            },
        )
        print(len(updated_controllers), "controllers updated")
        return updated_controllers
