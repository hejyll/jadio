from typing import Any, Dict, List

from ..program import Program
from ..station import Station
from .base import Service
from .hibiki import Hibiki
from .onsen import Onsen
from .radiko import Radiko


def _get_all_service_cls() -> List[Service]:
    return [Radiko, Onsen, Hibiki]


class Jadio(Service):
    def __init__(self, configs: Dict[str, Any]) -> None:
        super().__init__()
        all_service_cls = _get_all_service_cls()
        self._services = {
            cls.service_id(): cls(**configs.get(cls.service_id(), {}))
            for cls in all_service_cls
        }

    def service_id(self, program: Program) -> str:
        return self.get_service(program).service_id()

    def name(self, program: Program) -> str:
        return self.get_service(program).name()

    def link_url(self, program: Program) -> str:
        return self.get_service(program).link_url()

    def login(self) -> None:
        for service in self._services.values():
            service.login()

    def close(self) -> None:
        for service in self._services.values():
            service.close()

    def get_service(self, program: Program) -> Service:
        return self._services[program.service_id]

    def get_stations(self, **kwargs) -> List[Station]:
        return sum(
            [service.get_stations(**kwargs) for service in self._services.values()], []
        )

    def get_programs(self, **kwargs) -> List[Program]:
        return sum(
            [service.get_programs(**kwargs) for service in self._services.values()], []
        )

    def download_media(self, program: Program, filename: str) -> None:
        self.get_service(program).download_media(program, filename)

    def get_default_filename(self, program: Program) -> str:
        return self.get_service(program).get_default_filename(program)
