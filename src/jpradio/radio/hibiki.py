import json
import subprocess
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import requests

from ..program import Program
from ..station import Station
from ..util import check_dict_deep, to_datetime
from .base import Platform


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

    @property
    def id(self) -> str:
        return "hibiki-radio.jp"

    @property
    def name(self) -> str:
        return "響 - HiBiKi Radio Station -"

    @property
    def ascii_name(self) -> str:
        return "HiBiKi Radio Station"

    @property
    def url(self) -> str:
        return "https://hibiki-radio.jp/"

    def get_stations(self) -> List[Station]:
        ret = Station(
            id=self.id,
            platform_id=self.id,
            name=self.name,
            ascii_name=self.ascii_name,
            url=self.url,
            image_url="https://hibiki-cast.jp/wp-content/themes/hibiki/assets/images/common/logo_hibiki.png",
        )
        return [ret]

    def get_programs(self, filters: Optional[List[str]] = None) -> List[Program]:
        ret = []
        for raw_program in self._get("programs"):
            if filters and not raw_program["access_id"].lower() in filters:
                continue
            if not check_dict_deep(raw_program, ["episode", "video", "id"]):
                continue
            performers = raw_program["cast"].split(", ")
            program = Program(
                id=raw_program["id"],
                station_id=self.id,
                name=raw_program["name"],
                url=raw_program["share_url"],
                description=raw_program["description"],
                information=raw_program["onair_information"],
                performers=performers,
                copyright=raw_program["copyright"],
                episode_id=raw_program["episode"]["id"],
                episode_name=raw_program["episode"]["name"],
                datetime=to_datetime(raw_program["episode"]["updated_at"]),
                duration=raw_program["episode"]["video"]["duration"],
                ascii_name=raw_program["access_id"],
                image_url=raw_program["pc_image_url"],
                is_video=raw_program["episode"]["media_type"] != 1,
                raw_data=raw_program,
            )
            ret.append(program)
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
