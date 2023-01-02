# Jadio: Japanese Radio Downloader

jadio is a package for downloading programs from Japanese web radio platforms.

## Installation

```console
$ pip install git+https://github.com/hejyll/jadio
```

## Usage

```python
"""sample.py"""
import logging

import jadio

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Login information for premium members on each platform
configs = {
    "hibiki-radio.jp": {},
    "onsen.ag": {"mail": None, "password": None},
    "radiko.jp": {"mail": None, "password": None},
}

# jadio class can be used to handle all platforms.
with jadio.Jadio(configs) as platform:
    # Get program information from all platforms.
    programs = platform.get_programs()

    # Search for programs with specified conditions in pymongo-like query.
    query = jadio.ProgramQuery(
        station_id="TBS",
        program_name={"$regex": "JUNK"},
    )
    programs = jadio.search_programs(programs, query)

    # Download the searched programs.
    for program in programs:
        # If filename is not specified in download(),
        # the default filename defined by the platform
        # is used and returned in download().
        filename = platform.download(program)
        print(filename)
```

```console
$ python3 ./sample.py
2022-11-27 18:33:10,105 - WDM - INFO - ====== WebDriver manager ======
2022-11-27 18:33:10,184 - WDM - INFO - Get LATEST chromedriver version for google-chrome 107.0.5304
2022-11-27 18:33:10,374 - WDM - INFO - Driver [/Users/hejyll/.wdm/drivers/chromedriver/mac64/107.0.5304/chromedriver] found in cache
2022-11-27 18:34:32,214 - jadio.platforms.radiko - INFO - Get 60321 program(s) from radiko.jp
2022-11-27 18:34:34,423 - jadio.platforms.onsen - INFO - Get 357 program(s) from onsen.ag
2022-11-27 18:34:37,434 - jadio.platforms.hibiki - INFO - Get 44 program(s) from hibiki-radio.jp
2022-11-27 18:34:37,683 - jadio.platforms.base - INFO - Download TBS / "JUNK 伊集院光・深夜の馬鹿力" / "2022/11/22 01:00" to TBS_202211220100.m4a
TBS_202211220100.m4a
2022-11-27 18:35:07,828 - jadio.platforms.base - INFO - Download TBS / "JUNK 爆笑問題カーボーイ" / "2022/11/23 01:00" to TBS_202211230100.m4a
TBS_202211230100.m4a
2022-11-27 18:35:38,064 - jadio.platforms.base - INFO - Download TBS / "JUNK 山里亮太の不毛な議論" / "2022/11/24 01:00" to TBS_202211240100.m4a
TBS_202211240100.m4a
2022-11-27 18:36:08,363 - jadio.platforms.base - INFO - Download TBS / "JUNK おぎやはぎのメガネびいき" / "2022/11/25 01:00" to TBS_202211250100.m4a
TBS_202211250100.m4a
2022-11-27 18:36:37,791 - jadio.platforms.base - INFO - Download TBS / "JUNK バナナマンのバナナムーンGOLD" / "2022/11/26 01:00" to TBS_202211260100.m4a
TBS_202211260100.m4a
```

## License

These codes are licensed under CC0.

[![CC0](http://i.creativecommons.org/p/zero/1.0/88x31.png "CC0")](http://creativecommons.org/publicdomain/zero/1.0/deed.ja)
