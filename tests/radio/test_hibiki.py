import os
import tempfile

from jpradio import Hibiki
from jpradio.util import check_dict_deep


def test_login_without_user_info():
    with Hibiki():
        pass


def test_api_get_programs():
    with Hibiki() as radio:
        raw_program = radio._get("programs")[0]
        assert "access_id" in raw_program


def test_api_get_programs_detail():
    with Hibiki() as radio:
        raw_program = radio._get("programs")[0]
        detail = radio._get(f"programs/{raw_program['access_id']}")
        need_keys = [
            "id",
            "name",
            "description",
            "pc_image_url",
            "onair_information",
            "email",
            "copyright",
            "share_url",
            "episode",
            ["episode", "id"],
            ["episode", "name"],
            ["episode", "video", "id"],
            ["episode", "updated_at"],
            "casts",
        ]
        for key in need_keys:
            if isinstance(key, list):
                assert check_dict_deep(detail, key)
            else:
                assert key in detail


def test_get_programs():
    with Hibiki() as radio:
        programs = radio.get_programs()
        assert len(programs) > 0


def test_get_programs_with_filters():
    with Hibiki() as radio:
        target_id = radio._get("programs")[0]["access_id"]
        programs = radio.get_programs(filters=[target_id])
        assert len(programs) > 0


def test_download():
    with Hibiki() as radio, tempfile.TemporaryDirectory() as tmp_dir:
        target_id = radio._get("programs")[0]["access_id"]
        programs = radio.get_programs(filters=[target_id])
        filename = os.path.join(tmp_dir, "hoge.mp4")
        radio.download(programs[0], filename)
        assert os.path.exists(filename)
