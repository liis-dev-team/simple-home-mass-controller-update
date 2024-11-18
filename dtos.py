from dataclasses import dataclass, field
from os import path as sys_path
from os import getcwd
from typing import Any, Literal


@dataclass
class WebsocketsConfig:
    login: str = field(repr=False)
    password: str = field(repr=False)
    url: str = "wss://dev.cloud.simple-home.liis.su"

    def build_url(self, controller_uid: str, path: str = "ws/admin", **kwargs):
        url = f"{sys_path.join(self.url, path)}?uid={controller_uid}"
        for k, v in kwargs.items():
            url += f"&{k}={v}"
        return url


@dataclass
class ReportConfig:
    report_dir_path: str = field(default_factory=getcwd)
    is_absolute_path: bool = True
    detail_report: bool = True

    def build_report_dir_path(self) -> str:
        if self.is_absolute_path:
            return self.report_dir_path
        return sys_path.join(getcwd(), self.report_dir_path)


@dataclass
class Config:
    websockets: WebsocketsConfig
    report_writer: ReportConfig
    software_build_url: str
    file_service_token: str
    max_pool_size: int = 10
    # white list of controllers uid
    controllers_blacklist: set[str] = field(default_factory=set)
    # black list of controllers uid. Ignored if whitelist provided
    controllers_whitelist: set[str] = field(default_factory=set)
    # regex expression, that will be used to filter controllers uids
    controller_uid_regex: str | None = None
    validate_controllers: bool = True


@dataclass
class ControllerStatus:
    uid: str
    status: Literal["online", "inactive", "offline"]


@dataclass
class WorkerResponse:
    response: Any
    uid: str
    status: Literal["success", "error"]
