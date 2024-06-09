from typing import Any, Dict

from mutagen import mp4

from .program import Program
from .util import get_image


def get_mp4_tag(artist: str, program: Program) -> Dict[str, Any]:
    pub_date = program.pub_date
    day = pub_date.strftime("%Y-%m-%dT%H%M%SZ") if pub_date else None
    performers = program.performers
    if isinstance(performers, list):
        performers = ", ".join(performers)
    ret = {
        # artist
        "\xa9ART": artist,
        # album
        "\xa9alb": program.program_title,
        # title
        "\xa9nam": program.episode_title,
        # performers
        "\xa9con": performers,
        # year
        "\xa9day": day,
        # description
        "desc": program.description,
        # comment
        "\xa9cmt": program.information,
        # genre
        "\xa9gen": "Radio",
        # url
        "\xa9url": program.link_url,
        # copyright
        "cprt": program.copyright,
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
