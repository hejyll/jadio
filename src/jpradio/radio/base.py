import abc
from typing import List, Optional

from mutagen import mp4

from ..program import Program


class Radio(abc.ABC):
    @abc.abstractproperty
    def url(self) -> str:
        ...

    @abc.abstractproperty
    def name(self) -> str:
        ...

    @abc.abstractproperty
    def name_en(self) -> str:
        ...

    @abc.abstractproperty
    def name_jp(self) -> str:
        ...

    def __enter__(self) -> "Radio":
        self.login()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def login(self) -> None:
        return None

    def close(self) -> None:
        return None

    @abc.abstractmethod
    def get_programs(
        self, filters: Optional[List[str]] = None, **kwargs
    ) -> List[Program]:
        ...

    def download(self, program: Program, filename: str, set_tag: bool = True) -> None:
        self.download_media(program, filename)
        if set_tag:
            tag = program.get_tag()
            media = mp4.MP4(filename)
            for key, value in tag.items():
                if value is not None:
                    media[key] = value
            media.save()

    @abc.abstractmethod
    def download_media(self, program: Program, filename: str) -> None:
        ...
