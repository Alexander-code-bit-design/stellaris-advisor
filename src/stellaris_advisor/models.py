from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .visibility import VisibilityMode


@dataclass(slots=True)
class SaveMetadata:
    version: str | None = None
    name: str | None = None
    date: str | None = None
    player_country: int | None = None
    ironman: bool | None = None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class EmpireSummary:
    country_id: int
    name: str | None = None
    owned_planets: list[int] = field(default_factory=list)
    monthly_income: dict[str, float] = field(default_factory=dict)
    fleet_size: float | None = None
    used_naval_capacity: float | None = None
    empire_size: float | None = None
    sapient_pops: int | None = None
    military_power: float | None = None
    economy_power: float | None = None
    victory_rank: int | None = None


@dataclass(slots=True)
class SaveGame:
    metadata: SaveMetadata
    gamestate_text: str
    gamestate: dict[str, Any] = field(default_factory=dict)
    player_empire: EmpireSummary | None = None


@dataclass(slots=True)
class Finding:
    title: str
    severity: str
    detail: str
    recommendation: str


@dataclass(slots=True)
class AdvisorReport:
    visibility_mode: VisibilityMode
    summary: list[str]
    findings: list[Finding]
    next_steps: list[str]
