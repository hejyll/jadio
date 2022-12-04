from typing import Any, Dict

from mutagen import mp4

from .program import Program
from .station import Station
from .util import get_image


def get_mp4_tag(station: Station, program: Program) -> Dict[str, Any]:
    day = program.datetime.strftime("%Y-%m-%dT%H%M%SZ") if program.datetime else None
    ret = {
        # artist
        "\xa9ART": station.name,
        # album
        "\xa9alb": program.name,
        # title
        "\xa9nam": program.episode_name,
        # performers
        "\xa9con": ", ".join(program.performers),
        # year
        "\xa9day": day,
        # description
        "desc": program.description,
        # comment
        "\xa9cmt": program.information,
        # genre
        "\xa9gen": "Radio",
        # url
        "\xa9url": program.url,
        # copyright
        "cprt": program.copyright,
        # sort artist
        "soar": station.ascii_name,
        # sort album
        "soal": program.ascii_name,
        # episode id
        "tven": str(program.episode_id),
    }
    if program.image_url:
        covr = get_image(program.image_url)
        if covr:
            ret["covr"] = [covr]
    return ret


def set_mp4_tag(filename: str, tag: Dict[str, Any]) -> None:
    media = mp4.MP4(filename)
    for key, value in tag.items():
        if value is not None:
            media[key] = value
    media.save()
