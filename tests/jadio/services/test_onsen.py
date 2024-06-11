import tempfile
from pathlib import Path

import pytest

from jadio import Onsen
from jadio.util import check_dict_deep, get_login_info_from_config

try:
    LOGIN_INFO = get_login_info_from_config("radiko.jp")
except FileNotFoundError:
    LOGIN_INFO = None


def test_login_without_user_info():
    with Onsen() as service:
        service: Onsen
        assert service._driver.name == "chrome"


@pytest.mark.skipif(not LOGIN_INFO, reason="config file is not found")
def test_login_with_user_info():
    login_info = get_login_info_from_config("onsen.ag")
    with Onsen(**login_info) as service:
        assert len(service._driver.get_cookies()) > 0


def test_login_with_user_info_error():
    with Onsen(mail="hoge@gmail.com", password="xxx") as service:
        assert len(service._driver.get_cookies()) > 0


def test__get_information():
    with Onsen() as service:
        information = service._get_information()
        assert check_dict_deep(information, ["state", "programs", "programs", "all"])
        raw = information["state"]["programs"]["programs"]["all"][0]
        need_keys = [
            "id",
            "directory_name",
            "title",
            ["image", "url"],
            "delivery_interval",
            "copyright",
            "performers",
            "guests",
            "contents",
        ]
        for key in need_keys:
            if isinstance(key, list):
                assert check_dict_deep(raw, key)
            else:
                assert key in raw
        need_keys = [
            "id",
            "title",
            "program_id",
            "delivery_date",
            "movie",
            "poster_image_url",
            "streaming_url",
            "guests",
        ]
        for key in need_keys:
            assert key in raw["contents"][0]


def test_get_programs():
    with Onsen() as service:
        programs = service.get_programs()
        assert len(programs) > 0


def test_download():
    with Onsen() as service, tempfile.TemporaryDirectory() as tmp_dir:
        program = service.get_programs()[0]
        file_path = Path(tmp_dir) / "media.m4a"
        service.download(program, file_path)
        assert file_path.exists()
