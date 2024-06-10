import abc
import logging
from pathlib import Path
from typing import List, Optional, Type, TypeVar, Union

from ..program import Program
from ..station import Station
from ..tag import get_mp4_tag, set_mp4_tag

logger = logging.getLogger(__name__)

ServiceType = TypeVar("ServiceType", bound="Service")


class Service(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def service_id(cls) -> str:
        """ID to identify the service. Usually, URL of the service is
        specified.
        """
        ...

    @classmethod
    @abc.abstractmethod
    def name(cls) -> str:
        """Name of the service."""
        ...

    @classmethod
    @abc.abstractmethod
    def link_url(cls) -> str:
        """URL of the service link."""
        ...

    def __enter__(self: Type[ServiceType]) -> ServiceType:
        self.login()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def login(self) -> None:
        """It is used when you need to login to that service, such as a
        premium member.
        """
        return None

    def close(self) -> None:
        """Disconnecting a session with that service, logging out, etc."""
        return None

    def get_stations(self, **kwargs) -> List[Station]:
        """Get broadcast station data hosted by that service.

        It is used only when the service provides programs from multiple
        broadcast stations, as is the case with radiko.jp.

        Returns:
            list of `Station`: All station data hosted by the service.
        """
        return []

    def get_station_from_program(self, program: Program) -> Station:
        """Get broadcast station data for the specified program.

        It is used only when the service provides programs from multiple
        broadcast stations, as is the case with radiko.jp.

        Args:
            program (`Program`): Program that wants to get station data.

        Returns:
            `Station`: All station data hosted by the service.
        """
        if not program.station_id:
            raise RuntimeError(f"{self.service_id()} has no concept of station.")
        ret = list(
            filter(lambda x: x.station_id == program.station_id, self.get_stations())
        )
        if len(ret) == 0:
            raise ValueError(
                f"{program.station_id} is not found on {self.service_id()}"
            )
        return ret[0]

    @abc.abstractmethod
    def get_programs(self, **kwargs) -> List[Program]:
        """Get all program data provided by the service.

        Returns:
            list of `Program`: All program data provided by the service.
        """
        ...

    def download(
        self,
        program: Program,
        file_path: Optional[Union[str, Path]] = None,
        set_tag: bool = True,
        set_cover_image: bool = True,
    ) -> Path:
        """Download the media file of the specified program data.

        Args:
            program (`Program`): Program data for the media file to download.
            file_path (str or `pathlib.Path`): Downloaded media file path.
            set_tag (bool): Set tag information in the downloaded media file.
            set_cover_image (bool): Set cover image in the downloaded media
                file.

        Returns:
            str or `pathlib.Path`: Downloaded media file path.
        """
        file_path = Path(file_path or self._get_default_file_path(program))
        logger.info(
            f"Download {program.service_id} / {program.program_title} / {program.episode_title}"
            f" to {file_path}"
        )
        self._download_media(program, file_path)
        if set_tag:
            if program.station_id:
                station = self.get_station_from_program(program)
                artist = station.name
            else:
                artist = self.name()
            set_mp4_tag(file_path, get_mp4_tag(artist, program, set_cover_image))
        return file_path

    @abc.abstractmethod
    def _download_media(self, program: Program, file_path: Union[str, Path]) -> None:
        """Core method of downloading the media file.

        Args:
            program (`Program`): Program data for the media file to download.
            file_path (str or `pathlib.Path`): Downloaded media file path.
        """
        ...

    @abc.abstractmethod
    def _get_default_file_path(self, program: Program) -> Path:
        """Get the default media file path for the specified program data.

        Args:
            program (`Program`): Program data for the media file to download.

        Returns:
            `pathlib.Path`: Default media file path.
        """
        ...
