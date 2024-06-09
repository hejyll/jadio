import abc
import logging
from typing import List, Optional, Type, TypeVar

from ..program import Program
from ..station import Station
from ..tag import get_mp4_tag, set_mp4_tag

logger = logging.getLogger(__name__)

PlatformType = TypeVar("PlatformType", bound="Platform")


class Platform(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def id(cls) -> str: ...

    @classmethod
    @abc.abstractmethod
    def name(cls) -> str: ...

    @classmethod
    @abc.abstractmethod
    def url(cls) -> str: ...

    def __enter__(self: Type[PlatformType]) -> PlatformType:
        self.login()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def login(self) -> None:
        return None

    def close(self) -> None:
        return None

    def get_stations(self) -> List[Station]:
        return []

    def get_station_from_program(self, program: Program) -> Station:
        ret = list(filter(lambda x: x.id == program.station_id, self.get_stations()))
        if len(ret) == 0:
            raise ValueError(f"{program.station_id} is not found on {self.id()}")
        return ret[0]

    @abc.abstractmethod
    def get_programs(
        self, filters: Optional[List[str]] = None, **kwargs
    ) -> List[Program]: ...

    def download(self, program: Program, filename: Optional[str] = None) -> str:
        filename = filename or self.get_default_filename(program)
        logger.info(
            f'Download {program.service_id} / "{program.program_title}" / "{program.episode_title}"'
            f" to {filename}"
        )
        self.download_media(program, filename)
        # TODO: remove fetching stations
        if program.station_id:
            station = self.get_station_from_program(program)
            artist = station.name
        else:
            artist = self.name(program)
        set_mp4_tag(filename, get_mp4_tag(artist, program))
        return filename

    @abc.abstractmethod
    def download_media(self, program: Program, filename: str) -> None: ...

    @abc.abstractmethod
    def get_default_filename(self, program: Program) -> str: ...
