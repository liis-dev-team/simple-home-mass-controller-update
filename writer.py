from contextlib import contextmanager
from datetime import datetime
from io import TextIOWrapper
from os import makedirs, path as os_path

from yaml import dump, Dumper

from dtos import ReportConfig


class ReportWriter:
    def __init__(self, config: ReportConfig) -> None:
        self.config = config
        now = datetime.now()
        dirname = f"report_{now.strftime("%d-%m-%Y_%H:%M:%S.%s")}"
        self.dir_path = os_path.join(config.build_report_dir_path(), dirname)
        makedirs(self.dir_path)

    def write_text_file(self, data: str, file_name: str, dir_name: str = ""):
        """
        * file_name: name of the file to write too
        * dir_name: name of the subdir, where file is stored
        """
        with self.open(file_name, dir_name) as file:
            file.write(data)
            file.write("\n")

    def write_yaml_file(self, data: dict, file_name: str, dir_name: str = ""):
        """
        * file_name: name of the file to write too
        * dir_name: name of the subdir, where file is stored
        """
        if not file_name.endswith(".yaml"):
            raise Exception
        with self.open(file_name, dir_name) as file:
            dump(data, stream=file, Dumper=Dumper)

    @contextmanager
    def open(self, file_name: str,
             dir_name: str = "",
             mode: str = "+a") -> TextIOWrapper:
        dir_path = os_path.join(self.dir_path, dir_name)
        makedirs(dir_path, exist_ok=True)
        file_path = os_path.join(dir_path, file_name)
        with open(file_path, mode) as file:
            yield file
