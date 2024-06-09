import datetime as dt
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from dataclasses_json import DataClassJsonMixin


@dataclass
class Program(DataClassJsonMixin):
    """Program data.

    Attributes:
        service_id (str or int): ID to identify the service. Usually, URL of
            the service is specified.
        station_id (str or int): ID to identify the station. It is used only
            when a service provides programs from multiple broadcasting
            stations, as is the case with radiko.jp.
        program_id (str or int): ID to identify the program.
        episode_id (str or int): ID to identify the program episode.
        pub_date (datetime): Date and time of public launch.
        duration (int or float): Duration of the program episode [seconds].
        program_title (str): Title of the program.
        episode_title (str): Title of the program episode.
        description (str): Description of the program.
        information (str): Information of the program. Basically, the
            information will include the date and time of the broadcast or
            release.
        copyright (str): Copyright of the program.
        link_url (str): URL of the program link.
        image_url (str): URL of the program image.
        performers (list of str): Performers in the program.
        guests (list of str): Guests in the program.
        is_video (bool): Whether the program episode is a video.
        raw_data (dict): Raw data of the program.
    """

    service_id: Optional[Union[int, str]] = None
    station_id: Optional[Union[int, str]] = None
    program_id: Optional[Union[int, str]] = None
    episode_id: Optional[Union[int, str]] = None
    pub_date: Optional[dt.datetime] = None
    duration: Optional[Union[int, float]] = None
    program_title: Optional[str] = None
    episode_title: Optional[str] = None
    description: Optional[str] = None
    information: Optional[str] = None
    copyright: Optional[str] = None
    link_url: Optional[str] = None
    image_url: Optional[str] = None
    performers: Optional[Union[str, List[str]]] = None
    guests: Optional[Union[str, List[str]]] = None
    is_video: bool = False
    raw_data: Optional[Dict[str, Any]] = None
