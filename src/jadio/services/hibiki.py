import json
import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Union
from urllib.parse import urljoin

import requests

from ..program import Program
from ..util import check_dict_deep, to_datetime
from .base import Service

logger = logging.getLogger(__name__)


def _convert_raw_data_to_program(raw_data: Dict[str, Any], service_id: str) -> Program:
    return Program(
        service_id=service_id,
        station_id=None,
        program_id=raw_data["access_id"],
        episode_id=raw_data["episode"]["id"],
        pub_date=to_datetime(raw_data["episode_updated_at"]),
        duration=raw_data["episode"]["video"]["duration"],
        program_title=raw_data["name"],
        episode_title=raw_data["episode"]["name"],
        description=raw_data["description"],
        information=raw_data["onair_information"],
        copyright=raw_data["copyright"],
        link_url=raw_data["share_url"],
        image_url=raw_data["pc_image_url"],
        performers=raw_data["cast"].split(", "),
        guests=None,
        is_video=raw_data["episode"]["media_type"] not in [1, None],
        raw_data=raw_data,
    )


class Hibiki(Service):
    """hibiki-radio.jp service class."""

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
    def service_id(cls) -> str:
        return "hibiki-radio.jp"

    @classmethod
    def name(cls) -> str:
        return "響 - HiBiKi Radio Station -"

    @classmethod
    def link_url(cls) -> str:
        return "https://hibiki-radio.jp/"

    def get_programs(self, **kwargs) -> List[Program]:
        ret = []
        for raw_program in self._get("programs"):
            if not check_dict_deep(raw_program, ["episode", "video", "id"]):
                continue
            ret.append(_convert_raw_data_to_program(raw_program, self.service_id()))
        logger.info(f"Get {len(ret)} program(s) from {self.service_id()}")
        return ret

    def _download_media(self, program: Program, file_path: Union[str, Path]) -> None:
        video_id = program.raw_data["episode"]["video"]["id"]
        video = self._get(f"videos/play_check?video_id={video_id}")
        cmd = ["ffmpeg", "-y", "-loglevel", "quiet"]
        cmd += ["-i", video["playlist_url"]]
        cmd += ["-vcodec", "copy", "-acodec", "copy"]
        cmd += ["-bsf:a", "aac_adtstoasc"]
        cmd += [str(file_path)]
        subprocess.run(cmd)

    def _get_default_file_path(self, program: Program) -> Path:
        ext = "mp4" if program.is_video else "m4a"
        return Path(f"{program.program_id}_{program.episode_id}.{ext}")
