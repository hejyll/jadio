#!/usr/bin/env python3
import argparse
import logging
from pathlib import Path

import jadio

# You can check the logs by setting logging.
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s: %(message)s"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("keyword", type=str, help="Keyword to search for")
    parser.add_argument(
        "--config-path", type=Path, default=None, help="Jadio config file path"
    )
    args = parser.parse_args()
    return args


def main():
    args = parse_args()

    # Load the settings for each service from a config file.
    # If the path to the config file is not specified in load_config,
    # it will attempt to reference ${HOME}/.config/jadio/config.json.
    service_configs = jadio.load_config(args.config_path)

    # jadio class can be used to handle all platforms.
    with jadio.Jadio(service_configs) as service:
        # Get program data from all services.
        all_programs = service.get_programs(
            # Program data that cannot be downloaded,　such as unbroadcasted
            # programs, can be avoided (for Radiko service).
            only_downloadable=True,
            # Get more data, but longer run time (for Onsen service).
            more_data=False,
        )

        # Pick up program data that you want to download.
        # In this example, all programs with the specified keyword in the
        # program data
        target_programs = [
            program
            for program in all_programs
            if (
                args.keyword in program.program_title
                or args.keyword in (program.description or "")
                or args.keyword in (program.information or "")
                or args.keyword in (program.performers or [])
                or args.keyword in (program.guests or [])
            )
        ]

        for program in target_programs:
            print(f"\n====== {program.program_title} ======")

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

            # Programs can be (1) serialized in JSON format or (2) converted
            # to dict. This makes it easy to save program data in a file and
            # aggregate multiple programs.

            # (1) serialize in JSON format
            with open(str(file_path).replace(file_path.suffix, ".json"), "w") as fp:
                fp.write(program.to_json(indent=2, ensure_ascii=False))

            # (2) convert to dict
            # raw_data should be excluded from print output, as it is an
            # obstacle. It is the raw data obtained from services and is used
            # to create Program objects and download media files.
            program_dict = program.to_dict()
            program_dict.pop("raw_data")
            print(f"Downloaded program: {program_dict}")


if __name__ == "__main__":
    main()
