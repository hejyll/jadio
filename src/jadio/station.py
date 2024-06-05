from __future__ import annotations

import copy
import dataclasses
from typing import Any, Dict, Optional

from serdescontainer import BaseContainer


@dataclasses.dataclass
class Station(BaseContainer):
    id: str
    platform_id: str
    name: str
    ascii_name: Optional[str] = None
    url: Optional[str] = None
    image_url: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Station:
        args = copy.deepcopy(data)
        args.pop("_id", None)  # remove mongodb id
        return super().from_dict(args)
