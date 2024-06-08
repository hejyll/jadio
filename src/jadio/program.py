import datetime
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from dataclasses_json import DataClassJsonMixin


@dataclass
class Program(DataClassJsonMixin):
    id: Union[int, str]
    station_id: str
    platform_id: str
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
