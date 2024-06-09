import base64
import datetime
import logging
import re
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from xml.etree import ElementTree

import requests

from ..program import Program
from ..station import Station
from ..util import get_content, to_datetime
from .base import Service

logger = logging.getLogger(__name__)

RADIKO_COPYRIGHTS = "Copyright \xa9 radiko co., Ltd. All rights reserved"


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
            try:
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
                        k: None if prog.get(k) == "" else int(prog.get(k))
                        for k in attr_key
                    }
                }
                for key in data_key:
                    data[key] = prog.findtext(".//{}".format(key))
                progs.append(data)
            except ValueError:
                continue
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


def _get_program_id(station_id: str, ft: datetime.datetime) -> str:
    dow = ft.strftime("%a").lower()
    time = ft.strftime("%H%M")
    return f"{station_id.lower()}_{dow}_{time}"


def _get_information(ft: datetime.datetime, to: datetime.datetime) -> str:
    # Japanese radio broadcast stations express a day as 5:00-29:00.
    dow_ja_table = {0: "月", 1: "火", 2: "水", 3: "木", 4: "金", 5: "土", 6: "日"}
    dow_ja = dow_ja_table.get((ft - datetime.timedelta(hours=5)).weekday())
    ft_h, ft_m = ft.hour + (24 if ft.hour < 5 else 0), ft.minute
    to_h, to_m = to.hour + (24 if to.hour < 5 else 0), to.minute
    return f"{dow_ja}曜日 {ft_h:02}:{ft_m:02}〜{to_h:02}:{to_m:02}"


def _convert_raw_data_to_program(raw_data: Dict[str, Any], service_id: str) -> Program:
    raw_prog = raw_data["progs"][0]
    station_id = raw_data["attr"]["id"]
    ft = to_datetime(raw_prog["attr"]["ft"])
    to = to_datetime(raw_prog["attr"]["to"])
    return Program(
        service_id=service_id,
        station_id=station_id,
        program_id=_get_program_id(station_id, ft),
        episode_id=raw_prog["attr"]["id"],
        pub_date=ft,
        duration=raw_prog["attr"]["dur"],
        program_title=raw_prog["title"],
        episode_title=ft.strftime("%Y/%m/%d %H:%M"),
        description=raw_prog["desc"] + "<br>" + raw_prog["info"],
        information=_get_information(ft, to),
        copyright=RADIKO_COPYRIGHTS,
        link_url=raw_prog["url"],
        image_url=raw_prog["img"],
        performers=raw_prog["pfm"],
        guests=None,
        is_video=False,
        raw_data=raw_data,
    )


class Radiko(Service):
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
    def service_id(cls) -> str:
        return "radiko.jp"

    @classmethod
    def name(cls) -> str:
        return "ラジコ"

    @classmethod
    def link_url(cls) -> str:
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
            logger.info(f"Logged in to {self.service_id()} as {self._mail}")

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

    @lru_cache(maxsize=32)
    def _get_station_list_area(self) -> Dict[str, str]:
        area_id = self._area_info[0]
        return _parse_stations_tree(self._get(f"v2/station/list/{area_id}.xml", "tree"))

    @lru_cache(maxsize=1)
    def get_stations(self, **kwargs) -> List[Station]:
        ret = []
        get_station_fn = self._get_station_list_area
        if self._user_info:
            # For premium members, area-free downloading is available.
            get_station_fn = self._get_station_region_full
        for raw_station in get_station_fn():
            image_url = None
            if len(raw_station["logos"]) > 0:
                image_url = raw_station["logos"][0]["href"]
            station = Station(
                service_id=self.service_id(),
                station_id=raw_station["id"],
                name=raw_station["name"],
                description=None,
                link_url=raw_station["href"],
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

    def get_programs(self, **kwargs) -> List[Program]:
        ret = []
        for station in self.get_stations():
            raw_programs = self._get_program_station_weekly(station.station_id)
            if not raw_programs:
                continue
            raw_programs = raw_programs["stations"][0]  # len(raw_programs) == 1
            for raw_program in raw_programs["progs"]:
                raw_data = {
                    "attr": raw_programs["attr"],
                    "name": raw_programs["name"],
                    "date": raw_programs["date"],
                    "progs": [raw_program],
                }
                ret.append(_convert_raw_data_to_program(raw_data, self.service_id()))
        logger.info(f"Get {len(ret)} program(s) from {self.service_id()}")
        return ret

    def _download_media(self, program: Program, file_path: Union[str, Path]) -> None:
        """Support only time-shift download"""

        # check required fields of program
        required_fields = ["station_id", "pub_date", "duration"]
        for field in required_fields:
            if getattr(program, field) is None:
                raise ValueError(f"{field} field is required")

        def to_timestamp(x: datetime.datetime) -> str:
            return x.strftime("%Y%m%d%H%M%S")

        ft = program.pub_date
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
        cmd += [str(file_path)]
        subprocess.run(cmd)

    def _get_default_file_path(self, program: Program) -> Path:
        dt = program.pub_date.strftime("%Y-%m-%d-%H-%M")
        return Path(f"{program.program_id}_{dt}.m4a")
