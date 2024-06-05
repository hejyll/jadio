from __future__ import annotations

import copy
import dataclasses
import datetime
from typing import Any, Dict, List, Optional

from serdescontainer import BaseContainer

DATETIME_FORMAT = "%Y-%m-%d %H:%M"


@dataclasses.dataclass
class Program(BaseContainer):
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

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Program:
        args = copy.deepcopy(data)
        args.pop("_id", None)  # remove mongodb id
        return super().from_dict(args, datetime_format=DATETIME_FORMAT)

    def to_dict(self, serialize: bool = False) -> Dict[str, Any]:
        return super().to_dict(serialize=serialize, datetime_format=DATETIME_FORMAT)
