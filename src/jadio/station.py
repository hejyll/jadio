from dataclasses import dataclass
from typing import Optional, Union

from dataclasses_json import DataClassJsonMixin


@dataclass
class Station(DataClassJsonMixin):
    """Station data.
    It is used only when a service provides programs from multiple
    broadcasting stations, as is the case with radiko.jp.

    Attributes:
        service_id (str or int): ID to identify the service. Usually, URL of
            the service is specified.
        station_id (str or int): ID to identify the station.
        name (str): Name of the station.
        description (str): Description of the station.
        link_url (str): URL of the station link.
        image_url (str): URL of the station image.
    """

    service_id: Union[int, str]
    station_id: Union[int, str]
    name: str
    description: Optional[str] = None
    link_url: Optional[str] = None
    image_url: Optional[str] = None
