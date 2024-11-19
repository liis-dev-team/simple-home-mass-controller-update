from dataclasses import dataclass, field
from os import path as sys_path, getcwd
from yaml import YAMLObject
from typing import Any, Literal


@dataclass
class WebsocketsConfig(YAMLObject):
    login: str = field(repr=False)
    password: str = field(repr=False)
    url: str = "wss://dev.cloud.simple-home.liis.su"

    def build_url(self, controller_uid: str, path: str = "ws/admin", **kwargs):
        url = f"{sys_path.join(self.url, path)}?uid={controller_uid}"
        for k, v in kwargs.items():
            url += f"&{k}={v}"
        return url


@dataclass
class ReportConfig(YAMLObject):
    report_dir_path: str = field(default_factory=getcwd)
    is_absolute_path: bool = True
    detail_report: bool = True

    def build_report_dir_path(self) -> str:
        if self.is_absolute_path:
            return self.report_dir_path
        return sys_path.join(getcwd(), self.report_dir_path)


@dataclass
class BaseActionConfig(YAMLObject):
    timeout: int = 10
    enabled: bool = True


@dataclass
class UpdateActionConfig(BaseActionConfig):
    timeout: int = 5*60


@dataclass
class ActionsConfig(YAMLObject):
    validate: BaseActionConfig = field(default_factory=BaseActionConfig)
    update: UpdateActionConfig = field(default_factory=UpdateActionConfig)

    def __post_init__(self):
        if isinstance(self.validate, dict):
            self.validate = BaseActionConfig(**self.validate)
        if isinstance(self.update, dict):
            self.update = UpdateActionConfig(**self.update)


@dataclass
class Config(YAMLObject):
    websockets: WebsocketsConfig
    software_build_url: str
    file_service_token: str
    report_writer: ReportConfig = field(default_factory=ReportConfig)
    actions: ActionsConfig = field(default_factory=ActionsConfig)
    max_pool_size: int = 10
    # white list of controllers uid
    controllers_blacklist: set[str] = field(default_factory=set)
    # black list of controllers uid. Ignored if whitelist provided
    controllers_whitelist: set[str] = field(default_factory=set)
    # regex expression, that will be used to filter controllers uids
    controller_uid_regex: str | None = None

    def __post_init__(self):
        if isinstance(self.websockets, dict):
            self.websockets = WebsocketsConfig(**self.websockets)
        if isinstance(self.report_writer, dict):
            self.report_writer = ReportConfig(**self.report_writer)
        if isinstance(self.actions, dict):
            self.actions = ActionsConfig(**self.actions)


@dataclass
class ControllerStatus:
    uid: str
    status: Literal["online", "inactive", "offline"]


@dataclass
class WorkerResponse:
    response: Any
    uid: str
    status: Literal["success", "error"]
