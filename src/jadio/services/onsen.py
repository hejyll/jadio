import copy
import json
import logging
import subprocess
import time
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

from ..program import Program
from ..util import to_datetime
from .base import Service

logger = logging.getLogger(__name__)


def _get_webdriver() -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    service = ChromeService(executable_path=ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


@lru_cache(maxsize=1024)
def _get_description_from_program_web_site(
    directory_name: str, driver: webdriver.Chrome
) -> str:
    driver.get(f"https://www.onsen.ag/program/{directory_name}")
    xpath = '//*[@id="__layout"]/div/div[1]/article/div[1]/div/div/div/div[2]/div[2]/div/span'
    try:
        return driver.find_element(By.XPATH, xpath).text
    except:
        return ""


def _convert_raw_data_to_program(
    raw_data: Dict[str, Any], service_id: str, driver: Optional[webdriver.Chrome] = None
) -> Program:
    content = raw_data["contents"][0]
    directory_name = raw_data["directory_name"]
    if driver:
        description = _get_description_from_program_web_site(directory_name, driver)
    else:
        description = None
    # streaming_url:
    # https://onsen-ma3phlsvod.sslcs.cdngc.net/onsen-ma3pvod/_definst_/<yyyymm>/*.mp4/playlist.m3u
    year = content["streaming_url"].split("/")[-3][:4]
    delivery_date = None
    if year.isdigit() and content["delivery_date"]:
        delivery_date = to_datetime(f"{year}/{content['delivery_date']}")
    return Program(
        service_id=service_id,
        station_id=None,
        program_id=directory_name,
        episode_id=content["id"],
        pub_date=delivery_date,
        duration=None,
        program_title=raw_data["title"],
        episode_title=content["title"],
        description=description,
        information=raw_data["delivery_interval"],
        copyright=raw_data["copyright"],
        link_url=f"https://www.onsen.ag/program/{directory_name}",
        image_url=content.get("poster_image_url", raw_data["image"]["url"]),
        performers=[performer["name"] for performer in raw_data["performers"]],
        guests=[
            guest["name"] if isinstance(guest, dict) else guest
            for guest in content["guests"]
        ],
        is_video=content["movie"],
        raw_data=raw_data,
    )


class Onsen(Service):
    """onsen.ag service class.

    Args:
        mail (str): Premium member's email. `password` must also be set up.
            Setting this up allows you to download special programs.
        password (str): Premium member's password. `mail` must also be set up.
            Setting this up allows you to download special programs.
    """

    def __init__(
        self, mail: Optional[str] = None, password: Optional[str] = None
    ) -> None:
        super().__init__()
        self._mail = mail
        self._password = password
        self._driver = _get_webdriver()

    @classmethod
    def service_id(cls) -> str:
        return "onsen.ag"

    @classmethod
    def name(cls) -> str:
        return "インターネットラジオステーション＜音泉＞"

    @classmethod
    def link_url(cls) -> str:
        return "https://www.onsen.ag/"

    def login(self) -> None:
        if not (self._mail and self._password):
            return
        self._driver.get("https://www.onsen.ag/signin")
        login_xpath = (
            '//*[@id="__layout"]/div/div[1]/div/div/div[4]/div/div[1]/dl[1]/dd'
        )
        self._driver.find_element(
            By.XPATH, "/".join([login_xpath, "div[1]/input"])
        ).send_keys(self._mail)
        self._driver.find_element(
            By.XPATH, "/".join([login_xpath, "div[2]/input"])
        ).send_keys(self._password)
        self._driver.find_element(By.XPATH, "/".join([login_xpath, "button"])).click()
        time.sleep(1)
        logger.info(f"Logged in to {self.service_id()} as {self._mail}")

    def close(self) -> None:
        if self._driver:
            self._driver.quit()
            self._driver = None

    @lru_cache(maxsize=1)
    def _get_information(self) -> Dict[str, Any]:
        self._driver.get("https://www.onsen.ag/")
        ret = self._driver.execute_script("return JSON.stringify(window.__NUXT__);")
        return json.loads(ret)

    def get_programs(self, more_data: bool = False, **kwargs) -> List[Program]:
        """Get all program data provided by the service.

        Args:
            more_data (bool): Whether to get more data, here a `description`.
                By enabling this, a more program data can be gotten, but the
                run time will be longer.

        Returns:
            list of `Program`: All program data provided by the service.
        """
        information = self._get_information()
        ret = []
        for raw_program in information["state"]["programs"]["programs"]["all"]:
            for content in raw_program["contents"]:
                if not content.get("streaming_url", None):
                    continue
                raw_data = copy.deepcopy(raw_program)
                raw_data["contents"] = [content]
                ret.append(
                    _convert_raw_data_to_program(
                        raw_data, self.service_id(), self._driver if more_data else None
                    )
                )
        logger.info(f"Get {len(ret)} program(s) from {self.service_id()}")
        return ret

    def _download_media(self, program: Program, file_path: Union[str, Path]) -> None:
        # check required fields of program
        required_fields = ["raw_data"]
        for field in required_fields:
            if getattr(program, field) is None:
                raise ValueError(f"{field} field is required")

        cmd = ["ffmpeg", "-y", "-loglevel", "quiet"]
        cmd += ["-headers", "Referer: https://www.onsen.ag/"]
        cmd += ["-i", program.raw_data["contents"][0]["streaming_url"]]
        cmd += ["-vcodec", "copy", "-acodec", "copy"]
        cmd += ["-bsf:a", "aac_adtstoasc"]
        cmd += [str(file_path)]
        subprocess.run(cmd)

    def _get_default_file_path(self, program: Program) -> Path:
        ext = "mp4" if program.is_video else "m4a"
        return Path(f"{program.program_id}_{program.episode_id}.{ext}")
