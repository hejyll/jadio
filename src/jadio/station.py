from dataclasses import dataclass
from typing import Optional

from dataclasses_json import DataClassJsonMixin


@dataclass
class Station(DataClassJsonMixin):
    id: str
    platform_id: str
    name: str
    ascii_name: Optional[str] = None
    url: Optional[str] = None
    image_url: Optional[str] = None
