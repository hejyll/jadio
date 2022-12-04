import os
import tempfile

from jadio import Onsen
from jadio.util import check_dict_deep, get_login_info_from_config


def test_login_without_user_info():
    with Onsen() as radio:
        assert radio._driver.name == "chrome"


def test_login_with_user_info():
    login_info = get_login_info_from_config("radiko.jp")
    with Onsen(**login_info) as radio:
        assert len(radio._driver.get_cookies()) > 0


def test_login_with_user_info_error():
    with Onsen(mail="hoge@gmail.com", password="xxx") as radio:
        assert len(radio._driver.get_cookies()) > 0


def test_get_information():
    with Onsen() as radio:
        information = radio._get_information()
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
    with Onsen() as radio:
        programs = radio.get_programs()
        assert len(programs) > 0


def test_get_programs_with_filters():
    with Onsen() as radio:
        information = radio._get_information()
        raw = information["state"]["programs"]["programs"]["all"][0]
        target_id = raw["directory_name"]
        programs = radio.get_programs(filters=[target_id])
        for program in programs:
            assert program.ascii_name == target_id


def test_download():
    with Onsen() as radio, tempfile.TemporaryDirectory() as tmp_dir:
        programs = radio.get_programs()
        filename = os.path.join(tmp_dir, "hoge.mp4")
        radio.download(programs[0], filename)
        assert os.path.exists(filename)
