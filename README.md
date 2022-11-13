# Japanese Radio Downloader

## Usage

```python
import logging
import jpradio

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Login information for premium members on each platform
configs = {
    "hibiki-radio.jp": {},
    "onsen.ag": {"mail": None, "password": None},
    "radiko.jp": {"mail": None, "password": None},
}

# Jpradio class can be used to handle all platforms.
with jpradio.Jpradio(configs) as platform:
    # Get program information from all platforms.
    programs = platform.get_programs()

    # Search for programs with specified conditions in a query
    query = {
        "station_id": "TBS",
        "name": "JUNK 伊集院光・深夜の馬鹿力",
    }
    programs = jpradio.search_programs(programs, query)

    # Download the searched programs.
    for program in programs:
        # If filename is not specified in download(),
        # the default filename defined by the platform
        # is used and returned in download().
        filename = platform.download(program)
        print(filename)
```

## License

These codes are licensed under CC0.

[![CC0](http://i.creativecommons.org/p/zero/1.0/88x31.png "CC0")](http://creativecommons.org/publicdomain/zero/1.0/deed.ja)
