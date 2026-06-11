from __future__ import annotations

from enum import Enum


class DetailLevel(str, Enum):
    SUMMARY = "summary"
    STANDARD = "standard"
    FULL = "full"
