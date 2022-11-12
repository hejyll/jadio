import base64
import datetime
import logging
import re
import subprocess
from functools import lru_cache
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree

import requests

from ..program import Program
from ..station import Station
from ..util import convert_html_to_text, get_content, get_emails_from_text, to_datetime
from .base import Platform

logger = logging.getLogger(__name__)


def _get_partialkey(offset: int, length: int) -> bytes:
    """Get partialkey for HLS protocol.

    See: https://gist.github.com/takuya/7236db2f8a52eb461968f6eacd203294
    """
    authkey = "bcd151073c03b352e1ef2fd66c32209da9ca0afa"
    ret = authkey[offset : offset + length]
    return base64.b64encode(ret.encode())


def _parse_stations_tree(tree: ElementTree.Element) -> Dict[str, Any]:
    ret = []
    for station in tree.findall(".//station"):
        data_key = [
            "id",
            "name",
            "ascii_name",
            "areafree",
            "timefree",
            "banner",
            "href",
        ]
        data = {k: station.findtext(".//{}".format(k)) for k in data_key}
        logos = []
        for logo in station.findall(".//logo"):
            logos.append(
                {
                    "attr": {
                        "width": int(logo.get("width")),
                        "height": int(logo.get("height")),
                        "align": logo.get("align"),
                    },
                    "href": logo.text,
                }
            )
        data["logos"] = logos
        ret.append(data)
    return ret


def _parse_programs_tree(tree: ElementTree.Element) -> Dict[str, Any]:
    stations = []
    for station in tree.findall(".//station"):
        progs = []
        for prog in station.findall(".//prog"):
            attr_key = ["id", "master_id", "ft", "to", "ftl", "tol", "dur"]
            data_key = [
                "title",
                "url",
                "failed_record",
                "ts_in_ng",
                "ts_out_ng",
                "desc",
                "info",
                "pfm",
                "img",
                "metas",
            ]
            data = {
                "attr": {
                    k: None if prog.get(k) == "" else int(prog.get(k)) for k in attr_key
                }
            }
            for key in data_key:
                data[key] = prog.findtext(".//{}".format(key))
            progs.append(data)
        stations.append(
            {
                "attr": {
                    "id": station.get("id"),
                },
                "name": station.findtext(".//name"),
                "date": station.findtext(".//date"),
                "progs": progs,
            }
        )
    return {
        "ttl": int(tree.findtext(".//ttl")),
        "srvtime": int(tree.findtext(".//srvtime")),
        "stations": stations,
    }


class Radiko(Platform):
    def __init__(
        self,
        mail: Optional[str] = None,
        password: Optional[str] = None,
        timeout: int = 3,
    ) -> None:
        super().__init__()
        self._mail = mail
        self._password = password
        self._timeout = timeout
        self._session = requests.session()

        self._user_info = None
        self._authtoken = None
        self._area_info = None

    @classmethod
    @property
    def id(self) -> str:
        return "radiko.jp"

    @classmethod
    @property
    def name(self) -> str:
        return "ラジコ"

    @classmethod
    @property
    def ascii_name(self) -> str:
        return "radiko"

    @classmethod
    @property
    def url(self) -> str:
        return "https://radiko.jp/"

    def _get(self, href: str, content_type: str, **kwargs) -> Any:
        url = f"https://radiko.jp/{href}"
        response = self._session.get(url, timeout=self._timeout, **kwargs)
        response.raise_for_status()
        return get_content(response, content_type=content_type)

    def _post(self, href: str, content_type: str, **kwargs) -> Any:
        url = f"https://radiko.jp/{href}"
        response = self._session.post(url, timeout=self._timeout, **kwargs)
        response.raise_for_status()
        return get_content(response, content_type=content_type)

    def login(self) -> None:
        if self._mail and self._password:
            self._user_info = self._post(
                "ap/member/webapi/member/login",
                "json",
                data={"mail": self._mail, "pass": self._password},
            )
            logger.info(f"Logged in to {self.id} as {self._mail}")

        common_headers = {
            "X-Radiko-App": "pc_html5",
            "X-Radiko-App-Version": "0.0.1",
            "X-Radiko-User": "dummy_user",
            "X-Radiko-Device": "pc",
        }

        # first authentication
        info = self._get(
            "v2/api/auth1",
            "headers",
            headers={
                "User-Agent": "curl/7.56.1",
                "Accept": "*/*",
                **common_headers,
            },
        )
        info = {k.lower(): v for k, v in info.items()}
        authtoken = info["x-radiko-authtoken"]
        keylength = int(info["x-radiko-keylength"])
        keyoffset = int(info["x-radiko-keyoffset"])
        partialkey = _get_partialkey(keyoffset, keylength)

        # second authentication
        area_info = self._get(
            "v2/api/auth2",
            "text",
            headers={
                "X-Radiko-Authtoken": authtoken,
                "X-Radiko-Partialkey": partialkey,
                **common_headers,
            },
        )

        self._authtoken = authtoken
        self._area_info = area_info.strip().split(",")

    def close(self) -> None:
        if self._user_info:
            self._post("ap/member/webapi/member/logout", "text")
        self._session.close()

    @lru_cache(maxsize=1)
    def _get_station_region_full(self) -> Dict[str, str]:
        return _parse_stations_tree(self._get("v3/station/region/full.xml", "tree"))

    @lru_cache(maxsize=1)
    def get_stations(self) -> List[Station]:
        ret = []
        for raw_station in self._get_station_region_full():
            image_url = None
            if len(raw_station["logos"]) > 0:
                image_url = raw_station["logos"][0]["href"]
            station = Station(
                id=raw_station["id"],
                platform_id=self.id,
                name=raw_station["name"],
                ascii_name=raw_station["ascii_name"],
                url=raw_station["href"],
                image_url=image_url,
            )
            ret.append(station)
        return ret

    @lru_cache(maxsize=256)
    def _get_program_station_weekly(self, station_id: str) -> Dict[str, str]:
        try:
            ret = self._get(f"v3/program/station/weekly/{station_id}.xml", "tree")
        except requests.exceptions.HTTPError:
            return {}
        except requests.exceptions.ReadTimeout:
            return {}
        return _parse_programs_tree(ret)

    def get_programs(self, filters: Optional[List[str]] = None) -> List[Program]:
        ret = []
        for station in self.get_stations():
            if filters and station.id not in filters:
                continue
            raw_programs = self._get_program_station_weekly(station.id)
            if not raw_programs:
                continue
            raw_programs = raw_programs["stations"][0]  # len(raw_programs) == 1
            for raw_program in raw_programs["progs"]:
                ft = to_datetime(raw_program["attr"]["ft"])

                # collect raw data
                raw_data = {
                    "attr": raw_programs["attr"],
                    "name": raw_programs["name"],
                    "date": raw_programs["date"],
                    "progs": [raw_program],
                }

                # get ascii_name
                emails = get_emails_from_text(raw_program["desc"])
                if not emails:
                    emails = get_emails_from_text(raw_program["info"])
                ascii_name = emails[0].split("@")[0] if len(emails) > 1 else None

                program = Program(
                    id=raw_program["attr"]["id"],
                    station_id=station.id,
                    name=raw_program["title"],
                    url=raw_program["url"],
                    description=convert_html_to_text(raw_program["desc"]),
                    information=convert_html_to_text(raw_program["info"]),
                    performers=[raw_program["pfm"]],
                    copyright="Copyright \xa9 radiko co., Ltd. All rights reserved",
                    episode_id=raw_program["attr"]["id"],
                    episode_name=ft.strftime("%Y/%m/%d %H:%M"),
                    datetime=ft,
                    duration=raw_program["attr"]["dur"],
                    ascii_name=ascii_name,
                    image_url=raw_program["img"],
                    is_video=False,
                    raw_data=raw_data,
                )
                ret.append(program)
        logger.info(f"Get {len(ret)} program(s) from {self.id}")
        return ret

    def download_media(self, program: Program, filename: str) -> None:
        """Support only time-shift download"""

        def to_timestamp(x: datetime.datetime) -> str:
            return x.strftime("%Y%m%d%H%M%S")

        ft = program.datetime
        to = ft + datetime.timedelta(seconds=program.duration)
        ft, to = to_timestamp(ft), to_timestamp(to)

        playlist = self._get(
            "v2/api/ts/playlist.m3u8",
            "text",
            params={"station_id": program.station_id, "l": 15, "ft": ft, "to": to},
            headers={"X-Radiko-Authtoken": self._authtoken},
        )

        url = re.findall("^https?://.+m3u8$", playlist, flags=(re.MULTILINE))[0]
        cmd = ["ffmpeg", "-y", "-loglevel", "quiet"]
        cmd += ["-headers", f'"X-Radiko-Authtoken:{self._authtoken}"\r\n']
        cmd += ["-i", url]
        cmd += ["-vn", "-acodec", "copy"]
        cmd += ["-bsf:a", "aac_adtstoasc"]
        cmd += ["-timeout", str(120)]
        cmd += ["-t", str(program.duration)]
        cmd += [filename]
        subprocess.run(cmd)

    def get_default_filename(self, program: Program) -> str:
        dt = program.datetime.strftime("%Y%m%d%H%M")
        return f"{program.station_id}_{dt}.mp4"
