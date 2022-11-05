import dataclasses
from typing import Any, Dict, Optional


@dataclasses.dataclass
class Station:
    id: str
    platform_id: str
    name: str
    ascii_name: Optional[str] = None
    url: Optional[str] = None
    image_url: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Station":
        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "platform_id": self.platform_id,
            "name": self.name,
            "ascii_name": self.ascii_name,
            "url": self.url,
            "image_url": self.image_url,
        }
