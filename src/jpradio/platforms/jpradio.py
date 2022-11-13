from typing import Any, Dict, List, Optional

from ..program import Program
from ..station import Station
from .base import Platform
from .hibiki import Hibiki
from .onsen import Onsen
from .radiko import Radiko


def _get_all_platforms_cls() -> List[Platform]:
    return [Radiko, Onsen, Hibiki]


class Jpradio(Platform):
    def __init__(self, configs: Dict[str, Any]) -> None:
        super().__init__()
        all_platform_cls = _get_all_platforms_cls()
        self._platforms = {
            cls.id: cls(**configs.get(cls.id, {})) for cls in all_platform_cls
        }
        self._station_id_platform_map = {
            station.id: self._platforms[station.platform_id]
            for station in self.get_stations()
        }

    def id(self, program: Program) -> str:
        return self.get_platform(program).id

    def name(self, program: Program) -> str:
        return self.get_platform(program).name

    def ascii_name(self, program: Program) -> str:
        return self.get_platform(program).ascii_name

    def url(self, program: Program) -> str:
        return self.get_platform(program).url

    def login(self) -> None:
        for platform in self._platforms.values():
            platform.login()

    def close(self) -> None:
        for platform in self._platforms.values():
            platform.close()

    def get_platform(self, program: Program) -> Platform:
        return self._station_id_platform_map[program.station_id]

    def get_stations(self) -> List[Station]:
        return sum([p.get_stations() for p in self._platforms.values()], [])

    def get_programs(
        self, filters: Optional[List[str]] = None, **kwargs
    ) -> List[Program]:
        return sum([p.get_programs(filters) for p in self._platforms.values()], [])

    def download_media(self, program: Program, filename: str) -> None:
        self.get_platform(program).download_media(program, filename)

    def get_default_filename(self, program: Program) -> str:
        return self.get_platform(program).get_default_filename(program)
