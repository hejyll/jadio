import datetime
import json
import re
from typing import Any, Dict, List, Optional, Union
from xml.etree import ElementTree

import html2text
import requests
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager


def get_webdriver() -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    return webdriver.Chrome(ChromeDriverManager().install(), options=options)


def extract_numbers(x: str) -> Optional[int]:
    """Extract numbers from string.

    Args:
        x (str): input string.

    Returns:
        int: number.
    """
    ret = "".join(c for c in x if c.isdigit())
    return int(ret) if len(ret) else None


def to_datetime(dt: Union[int, str, None]) -> datetime.datetime:
    """Convert to datetime.

    Args:
        dt (:class:`datetime.datetime`, str or int): input datetime data.

    Returns:
        :class:`datetime.datetime`: datetime.
    """
    now = datetime.datetime.now()
    if dt is None:
        dt = now
    if isinstance(dt, int):
        dt = str(dt)
    if isinstance(dt, str):
        if dt == "now":
            dt = now
        elif dt == "today":
            dt = datetime.datetime(now.year, now.month, now.day)
        elif dt == "weekly":
            dt = datetime.datetime(now.year, now.month, now.day)
        elif not dt.isdecimal():
            dt = dt.replace("/", "-")
            hms_fmt = {2: "%H:%M:%S", 1: "%H:%M"}.get(dt.count(":"), "")
            ymd_fmt = "%y-%m-%d"
            if dt.count("-") > 0:
                if dt.count("-") == 2 and len(dt.split("-")[0]) == 4:
                    ymd_fmt = "%Y-%m-%d"
                elif dt.count("-") == 1:
                    dt = now.strftime("%y-") + dt
            else:
                dt = now.strftime("%y-%m-%d ") + dt
            fmt = " ".join([ymd_fmt, hms_fmt])
            fmt = fmt[:-1] if fmt[-1] == " " else fmt
            dt = datetime.datetime.strptime(dt, fmt)
        else:
            dt = str(extract_numbers(dt))
            fmts = {
                14: ["%Y%m%d%H%M%S"],
                12: ["%Y%m%d%H%M", "%y%m%d%H%M%S"],
                10: ["%y%m%d%H%M", "%m%d%H%M%S"],
                8: ["%Y%m%d", "%m%d%H%M"],
                6: ["%y%m%d"],
                4: ["%m%d"],
            }.get(len(dt), None)
            if fmts is None:
                raise ValueError(f"unknown datetime format: {dt}")
            for fmt in fmts:
                try:
                    dt = datetime.datetime.strptime(dt, fmt)
                    break
                except ValueError:
                    continue
            if isinstance(dt, str):
                raise ValueError(f"{dt} cannot be converted to datetime")
            if dt.year == 1900:
                dt = dt.replace(year=now.year)
    return dt


def _remove_callback(text: str) -> str:
    if text == "callback();":
        return None
    return text[9:-3] if text[:8] == "callback" else text


def _parse_json(text: str) -> Dict[str, str]:
    text = _remove_callback(text)
    return json.loads(text) if text else None


def _parse_qs(text: str, separator: str = "\r\n") -> Dict[str, str]:
    ret = {}
    for key_value in text.split(separator):
        if len(key_value) == 0:
            break
        key, value = key_value.split("=")
        ret[key] = value
    return ret


def _convert_content(content: bytes, content_type: str = "text") -> Dict[str, str]:
    if content_type == "byte":
        ret = content
    else:
        ret = {
            "text": lambda x: x,
            "json": _parse_json,
            "tree": ElementTree.fromstring,
            "qs": _parse_qs,
        }.get(content_type, lambda x: None)(content.decode("utf-8"))
    return ret


def get_content(response: requests.Response, content_type: str = "text") -> Any:
    ret = {
        "raw": response,
        "headers": response.headers,
    }.get(content_type, _convert_content(response.content, content_type))
    if ret is None:
        raise ValueError(f"{content_type} is not supported content_type")
    return ret


def get_image(url: str) -> Optional[bytes]:
    """Get image data.

    Args:
        url (str): target url.

    Returns:
        bytes: downloaded image data.
    """
    response = requests.get(url)
    response.raise_for_status()
    return get_content(response, content_type="byte")


def convert_html_to_text(x: str) -> str:
    if not x:
        return x
    return html2text.html2text(x)


def get_emails_from_text(x: str) -> List[str]:
    return re.findall(r"[\w.+-]+@[\w-]+\.[\w.-]+", x)
