import copy
import dataclasses
import datetime
from typing import Any, Dict, List, Optional, Union

from .util import get_image


@dataclasses.dataclass
class Program:
    radio: str
    title: str
    program_name: str
    program_sort: str
    program_id: Union[int, str]
    program_url: str
    program_number: int
    station_name: str
    station_sort: str
    station_id: Union[int, str]
    station_url: str
    performers: List[str]
    description: str
    information: str
    copyright: str
    datetime: datetime.datetime
    duration: Optional[int] = None  # unit: minutes
    is_movie: bool = False
    image_url: Optional[str] = None
    raw: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Program":
        args = copy.deepcopy(data)
        dt = args["datetime"]
        if isinstance(dt, str):
            args["datetime"] = datetime.datetime.strptime(dt, "%Y-%m-%d %H:%M")
        return cls(**args)

    def to_dict(self, serializable: bool = False) -> Dict[str, Any]:
        dt = self.datetime.strftime("%Y-%m-%d %H:%M") if serializable else self.datetime
        return {
            "radio": self.radio,
            "title": self.title,
            "program_name": self.program_name,
            "program_sort": self.program_sort,
            "program_id": self.program_id,
            "program_url": self.program_url,
            "program_number": self.program_number,
            "station_name": self.station_name,
            "station_sort": self.station_sort,
            "station_id": self.station_id,
            "station_url": self.station_url,
            "performers": self.performers,
            "description": self.description,
            "information": self.information,
            "copyright": self.copyright,
            "datetime": dt,
            "duration": self.duration,
            "is_movie": self.is_movie,
            "image_url": self.image_url,
            "raw": self.raw,
        }

    def get_tag(self) -> Dict[str, Any]:
        ret = {
            # Artist
            "\xa9ART": self.station_name,
            "soar": self.station_sort,
            # Album artist
            "aART": ", ".join(self.performers),
            # Album
            "\xa9alb": self.program_name,
            # Title
            "\xa9nam": self.title,
            "sonm": self.datetime.strftime("%Y-%m-%d %H:%M"),
            # Year
            "\xa9day": self.datetime.strftime("%Y-%m-%d"),
            # Commnet
            "\xa9cmt": self.information,
            # Genre
            "\xa9gen": "Radio",
            # Podcasts fieldsppp
            "pcst": False,
            "purl": self.program_url,
            "desc": self.description,
            "purd": self.datetime.strftime("%Y-%m-%d %H:%M:%S"),
            "cprt": self.copyright,
        }
        if self.image_url:
            covr = get_image(self.image_url)
            if covr:
                ret["covr"] = [covr]
        return ret