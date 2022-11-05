import copy
import json
import subprocess
import time
from functools import lru_cache
from typing import Any, Dict, List, Optional

from ..program import Program
from ..station import Station
from ..util import get_webdriver, to_datetime
from .base import Platform


class Onsen(Platform):
    def __init__(
        self, mail: Optional[str] = None, password: Optional[str] = None
    ) -> None:
        super().__init__()
        self._mail = mail
        self._password = password
        self._driver = get_webdriver()

    @property
    def id(self) -> str:
        return "onsen.ag"

    @property
    def name(self) -> str:
        return "インターネットラジオステーション＜音泉＞"

    @property
    def ascii_name(self) -> str:
        return "Internet Radio Station <Onsen>"

    @property
    def url(self) -> str:
        return "https://www.onsen.ag/"

    def login(self) -> None:
        if not (self._mail and self._password):
            return
        self._driver.get("https://www.onsen.ag/signin")
        login_xpath = (
            '//*[@id="__layout"]/div/div[1]/div/div/div[4]/div/div[1]/dl[1]/dd'
        )
        self._driver.find_element_by_xpath(
            "/".join([login_xpath, "div[1]/input"])
        ).send_keys(self._mail)
        self._driver.find_element_by_xpath(
            "/".join([login_xpath, "div[2]/input"])
        ).send_keys(self._password)
        self._driver.find_element_by_xpath("/".join([login_xpath, "button"])).click()
        time.sleep(1)

    def close(self) -> None:
        if self._driver:
            self._driver.quit()
            self._driver = None

    def get_stations(self) -> List[Station]:
        ret = Station(
            id=self.id,
            platform_id=self.id,
            name=self.name,
            ascii_name=self.ascii_name,
            url=self.url,
            image_url="https://www.onsen.ag/_nuxt/img/76b80ac.png",
        )
        return [ret]

    @lru_cache(maxsize=1)
    def _get_information(self) -> Dict[str, Any]:
        self._driver.get("https://www.onsen.ag/")
        ret = self._driver.execute_script("return JSON.stringify(window.__NUXT__);")
        return json.loads(ret)

    def get_programs(self, filters: Optional[List[str]] = None) -> List[Program]:
        information = self._get_information()
        ret = []
        for raw_program in information["state"]["programs"]["programs"]["all"]:
            if filters and not raw_program["directory_name"] in filters:
                continue
            program_url = (
                f"https://www.onsen.ag/program/{raw_program['directory_name']}"
            )
            performers = [p["name"] for p in raw_program["performers"]]
            description = None
            if len(raw_program["related_links"]) > 0:
                description = raw_program["related_links"][0]["link_url"]
            for content in raw_program["contents"]:
                raw_data = copy.deepcopy(raw_program)
                raw_data["contents"] = [content]
                delivery_date = to_datetime(content["delivery_date"])
                program = Program(
                    id=raw_program["id"],
                    station_id=self.id,
                    name=raw_program["title"],
                    url=program_url,
                    description=description,
                    information=raw_program["delivery_interval"],
                    performers=performers,
                    copyright=raw_program["copyright"],
                    episode_id=content["id"],
                    episode_name=content["title"],
                    datetime=delivery_date,
                    ascii_name=raw_program["directory_name"],
                    guests=[g["name"] for g in raw_program["guests"]],
                    image_url=content.get("poster_image_url")
                    or raw_program["image"]["url"],
                    is_video=content["movie"],
                    raw_data=raw_data,
                )
                ret.append(program)
        return ret

    def download_media(self, program: Program, filename: str) -> None:
        cmd = ["ffmpeg", "-y", "-loglevel", "quiet"]
        cmd += ["-headers", "Referer: https://www.onsen.ag/"]
        cmd += ["-i", program.raw_data["contents"][0]["streaming_url"]]
        cmd += ["-vcodec", "copy", "-acodec", "copy"]
        cmd += ["-bsf:a", "aac_adtstoasc"]
        cmd += [filename]
        subprocess.run(cmd)
