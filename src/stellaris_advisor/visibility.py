from __future__ import annotations

from enum import Enum


class VisibilityMode(str, Enum):
    PLAYER_VISIBLE = "player_visible"
    DEBUG = "debug"
    OMNISCIENT = "omniscient"


def parse_visibility_mode(value: str) -> VisibilityMode:
    try:
        return VisibilityMode(value)
    except ValueError as exc:
        allowed = ", ".join(mode.value for mode in VisibilityMode)
        raise ValueError(f"Unknown visibility mode '{value}'. Expected one of: {allowed}") from exc
