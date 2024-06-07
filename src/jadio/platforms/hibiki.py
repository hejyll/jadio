import json
import logging
import subprocess
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests

from ..program import Program
from ..station import Station
from ..util import check_dict_deep, to_datetime
from .base import Platform

logger = logging.getLogger(__name__)


def _convert_raw_data_to_program(raw_data: Dict[str, Any], platform_id: str) -> Program:
    return Program(
        id=raw_data["id"],
        station_id=raw_data["access_id"],
        platform_id=platform_id,
        name=raw_data["name"],
        url=raw_data["share_url"],
        description=raw_data["description"],
        information=raw_data["onair_information"],
        performers=raw_data["cast"].split(", "),
        copyright=raw_data["copyright"],
        episode_id=raw_data["episode"]["id"],
        episode_name=raw_data["episode"]["name"],
        datetime=to_datetime(raw_data["episode"]["updated_at"]),
        duration=raw_data["episode"]["video"]["duration"],
        ascii_name=raw_data["access_id"],
        image_url=raw_data["pc_image_url"],
        is_video=raw_data["episode"]["media_type"] not in [1, None],
        raw_data=raw_data,
    )


class Hibiki(Platform):
    def __init__(self) -> None:
        super().__init__()
        self._session = requests.session()

    def _get(self, href: str) -> Dict[str, Any]:
        url = urljoin("https://vcms-api.hibiki-radio.jp/api/v1/", href)
        response = self._session.get(
            url, headers={"X-Requested-With": "XMLHttpRequest"}
        )
        response.raise_for_status()
        return json.loads(response.text)

    def close(self) -> None:
        self._session.close()

    @classmethod
    @property
    def id(self) -> str:
        return "hibiki-radio.jp"

    @classmethod
    @property
    def name(self) -> str:
        return "響 - HiBiKi Radio Station -"

    @classmethod
    @property
    def ascii_name(self) -> str:
        return "HiBiKi Radio Station"

    @classmethod
    @property
    def url(self) -> str:
        return "https://hibiki-radio.jp/"

    def get_stations(self) -> List[Station]:
        ret = []
        for raw_program in self._get("programs"):
            station = Station(
                id=raw_program["access_id"],
                platform_id=self.id,
                name=raw_program["name"],
                ascii_name=raw_program["access_id"],
                url=raw_program["share_url"],
                image_url=raw_program["pc_image_url"],
            )
            ret.append(station)
        return ret

    def get_programs(self, filters: Optional[List[str]] = None) -> List[Program]:
        ret = []
        for raw_program in self._get("programs"):
            if filters and not raw_program["access_id"].lower() in filters:
                continue
            if not check_dict_deep(raw_program, ["episode", "video", "id"]):
                continue
            ret.append(_convert_raw_data_to_program(raw_program, self.id))
        logger.info(f"Get {len(ret)} program(s) from {self.id}")
        return ret

    def download_media(self, program: Program, filename: str) -> None:
        video_id = program.raw_data["episode"]["video"]["id"]
        video = self._get(f"videos/play_check?video_id={video_id}")
        cmd = ["ffmpeg", "-y", "-loglevel", "quiet"]
        cmd += ["-i", video["playlist_url"]]
        cmd += ["-vcodec", "copy", "-acodec", "copy"]
        cmd += ["-bsf:a", "aac_adtstoasc"]
        cmd += [filename]
        subprocess.run(cmd)

    def get_default_filename(self, program: Program) -> str:
        ext = "mp4" if program.is_video else "m4a"
        return f"{program.ascii_name}_{program.episode_id}.{ext}"
