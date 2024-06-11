# Jadio: Japanese Radio Downloader

jadio is a package to easily download radio programs from Japanese web radio services in Python.

The following services are currently supported:

* [radiko.jp](https://radiko.jp/)
* [onsen.ag](https://www.onsen.ag/)
* [hibiki-radio.jp](https://hibiki-radio.jp/)

## Setup

### Install dependent packages

jadio depends on the following apps:

* ffmpeg
  * It is used to download media files.
* google-chrome
  * It is used to get program data from [onsen.ag](https://www.onsen.ag/).

#### Ubuntu 22.04

```bash
sudo apt-get update
sudo apt-get install -y ffmpeg gnupg wget
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt-get update
sudo apt-get install -y ./google-chrome-stable_current_amd64.deb
rm google-chrome-stable_current_amd64.deb
```

#### macOS

```bash
brew install ffmpeg
brew install --cask google-chrome
```

### Install jadio

```bash
pip install git+https://github.com/hejyll/jadio
```

## Usage

### Typical use case

A simplified sample of [`samples/keyword_download.py`](samples/keyword_download.py) will be used as an example.

Here is a typical use case of jadio to do the following:

* Get program data from various radio broadcast services
* Pick up programs that contain specific keyword(s)
* Download media files of the programs picked up

By using `jadio.Jadio`, a class that supervises all radio service classes (`jadio.Radiko`, `jadio.Onsen` and `jadio.Hibiki`), it is possible to get program data across services.

The following sample is to find and download programs from all services that contain the keyword "鬼滅の刃" in the program title. In [`samples/keyword_download.py`](samples/keyword_download.py), other fields than `program_title` are also searched.

```python
import logging

import jadio

# You can check the logs by setting logging.
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s: %(message)s"
)

keyword = "鬼滅の刃"

# Load the settings for each service from a config file.
# If the path to the config file is not specified in load_config,
# it will attempt to reference ${HOME}/.config/jadio/config.json.
service_configs = jadio.load_config()

# jadio class can be used to handle all platforms.
with jadio.Jadio(service_configs) as service:
    # Get program data from all services.
    all_programs = service.get_programs(
        # Program data that cannot be downloaded,　such as unbroadcasted programs, can be avoided.
        only_downloadable=True,
        # Get more data, but longer run time.
        more_data=False,
    )

    # Pick up program data that you want to download.
    # In this example, all programs with the specified keyword in the program title are downloaded.
    target_programs = [
        program for program in all_programs if keyword in program.program_title
    ]

    for program in target_programs:
        print(f"\nStart: {program.program_title}")

        # If file_path is not specified in download(), the default file path
        # defined by the service is used and returned in download().
        file_path = service.download(
            program,
            # Set tag data in the downloaded media file. (default: True)
            set_tag=True,
            # Set cover image in the downloaded media file. (default: True)
            set_cover_image=True,
        )
        print(f"Save: {file_path}")

        # Programs can be (1) serialized in JSON format or (2) converted to dict.
        # This makes it easy to save program data in a file and aggregate multiple programs.

        # (1) serialize in JSON format
        with open(str(file_path).replace(file_path.suffix, ".json"), "w") as fp:
            fp.write(program.to_json(indent=2, ensure_ascii=False))

        # (2) convert to dict
        # raw_data should be excluded from print output, as it is an obstacle.
        # It is the raw data obtained from services and is used to create Program objects and download media files.
        program_dict = program.to_dict()
        program_dict.pop("raw_data")
        print(f"Downloaded program: {program_dict}")
```

<details><summary>Console output for this sample</summary><div>

```
2024-06-11 07:45:08,053 - INFO - WDM: ====== WebDriver manager ======
2024-06-11 07:45:08,333 - INFO - WDM: Get LATEST chromedriver version for google-chrome
2024-06-11 07:45:08,390 - INFO - WDM: Get LATEST chromedriver version for google-chrome
2024-06-11 07:45:08,432 - INFO - WDM: Driver [/Users/hejyll/.wdm/drivers/chromedriver/mac64/125.0.6422.141/chromedriver-mac-x64/chromedriver] found in cache
2024-06-11 07:45:13,212 - INFO - jadio.services.onsen: Logged in to onsen.ag as tmitsuishi30@gmail.com
2024-06-11 07:45:15,993 - INFO - jadio.services.radiko: Get 3412 program(s) from radiko.jp
2024-06-11 07:45:19,145 - INFO - jadio.services.onsen: Get 481 program(s) from onsen.ag
2024-06-11 07:45:20,276 - INFO - jadio.services.hibiki: Get 38 program(s) from hibiki-radio.jp

Start: テレビアニメ「鬼滅の刃」公式ラジオ『鬼滅ラヂヲ』
2024-06-11 07:45:20,279 - INFO - jadio.services.base: Download radiko.jp / テレビアニメ「鬼滅の刃」公式ラジオ『鬼滅ラヂヲ』 / 2024/06/08 19:00 to lfr_sat_1900_2024-06-08-19-00.m4a
Save: lfr_sat_1900_2024-06-08-19-00.m4a
Downloaded program: {'service_id': 'radiko.jp', 'station_id': 'LFR', 'program_id': 'lfr_sat_1900', 'episode_id': 10063611, 'pub_date': datetime.datetime(2024, 6, 8, 19, 0), 'duration': 1800, 'program_title': 'テレビアニメ「鬼滅の刃」公式ラジオ『鬼滅ラヂヲ』', 'episode_title': '2024/06/08 19:00', 'description': '新シリーズ「柱稽古編」の放送開始に合わせて、テレビアニメ「鬼滅の刃」公式ラジオ『鬼滅ラヂヲ』をレギュラー放送。テレビアニメ「鬼滅の刃」の魅力を届けていきます。<br>番組ホームページは<a href="https://www.1242.com/kimetsu/">こちら</a><br><br>twitterハッシュタグは「<a href="http://twitter.com/search?q=%23%E9%AC%BC%E6%BB%85%E3%83%A9%E3%83%82%E3%83%B2">#鬼滅ラヂヲ</a>」', 'information': '土曜日 19:00〜19:30', 'copyright': 'Copyright © radiko co., Ltd. All rights reserved', 'link_url': 'https://www.1242.com/kimetsu/', 'image_url': 'https://program-static.cf.radiko.jp/o8tefk6a3a.jpg', 'performers': '', 'guests': None, 'is_video': False}

Start: テレビアニメ「鬼滅の刃」公式ラジオ　鬼滅ラヂヲ　WEB版
2024-06-11 07:45:30,827 - INFO - jadio.services.base: Download onsen.ag / テレビアニメ「鬼滅の刃」公式ラジオ　鬼滅ラヂヲ　WEB版 / 第83回 to kimetsu_18474.m4a
Save: kimetsu_18474.m4a
Downloaded program: {'service_id': 'onsen.ag', 'station_id': None, 'program_id': 'kimetsu', 'episode_id': 18474, 'pub_date': datetime.datetime(2024, 6, 4, 0, 0), 'duration': None, 'program_title': 'テレビアニメ「鬼滅の刃」公式ラジオ\u3000鬼滅ラヂヲ\u3000WEB版', 'episode_title': '第83回', 'description': None, 'information': None, 'copyright': 'ⓒ吾峠呼世晴／集英社・アニプレックス・ufotable', 'link_url': 'https://www.onsen.ag/program/kimetsu', 'image_url': 'https://d3bzklg4lms4gh.cloudfront.net/program_info/image/default/production/4f/55/70a0eb23c92c177df632c2c6b6af42f29152/image?v=1717486197', 'performers': ['櫻井孝宏', '小西克幸'], 'guests': [], 'is_video': False}
```

**NOTE**

* Logs about WebDriver manager are caused by `Onsen` import

</div></details>

#### `configs` argument of `jadio.Jadio`

The `configs` argument of `jadio.Jadio` is a `dict` variable (key is `Service.service_id()`) that defines the arguments of each service class.

e.g. login data for premium members on each service

```python
service_configs = {
    "onsen.ag": {"mail": "xxx@yyy.com", "password": "passw0rd"},
    "radiko.jp": {"mail": "xxx@yyy.com", "password": "passw0rd"},
}
```

See docstring in the file under [`src/jadio/services/`](src/jadio/services/) for details of arguments for each service class.

### Simple use case for radiko.jp

Each service class (`jadio.Radiko`, `jadio.Onsen` and `jadio.Hibiki`) can be used independently without using `jadio.Jadio`.

Especially in the case of `jadio.Radiko`, programs can be downloaded as long as the `station_id`, `pub_date`, and `duration` of the `Program` are set, so it can be used simply as shown in the sample below.

```python
import datetime

import jadio

with jadio.Radiko() as service:
    program = jadio.Program(
        station_id="TBS", pub_date=datetime.datetime(2024, 6, 4, 1, 0), duration=2 * 60 * 60
    )
    service.download(program, "junk_ijuin.m4a")
```

## API

See docstring in the Python file under [`src/jadio/`](src/jadio).

## Data fields

To find the desired program or station, you can use `Program` and `Station`. The following shows what kind of data these consist of so that you can create search queries.

### [`Program`](src/jadio/program.py)

| Field name | Type | Description | `Radiko.get_programs()` | `Onsen.get_programs()` | `Hibiki.get_programs()` |
| -- | -- | -- | -- | -- | -- |
| `service_id` | str or int | ID to identify the service. | `"radiko.jp"` | `"onsen.ag"` | `"hibiki-radio.jp"` |
| `station_id` | str or int | ID to identify the station. | `raw_data.attr.id` | N/A | N/A |
| `program_id` | str or int | ID to identify the program. | construct from `raw_data.attr.id` and `raw_data.progs.*.attr.ft`<br/>(`<station-id>-<day-of-week>-<start-time>`) | `raw_data.directory_name` | `raw_data.access_id` |
| `episode_id` | str or int | ID to identify the program episode. | `raw_data.progs.*.attr.id` | `raw_data.contents.*.id` | `raw_data.episode.id` |
| `pub_date` | datetime | Date and time of public launch. | `raw_data.progs.*.attr.ft` | construct from `raw_data.streaming_url` and `raw_data.delivery_date` | `raw_data.episode_updated_at` |
| `duration` | int or float | Duration of the program episode [seconds]. | `raw_data.progs.*.attr.dur` | N/A | `raw_data.episode.video.duration` |
| `program_title` | str | Title of the program. | `raw_data.progs.*.title` | `raw_data.title` | `raw_data.name` |
| `episode_title` | str | Title of the program episode. | construct from `raw_data.progs.*.attr.ft` | `raw_data.contents.*.title` | `raw_data.episode.name` |
| `description` | str | Description of the program. | `raw_data.progs.*.desc` + `raw_data.progs.*.info` | extract from `https://www.onsen.ag/program/<directory_name>` | `raw_data.description` |
| `information` | str | Information of the program. | construct from `raw_data.progs.*.attr.{ft,to}` | `raw_data.delivery_interval` | `raw_data.onair_information` |
| `copyright` | str | Copyright of the program. | extract from [radiko.jp](https://radiko.jp) | `raw_data.copyright` | `raw_data.copyright` |
| `link_url` | str | URL of the program link. | `raw_data.progs.*.url` | construct from `raw_data.directory_name`<br/>(`https://www.onsen.ag/program/<directory_name>`) | `raw_data.share_url` |
| `image_url` | str | URL of the program image. | `raw_data.progs.*.img` | `raw_data.contents.*.poster_image_url` | `raw_data.pc_image_url` |
| `performers` | list of str | Performers in the program. | `raw_data.progs.*.pfm` | `raw_data.performers.*.name` | `raw_data.cast` |
| `guests` | list of str | Guests in the program. | N/A | `raw_data.guests.*.name` | N/A |
| `is_video` | bool | Whether the program episode is a video. | always false | `raw_data.contents.*.movie` | `raw_data.episode.media_type` (audio: null or 1, video: others) |
| `raw_data` | dict | Raw data of the program. | extract from `https://radiko.jp/v3/program/station/weekly/<station_id>.xml` | extract from [onsen.ag](https://www.onsen.ag/) | extract from `https://vcms-api.hibiki-radio.jp/api/v1/programs` |

**NOTE**

* Difference between program and episode: program indicates the radio program itself, while episode indicates the date and time of its release and how many times it has been broadcast.
* Difference between `description` and `information`: The difference between the two is ambiguous, but `information` often includes a (regular) publication date and time.
* You can tag media files by setting the `set_tag` and `set_cover_image` arguments of `Service.download()` to True. The tag data is generated from `Program`. See [`tag.py`](src/jadio/tag.py) for details.

### [`Station`](src/jadio/station.py)

It is used only when a service provides programs from multiple broadcasting stations, as is the case with radiko.jp.

| Field name | Type | Description |
| -- | -- | -- |
| `service_id` | int or str | ID to identify the service. |
| `station_id` | int or str | ID to identify the station. |
| `name` | str | Name of the station. |
| `description` | str | Description of the station. |
| `link_url` | str | URL of the station link. |
| `image_url` | str | URL of the station image. |

## License

These codes are licensed under MIT License.
