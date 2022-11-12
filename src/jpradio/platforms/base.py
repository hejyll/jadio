import abc
import logging
from typing import Any, Dict, List, Optional

from mutagen import mp4

from ..program import Program
from ..station import Station
from ..util import get_image

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

    def _get_mp4_tag(self, station: Station, program: Program) -> Dict[str, Any]:
        ret = {
            # artist
            "\xa9ART": station.name,
            # album
            "\xa9alb": program.name,
            # title
            "\xa9nam": program.episode_name,
            # performers
            "\xa9con": ", ".join(program.performers),
            # year
            "\xa9day": program.datetime.strftime("%Y-%m-%dT%H%M%SZ"),
            # description
            "desc": program.description,
            # comment
            "\xa9cmt": program.information,
            # genre
            "\xa9gen": "Radio",
            # url
            "\xa9url": program.url,
            # copyright
            "cprt": program.copyright,
            # sort artist
            "soar": station.ascii_name,
            # sort album
            "soal": program.ascii_name,
            # episode id
            "tven": str(program.episode_id),
        }
        if program.image_url:
            covr = get_image(program.image_url)
            if covr:
                ret["covr"] = [covr]
        return ret

    def set_mp4_tag(self, program: Program, filename: str) -> None:
        station = self.get_station_from_program(program)
        media = mp4.MP4(filename)
        for key, value in self._get_mp4_tag(station, program).items():
            if value is not None:
                media[key] = value
        media.save()

    def download(self, program: Program, filename: str) -> None:
        logger.info(
            f'Download {program.station_id} / "{program.name}" / "{program.episode_name}"'
            f" to {filename}"
        )
        self.download_media(program, filename)
        self.set_mp4_tag(program, filename)

    @abc.abstractmethod
    def download_media(self, program: Program, filename: str) -> None:
        ...

    @abc.abstractmethod
    def get_default_filename(self, program: Program) -> str:
        ...
