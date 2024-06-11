import tempfile
from pathlib import Path

from jadio import Hibiki
from jadio.util import check_dict_deep


def test_login_without_user_info():
    with Hibiki():
        pass


def test_api_get_programs():
    with Hibiki() as service:
        raw_program = service._get("programs")[0]
        need_keys = [
            "id",
            "name",
            "description",
            "pc_image_url",
            "onair_information",
            "email",
            "copyright",
            "share_url",
            "cast",
            "episode",
            ["episode", "id"],
            ["episode", "name"],
            ["episode", "video", "id"],
            ["episode", "video", "duration"],
            ["episode", "updated_at"],
        ]
        for key in need_keys:
            if isinstance(key, list):
                assert check_dict_deep(raw_program, key)
            else:
                assert key in raw_program


def test_get_programs():
    with Hibiki() as service:
        programs = service.get_programs()
        assert len(programs) > 0


def test_download():
    with Hibiki() as service, tempfile.TemporaryDirectory() as tmp_dir:
        program = service.get_programs()[0]
        file_path = Path(tmp_dir) / "media.m4a"
        service.download(program, file_path)
        assert file_path.exists()
