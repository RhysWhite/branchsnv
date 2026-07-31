"""Small deterministic utilities."""

from __future__ import annotations

import hashlib
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_lines(values: list[str] | tuple[str, ...]) -> str:
    payload = "".join(f"{value}\n" for value in values).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def parse_coordinate(site_id: str) -> tuple[str, int | None]:
    """Split a terminal ``_<integer>`` coordinate without guessing earlier underscores."""

    head, separator, tail = site_id.rpartition("_")
    if separator and head and tail.isdigit():
        return head, int(tail)
    return site_id, None


def bool_text(value: bool) -> str:
    return "true" if value else "false"
