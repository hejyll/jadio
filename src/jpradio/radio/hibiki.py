import json
import subprocess
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests

from ..program import Program
from ..util import check_dict_deep, to_datetime
from .base import Radio


class Hibiki(Radio):
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
        for raw_program in self._get("programs"):
            if filters and not raw_program["access_id"].lower() in filters:
                continue
            if not check_dict_deep(raw_program, ["episode", "video", "id"]):
                continue
            detail = self._get(f"programs/{raw_program['access_id']}")
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
        video = self._get(f"videos/play_check?video_id={video_id}")
        cmd = ["ffmpeg", "-y", "-loglevel", "quiet"]
        cmd += ["-i", video["playlist_url"]]
        cmd += ["-vcodec", "copy", "-acodec", "copy"]
        cmd += ["-bsf:a", "aac_adtstoasc"]
        cmd += [filename]
        subprocess.run(cmd)
