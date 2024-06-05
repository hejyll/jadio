from __future__ import annotations

import dataclasses
import datetime
import json
from typing import Any, Dict, List, Optional, TypeVar, Union

from serdescontainer import BaseContainer

from .program import Program

T = TypeVar("T")
Condition = Optional[Union[T, Dict[str, T]]]


__all__ = [
    "ProgramQuery",
    "ProgramQueryList",
    "is_downloadable",
    "search_programs",
]


@dataclasses.dataclass
class ProgramQuery(BaseContainer):
    station_id: Condition[str] = None
    program_id: Condition[int] = None
    program_name: Condition[str] = None
    program_url: Condition[str] = None
    description: Condition[str] = None
    information: Condition[str] = None
    performers: Condition[List[str]] = None
    episode_id: Condition[int] = None
    episode_name: Condition[str] = None
    datetime: Condition[datetime.datetime] = None
    duration: Condition[int] = None
    ascii_name: Condition[str] = None
    guests: Condition[List[str]] = None
    is_video: Condition[bool] = None

    def to_query(self) -> Dict[str, List[Dict[str, Any]]]:
        ret = []
        for key, condition in self.to_dict(ignore_none_fields=True).items():
            ret.append({key.replace("program_", ""): condition})
        return {"$and": ret}


class ProgramQueryList:
    def __init__(self, queries: List[ProgramQuery]) -> None:
        self._queries = queries

    def to_dict(self) -> List[Dict[str, Any]]:
        return [query.to_dict() for query in self._queries]

    def to_query(self) -> Dict[str, Dict[str, Any]]:
        return {"$or": [query.to_query() for query in self._queries]}

    def to_json(self, filename: str) -> None:
        with open(filename, "w") as fh:
            json.dump(self.to_dict(), fh, indent=2, ensure_ascii=False)

    @classmethod
    def from_json(cls, filename: str) -> "ProgramQueryList":
        with open(filename, "r") as fh:
            queries = json.load(fh)
        return cls([ProgramQuery.from_dict(query) for query in queries])


def is_downloadable(program: Program) -> bool:
    if not program.datetime:
        return False
    target_dt = program.datetime
    if program.duration:
        target_dt += datetime.timedelta(seconds=program.duration)
    return datetime.datetime.now() > target_dt


def _to_list(x: Any) -> List[Any]:
    if isinstance(x, (tuple, list)):
        return list(x)
    return [x]


def _is_match(x: Union[Any, Dict[str, Any]], query: Dict[str, Any]) -> bool:
    """pymongo like matcher."""
    ret = True
    for key, query_val in query.items():
        if key == "$and":
            ret = all(_is_match(x, query_val_i) for query_val_i in _to_list(query_val))
        elif key == "$or":
            ret = any(_is_match(x, query_val_i) for query_val_i in _to_list(query_val))
        elif key == "$regex":
            # TODO: support "^" and "$"
            if query_val[0] == "^":
                raise NotImplementedError(f"'^' is not supported")
            elif query_val[-1] == "$":
                raise NotImplementedError(f"'$' is not supported")
            ret = query_val in x
        elif key == "$lt":
            ret = x < query_val
        elif key == "$lte":
            ret = x <= query_val
        elif key == "$gt":
            ret = x > query_val
        elif key == "$gte":
            ret = x >= query_val
        elif key == "$ne":
            ret = x != query_val
        elif key == "$in":
            ret = query_val in _to_list(x)
        elif key == "$nin":
            ret = query_val not in _to_list(x)
        elif isinstance(query_val, dict):
            ret = _is_match(x[key], query_val)
        else:
            ret = x[key] == query_val
        if not ret:
            return False
    return True


def search_programs(
    programs: List[Program],
    query: Union[ProgramQuery, List[ProgramQuery], ProgramQueryList],
    downloadable: bool = True,
) -> List[Program]:
    if isinstance(query, list):
        query = ProgramQueryList(query)
    if downloadable:
        programs = filter(lambda program: is_downloadable(program), programs)
    query = query.to_query()
    programs = filter(lambda program: _is_match(program.to_dict(), query), programs)
    return list(programs)
