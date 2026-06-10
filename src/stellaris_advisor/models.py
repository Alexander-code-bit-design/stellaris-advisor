from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class SaveMetadata:
    version: str | None = None
    name: str | None = None
    date: str | None = None
    player_country: int | None = None
    ironman: bool | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class SaveGame:
    metadata: SaveMetadata
    gamestate_text: str
    gamestate: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Finding:
    title: str
    severity: str
    detail: str
    recommendation: str


@dataclass(slots=True)
class AdvisorReport:
    summary: list[str]
    findings: list[Finding]
    next_steps: list[str]

