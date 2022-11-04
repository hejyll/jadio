import json
import subprocess
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests

from ..program import Program
from ..util import get_webdriver, to_datetime
from .base import Radio


def _get_api_v1(href: str) -> Dict[str, Any]:
    headers = {"X-Requested-With": "XMLHttpRequest"}
    url = urljoin("https://vcms-api.hibiki-radio.jp/api/v1/", href)
    response = requests.get(url, headers=headers)
    return json.loads(response.text)


class Hibiki(Radio):
    def __init__(
        self, mail: Optional[str] = None, password: Optional[str] = None
    ) -> None:
        super().__init__()
        self._mail = mail
        self._password = password
        self._driver = get_webdriver()

    @property
    def url(self) -> str:
        return "https://hibiki-radio.jp/"

    @property
    def name(self) -> str:
        return "hibiki-radio.jp"

    @property
    def name_en(self) -> str:
        return "HiBiKi Radio Station"

    @property
    def name_jp(self) -> str:
        return "響 - HiBiKi Radio Station -"

    def get_programs(self, filters: Optional[List[str]] = None) -> List[Program]:
        ret = []
        for raw_program in _get_api_v1("programs"):
            if filters and not raw_program["access_id"].lower() in filters:
                continue
            if (
                not raw_program["episode"]
                or "video" not in raw_program["episode"]
                or "id" not in raw_program["episode"]["video"]
            ):
                continue
            detail = _get_api_v1(f"programs/{raw_program['access_id']}")
            performers = [p["name"] for p in detail["casts"]]
            program = Program(
                radio=self.name,
                title=detail["episode"]["name"],
                program_name=detail["name"],
                program_sort=detail["access_id"],
                program_id=detail["id"],
                program_url=detail["share_url"],
                program_number=detail["episode"]["id"],
                station_name=self.name_jp,
                station_sort=self.name_en,
                station_id=self.name,
                station_url=self.url,
                performers=performers,
                description=detail["description"],
                information=detail["onair_information"],
                copyright=detail["copyright"],
                datetime=to_datetime(detail["episode"]["updated_at"]),
                is_movie=False,
                image_url=detail["pc_image_url"],
                raw=detail,
            )
            ret.append(program)
        return ret

    def download_media(self, program: Program, filename: str) -> None:
        video_id = program.raw["episode"]["video"]["id"]
        video = _get_api_v1(f"videos/play_check?video_id={video_id}")
        cmd = [
            "ffmpeg",
            "-loglevel",
            "quiet",
            "-i",
            video["playlist_url"],
            "-vcodec",
            "copy",
            "-acodec",
            "copy",
            "-bsf:a",
            "aac_adtstoasc",
            filename,
        ]
        subprocess.run(cmd)
