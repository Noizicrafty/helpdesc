from __future__ import annotations

import re
from datetime import datetime
from email.header import decode_header, make_header
from email.utils import getaddresses
from pathlib import Path
from typing import Iterable, Tuple


def safe_decode_header(value: str | None) -> str:
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except Exception:
        return value


def parse_sender(raw_sender: str) -> Tuple[str, str]:
    addresses = getaddresses([raw_sender or ""])
    if not addresses:
        return "Неизвестный отправитель", ""
    name, email = addresses[0]
    return safe_decode_header(name) or email or "Неизвестный отправитель", email


def ensure_directory(path: str | Path) -> Path:
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^\w\s-]", "", value, flags=re.UNICODE)
    value = re.sub(r"[-\s]+", "_", value, flags=re.UNICODE)
    return value[:80] or "category"


def parse_date_input(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d")


def format_datetime(value: datetime) -> str:
    return value.strftime("%Y-%m-%d %H:%M:%S")


def flatten(iterable: Iterable[Iterable[str]]) -> list[str]:
    result: list[str] = []
    for part in iterable:
        result.extend(part)
    return result
