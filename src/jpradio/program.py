import copy
import dataclasses
import datetime
from typing import Any, Dict, List, Optional


@dataclasses.dataclass
class Program:
    id: int
    station_id: str
    name: str
    url: str
    description: str
    information: str
    performers: List[str]
    copyright: str
    episode_id: int
    episode_name: str
    datetime: datetime.datetime
    duration: Optional[int] = None  # unit: seconds
    ascii_name: Optional[str] = None
    guests: Optional[List[str]] = None
    image_url: Optional[str] = None
    is_video: bool = False
    raw_data: Optional[Dict[str, Any]] = None

    def __new__(cls, *args, **kwargs):
        dataclasses.dataclass(cls)
        return super().__new__(cls)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Program":
        args = copy.deepcopy(data)
        args.pop("_id", None)  # remove mongodb id
        dt = args["datetime"]
        if isinstance(dt, str):
            args["datetime"] = datetime.datetime.strptime(dt, "%Y-%m-%d %H:%M")
        return cls(**args)

    def to_dict(self, serializable: bool = False) -> Dict[str, Any]:
        dt = self.datetime.strftime("%Y-%m-%d %H:%M") if serializable else self.datetime
        return {
            "id": self.id,
            "station_id": self.station_id,
            "name": self.name,
            "url": self.url,
            "description": self.description,
            "information": self.information,
            "performers": self.performers,
            "copyright": self.copyright,
            "episode_id": self.episode_id,
            "episode_name": self.episode_name,
            "datetime": dt,
            "duration": self.duration,
            "ascii_name": self.ascii_name,
            "guests": self.guests,
            "image_url": self.image_url,
            "is_video": self.is_video,
            "raw_data": self.raw_data,
        }
