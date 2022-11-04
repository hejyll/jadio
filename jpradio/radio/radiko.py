import base64
import datetime
import re
import subprocess
from functools import lru_cache
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree

import requests

from ..program import Program
from ..util import convert_html_to_text, get_content, get_emails_from_text, to_datetime
from .base import Radio


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


class Radiko(Radio):
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

    @property
    def url(self) -> str:
        return "https://radiko.jp/"

    @property
    def name(self) -> str:
        return "radiko.jp"

    @property
    def name_en(self) -> str:
        return "radiko"

    @property
    def name_jp(self) -> str:
        return "ラジコ"

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

    @lru_cache(maxsize=256)
    def _get_program_station_weekly(self, station_id: str) -> Dict[str, str]:
        return _parse_programs_tree(
            self._get(f"v3/program/station/weekly/{station_id}.xml", "tree")
        )

    def get_programs(self, filters: Optional[List[str]] = None) -> List[Program]:
        ret = []
        for station in self._get_station_region_full():
            if filters and station["id"].lower() not in filters:
                continue
            raw_programs = self._get_program_station_weekly(station["id"])["stations"]
            raw_programs = raw_programs[0]  # len(raw_programs) == 1
            for raw_program in raw_programs["progs"]:
                ft = to_datetime(raw_program["attr"]["ft"])
                raw = {
                    "attr": raw_programs["attr"],
                    "name": raw_programs["name"],
                    "date": raw_programs["date"],
                    "progs": [raw_program],
                }
                emails = get_emails_from_text(raw_program["desc"])
                if not emails:
                    emails = get_emails_from_text(raw_program["info"])
                program_sort = emails[0].split("@")[0] if len(emails) > 1 else None
                program = Program(
                    radio=self.name,
                    title=ft.strftime("%Y/%m/%d %H:%M"),
                    program_name=raw_program["title"],
                    program_sort=program_sort,
                    program_id=raw_program["attr"]["id"],
                    program_url=raw_program["url"],
                    program_number=raw_program["attr"]["id"],
                    station_name=station["name"],
                    station_sort=station["ascii_name"],
                    station_id=station["id"],
                    station_url=station["href"],
                    performers=[raw_program["pfm"]],
                    description=convert_html_to_text(raw_program["desc"]),
                    information=convert_html_to_text(raw_program["info"]),
                    copyright="Copyright \xa9 radiko co., Ltd. All rights reserved",
                    datetime=ft,
                    duration=raw_program["attr"]["dur"] // 60,  # seconds to minutes
                    is_movie=False,
                    image_url=raw_program["img"],
                    raw=raw,
                )
                ret.append(program)
        return ret

    def download_media(self, program: Program, filename: str) -> None:
        """Support only time-shift download"""

        def to_timestamp(x: datetime.datetime) -> str:
            return x.strftime("%Y%m%d%H%M%S")

        ft = program.datetime
        to = ft + datetime.timedelta(minutes=program.duration)
        ft, to = to_timestamp(ft), to_timestamp(to)

        playlist = self._get(
            "v2/api/ts/playlist.m3u8",
            "text",
            params={"station_id": program.station_id, "l": 15, "ft": ft, "to": to},
            headers={"X-Radiko-Authtoken": self._authtoken},
        )

        url = re.findall("^https?://.+m3u8$", playlist, flags=(re.MULTILINE))[0]
        cmd = [
            "ffmpeg",
            "-y",  # overwrite
            "-loglevel",
            "quiet",
            "-headers",
            f'"X-Radiko-Authtoken:{self._authtoken}"\r\n',
            "-i",
            url,
            "-acodec",
            "copy",
            "-vn",
            "-bsf:a",
            "aac_adtstoasc",
            "-timeout",
            str(120),
            "-t",
            str(program.duration * 60),  # minutes to seconds
            filename,
        ]
        subprocess.run(cmd)
