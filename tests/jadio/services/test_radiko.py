import tempfile
from pathlib import Path
from typing import Any, Dict, List

import pytest
import requests

from jadio import Program, Radiko
from jadio.util import check_dict_deep, get_login_info_from_config

try:
    LOGIN_INFO = get_login_info_from_config("radiko.jp")
except FileNotFoundError:
    LOGIN_INFO = None


def test_login_without_user_info():
    with Radiko() as service:
        assert not service._user_info
        assert service._authtoken
        assert len(service._area_info) == 3


@pytest.mark.skipif(not LOGIN_INFO, reason="config file is not found")
def test_login_with_user_info():
    login_info = get_login_info_from_config("radiko.jp")
    with Radiko(**login_info) as service:
        assert service._user_info["areafree"] == str(1)
        assert service._authtoken
        assert len(service._area_info) == 3


def test_login_with_user_info_error():
    with pytest.raises(requests.exceptions.HTTPError), Radiko(
        mail="hoge@gmail.com", password="xxx"
    ) as service:
        assert not service._user_info
        assert service._authtoken
        assert len(service._area_info) == 3


def _check_dict_keys(data: Dict[str, Any], need_keys: List[str]):
    for key in need_keys:
        if isinstance(key, list):
            assert check_dict_deep(data, key)
        else:
            assert key in data


def _check_station_dict(stations: List[Dict[str, Any]]):
    station = stations[0]
    need_keys = [
        "id",
        "name",
        "ascii_name",
        "areafree",
        "timefree",
        "banner",
        "href",
        "logos",
    ]
    _check_dict_keys(station, need_keys)

    logos = station["logos"]
    assert isinstance(logos, list) and len(logos) > 0

    logo = logos[0]
    need_keys = [
        ["attr", "width"],
        ["attr", "height"],
        ["attr", "align"],
        "href",
    ]
    _check_dict_keys(logo, need_keys)


def test__get_station_region_full():
    with Radiko() as service:
        stations = service._get_station_region_full()
        assert isinstance(stations, list) and len(stations) > 0
        _check_station_dict(stations)


def test__get_station_region_full():
    with Radiko() as service:
        stations = service._get_station_list_area()
        assert isinstance(stations, list) and len(stations) > 0
        _check_station_dict(stations)


def test__get_program_station_weekly():
    with Radiko() as service:
        station_id = "TBS"
        data = service._get_program_station_weekly(station_id)

        need_keys = [
            "ttl",
            "srvtime",
            "stations",
        ]
        _check_dict_keys(data, need_keys)

        stations = data["stations"]
        assert len(stations) == 1

        station = stations[0]
        need_keys = [
            ["attr", "id"],
            "name",
            "date",
            "progs",
        ]
        _check_dict_keys(station, need_keys)

        progs = station["progs"]
        assert isinstance(progs, list) and len(progs) > 0

        prog = progs[0]
        need_keys = [
            "attr",
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
        _check_dict_keys(prog, need_keys)

        attr = prog["attr"]
        need_keys = [
            "id",
            "master_id",
            "ft",
            "to",
            "ftl",
            "tol",
            "dur",
        ]
        _check_dict_keys(attr, need_keys)


def test_get_programs():
    with Radiko() as service:
        programs = service.get_programs()
        assert len(programs) > 0
        assert all(isinstance(program, Program) for program in programs)


def test_download():
    with Radiko() as service, tempfile.TemporaryDirectory() as tmp_dir:
        program = service.get_programs()[0]
        file_path = Path(tmp_dir) / "media.m4a"
        service.download(program, file_path)
        assert file_path.exists()
