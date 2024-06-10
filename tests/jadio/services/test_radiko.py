import os
import tempfile

import pytest
import requests

from jadio import Radiko
from jadio.util import get_login_info_from_config


def test_login_without_user_info():
    with Radiko() as radio:
        assert not radio._user_info
        assert radio._authtoken
        assert len(radio._area_info) == 3


def test_login_with_user_info():
    login_info = get_login_info_from_config("radiko.jp")
    with Radiko(**login_info) as radio:
        assert radio._user_info["areafree"] == str(1)
        assert radio._authtoken
        assert len(radio._area_info) == 3


def test_login_with_user_info_error():
    with pytest.raises(requests.exceptions.HTTPError), Radiko(
        mail="hoge@gmail.com", password="xxx"
    ) as radio:
        assert not radio._user_info
        assert radio._authtoken
        assert len(radio._area_info) == 3


def test_get_station_region_full():
    with Radiko() as radio:
        stations = radio._get_station_region_full()
        assert len(stations) > 0


def test_get_programs():
    with Radiko() as radio:
        programs = radio.get_programs()
        assert len(programs) > 0


def test_get_programs_with_filters():
    with Radiko() as radio:
        stations = radio._get_station_region_full()
        target_id = stations[0]["id"]
        programs = radio.get_programs(filters=[target_id])
        for program in programs:
            assert program.station_id == target_id


def test_download():
    with Radiko() as radio, tempfile.TemporaryDirectory() as tmp_dir:
        target_id = "TBS"
        programs = radio.get_programs(filters=[target_id])
        filename = os.path.join(tmp_dir, "hoge.mp4")
        radio.download(programs[0], filename)
        assert os.path.exists(filename)
