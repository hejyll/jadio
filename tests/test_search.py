from datetime import datetime
from typing import List

from jpradio.program import Program
from jpradio.search import ProgramQuery, ProgramQueryList, search_programs

_programs = [
    Program(
        0,
        "TBS",
        "JUNK Mon",
        "http://test0",
        "000",
        "aaa",
        ["ijuin"],
        "",
        0,
        "2022/11/27 01:00",
        datetime(2022, 11, 27, 1, 0),
        7200,
    ),
    Program(
        1,
        "TBS",
        "JUNK Tue",
        "http://test1",
        "000",
        "aaa",
        ["ohta", "tanaka"],
        "",
        0,
        "2022/11/28 01:00",
        datetime(2022, 11, 28, 1, 0),
        7200,
    ),
    Program(
        2,
        "TBS",
        "JUNK Wed",
        "http://test2",
        "111",
        "bbb",
        ["yama"],
        "",
        0,
        "2022/11/29 01:00",
        datetime(2022, 11, 29, 1, 0),
        7200,
    ),
    Program(
        10000,
        "onsen.ag",
        "Anime part 1",
        "http://onsen.ag/program/anime",
        "222",
        "ccc",
        ["tanaka", "tsuda"],
        "",
        100,
        "2022/11/28 01:00",
        datetime(2022, 11, 30, 0, 0),
        ascii_name="anime",
        is_video=True,
    ),
]


def _checker(results: List[Program], expected_indices: List[int]) -> None:
    assert len(results) == len(expected_indices)
    for result, expected_index in zip(results, expected_indices):
        assert result == _programs[expected_index]


def test_full_match_single():
    query = ProgramQuery(program_name="JUNK Mon")
    res = search_programs(_programs, query, downloadable=False)
    _checker(res, [0])


def test_full_match_multiple():
    query = ProgramQuery(station_id="TBS")
    res = search_programs(_programs, query, downloadable=False)
    _checker(res, [0, 1, 2])


def test_regex_match():
    query = ProgramQuery(program_name={"$regex": "JUNK"})
    res = search_programs(_programs, query, downloadable=False)
    _checker(res, [0, 1, 2])


def test_and_match():
    query = ProgramQuery(program_name={"$regex": "JUNK"}, description="000")
    res = search_programs(_programs, query, downloadable=False)
    _checker(res, [0, 1])


def test_or_match_query_list():
    queries = [
        ProgramQuery(program_name="JUNK Mon"),
        ProgramQuery(program_name="Anime part 1"),
    ]
    queries = ProgramQueryList(queries)
    res = search_programs(_programs, queries, downloadable=False)
    _checker(res, [0, 3])


def test_or_match_raw_list():
    queries = [
        ProgramQuery(program_name="JUNK Mon"),
        ProgramQuery(program_name="Anime part 1"),
    ]
    res = search_programs(_programs, queries, downloadable=False)
    _checker(res, [0, 3])


def test_lt_match():
    query = ProgramQuery(program_id={"$lt": 1})
    res = search_programs(_programs, query, downloadable=False)
    _checker(res, [0])


def test_lte_match():
    query = ProgramQuery(program_id={"$lte": 1})
    res = search_programs(_programs, query, downloadable=False)
    _checker(res, [0, 1])


def test_gt_match():
    query = ProgramQuery(program_id={"$gt": 1})
    res = search_programs(_programs, query, downloadable=False)
    _checker(res, [2, 3])


def test_gte_match():
    query = ProgramQuery(program_id={"$gte": 1})
    res = search_programs(_programs, query, downloadable=False)
    _checker(res, [1, 2, 3])


def test_ne_match():
    query = ProgramQuery(datetime={"$ne": datetime(2022, 11, 28, 1, 0)})
    res = search_programs(_programs, query, downloadable=False)
    _checker(res, [0, 2, 3])


def test_in_match():
    query = ProgramQuery(performers={"$in": "tanaka"})
    res = search_programs(_programs, query, downloadable=False)
    _checker(res, [1, 3])


def test_nin_match():
    query = ProgramQuery(performers={"$nin": "tanaka"})
    res = search_programs(_programs, query, downloadable=False)
    _checker(res, [0, 2])
