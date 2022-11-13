import abc
import logging
from typing import List, Optional

from ..program import Program
from ..station import Station
from ..tag import get_mp4_tag, set_mp4_tag

logger = logging.getLogger(__name__)


class Platform(abc.ABC):
    @abc.abstractclassmethod
    @abc.abstractproperty
    def id(self) -> str:
        ...

    @abc.abstractclassmethod
    @abc.abstractproperty
    def name(self) -> str:
        ...

    @abc.abstractclassmethod
    @abc.abstractproperty
    def ascii_name(self) -> str:
        ...

    @abc.abstractclassmethod
    @abc.abstractproperty
    def url(self) -> str:
        ...

    def __enter__(self) -> "Platform":
        self.login()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def login(self) -> None:
        return None

    def close(self) -> None:
        return None

    @abc.abstractmethod
    def get_stations(self) -> List[Station]:
        ...

    def get_station_from_program(self, program: Program) -> Station:
        ret = list(filter(lambda x: x.id == program.station_id, self.get_stations()))
        if len(ret) == 0:
            raise ValueError(f"{program.station_id} is not found on {self.id}")
        return ret[0]

    @abc.abstractmethod
    def get_programs(
        self, filters: Optional[List[str]] = None, **kwargs
    ) -> List[Program]:
        ...

    def download(self, program: Program, filename: Optional[str] = None) -> str:
        filename = filename or self.get_default_filename(program)
        logger.info(
            f'Download {program.station_id} / "{program.name}" / "{program.episode_name}"'
            f" to {filename}"
        )
        self.download_media(program, filename)
        station = self.get_station_from_program(program)
        set_mp4_tag(filename, get_mp4_tag(station, program))
        return filename

    @abc.abstractmethod
    def download_media(self, program: Program, filename: str) -> None:
        ...

    @abc.abstractmethod
    def get_default_filename(self, program: Program) -> str:
        ...
