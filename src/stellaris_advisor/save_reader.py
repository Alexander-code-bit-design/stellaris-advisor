from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Any

from .clausewitz import parse_top_level_assignments
from .models import SaveGame, SaveMetadata


META_KEYS = {"version", "name", "date", "player", "ironman"}
GAMESTATE_KEYS = {
    "date",
    "player",
    "country",
    "galactic_object",
    "planet",
    "fleet",
    "ship",
    "war",
}


class SaveReadError(RuntimeError):
    pass


def read_save(path: str | Path) -> SaveGame:
    save_path = Path(path)
    if not save_path.exists():
        raise SaveReadError(f"Save file does not exist: {save_path}")
    if not zipfile.is_zipfile(save_path):
        raise SaveReadError("Expected a Stellaris .sav zip archive")

    with zipfile.ZipFile(save_path) as archive:
        names = set(archive.namelist())
        if "meta" not in names or "gamestate" not in names:
            raise SaveReadError("Save archive must contain 'meta' and 'gamestate'")

        meta_text = archive.read("meta").decode("utf-8-sig", errors="replace")
        gamestate_text = archive.read("gamestate").decode("utf-8-sig", errors="replace")

    meta_raw = parse_top_level_assignments(meta_text, META_KEYS)
    gamestate = parse_top_level_assignments(gamestate_text, GAMESTATE_KEYS)

    metadata = SaveMetadata(
        version=_as_optional_str(meta_raw.get("version")),
        name=_as_optional_str(meta_raw.get("name")),
        date=_as_optional_str(meta_raw.get("date") or gamestate.get("date")),
        player_country=_as_optional_int(meta_raw.get("player") or gamestate.get("player")),
        ironman=_as_optional_bool(meta_raw.get("ironman")),
        raw=meta_raw,
    )
    return SaveGame(metadata=metadata, gamestate_text=gamestate_text, gamestate=gamestate)


def _as_optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _as_optional_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _as_optional_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    return str(value).lower() in {"yes", "true", "1"}

