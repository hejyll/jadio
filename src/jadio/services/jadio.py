from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..program import Program
from ..station import Station
from .base import Service
from .hibiki import Hibiki
from .onsen import Onsen
from .radiko import Radiko


def _get_all_service_cls() -> List[Service]:
    return [Radiko, Onsen, Hibiki]


class Jadio(Service):
    """Class that supervises all service classes.

    Args:
        configs (dict): dict that defines the arguments for each service
            class. key is `service_id`.
    """

    def __init__(self, configs: Dict[str, Any]) -> None:
        super().__init__()
        self._services = {
            cls.service_id(): cls(**configs.get(cls.service_id(), {}))
            for cls in _get_all_service_cls()
        }

    def service_id(self, program: Program) -> str:
        return self.get_service_from_program(program).service_id()

    def name(self, program: Program) -> str:
        return self.get_service_from_program(program).name()

    def link_url(self, program: Program) -> str:
        return self.get_service_from_program(program).link_url()

    def login(self) -> None:
        for service in self._services.values():
            service.login()

    def close(self) -> None:
        for service in self._services.values():
            service.close()

    def get_service_from_program(self, program: Program) -> Service:
        return self._services[program.service_id]

    def get_stations(self, **kwargs) -> List[Station]:
        return sum(
            [service.get_stations(**kwargs) for service in self._services.values()], []
        )

    def get_programs(self, **kwargs) -> List[Program]:
        return sum(
            [service.get_programs(**kwargs) for service in self._services.values()], []
        )

    def download(
        self,
        program: Program,
        file_path: Optional[Union[str, Path]] = None,
        set_tag: bool = True,
        set_cover_image: bool = True,
    ) -> Path:
        return self.get_service_from_program(program).download(
            program=program,
            file_path=file_path,
            set_tag=set_tag,
            set_cover_image=set_cover_image,
        )

    def _download_media(self, program: Program, file_path: Union[str, Path]) -> None:
        self.get_service_from_program(program)._download_media(program, file_path)

    def _get_default_file_path(self, program: Program) -> Path:
        return self.get_service_from_program(program)._get_default_file_path(program)
