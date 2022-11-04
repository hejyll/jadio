import json
import subprocess
import time
from typing import Any, Dict, List, Optional

from ..program import Program
from ..util import get_webdriver, to_datetime
from .base import Radio


class Onsen(Radio):
    def __init__(
        self, mail: Optional[str] = None, password: Optional[str] = None
    ) -> None:
        super().__init__()
        self._mail = mail
        self._password = password
        self._driver = get_webdriver()

    @property
    def url(self) -> str:
        return "https://www.onsen.ag/"

    @property
    def name(self) -> str:
        return "onsen.ag"

    @property
    def name_jp(self) -> str:
        return "インターネットラジオステーション＜音泉＞"

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
        time.sleep(1)
        self._driver.find_element_by_xpath(
            "/".join([login_xpath, "div[2]/input"])
        ).send_keys(self._password)
        time.sleep(1)
        self._driver.find_element_by_xpath("/".join([login_xpath, "button"])).click()
        time.sleep(1)

    def close(self) -> None:
        if self._driver:
            self._driver.quit()
            self._driver = None

    def _get_information(self) -> Dict[str, Any]:
        self._driver.get("https://www.onsen.ag/")
        ret = self._driver.execute_script("return JSON.stringify(window.__NUXT__);")
        return json.loads(ret)

    def _get_program_summary_content(self, url: str) -> str:
        self._driver.get(url)
        ret = self._driver.find_element_by_xpath(
            '//*[@id="__layout"]/div/div[1]/article/div[1]/div/div/div/div[2]/div[2]/div/span'
        )
        return ret

    def get_programs(self, filters: Optional[List[str]] = None) -> List[Program]:
        infomation = self._get_information()
        ret = []
        for raw_program in infomation["state"]["programs"]["programs"]["all"]:
            if filters and not raw_program["directory_name"] in filters:
                continue
            program_url = (
                f"https://www.onsen.ag/program/{raw_program['directory_name']}"
            )
            performers = [p["name"] for p in raw_program["performers"]]
            info = None
            if len(raw_program["related_links"]) > 0:
                info = raw_program["related_links"][0]["link_url"]
            for content in raw_program["contents"]:
                delivery_date = to_datetime(content["delivery_date"])
                program = Program(
                    radio=self.name,
                    title=content["title"],
                    program_name=raw_program["title"],
                    program_sort=raw_program["directory_name"],
                    program_id=raw_program["id"],
                    program_url=program_url,
                    program_number=content["id"],
                    station_name=self.name_jp,
                    station_sort=self.name,
                    station_id=self.name,
                    station_url=self.url,
                    performers=performers,
                    performers_sort=raw_program["performers"][0]["id"],
                    desc=raw_program["delivery_interval"],
                    info=info,
                    copyright=raw_program["copyright"],
                    datetime=delivery_date,
                    is_movie=content["movie"],
                    image_url=content.get("poster_image_url")
                    or raw_program["image"]["url"],
                    meta={"streaming_url": content["streaming_url"]},
                )
                ret.append(program)
        return ret

    def download_media(self, program: Program, filename: str) -> None:
        cmd = [
            "ffmpeg",
            "-loglevel",
            "quiet",
            "-headers",
            "Referer: https://www.onsen.ag/",
            "-i",
            program.meta["streaming_url"],
            "-vcodec",
            "copy",
            "-acodec",
            "copy",
            "-bsf:a",
            "aac_adtstoasc",
            filename,
        ]
        subprocess.run(cmd)
