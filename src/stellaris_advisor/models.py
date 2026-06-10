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
class LeaderSummary:
    leader_id: int
    name: str | None = None
    leader_class: str | None = None
    level: int | None = None
    age: int | None = None
    gender: str | None = None
    ethic: str | None = None
    job: str | None = None
    traits: list[str] = field(default_factory=list)
    location_type: str | None = None
    location_id: int | None = None
    council_position_id: int | None = None


@dataclass(slots=True)
class PlanetSummary:
    planet_id: int
    name: str | None = None
    planet_class: str | None = None
    planet_size: int | None = None
    owner: int | None = None
    controller: int | None = None
    governor_id: int | None = None
    designation: str | None = None
    final_designation: str | None = None
    ascension_tier: int | None = None
    districts: list[int] = field(default_factory=list)
    buildings: list[int] = field(default_factory=list)
    deposits: list[int] = field(default_factory=list)
    pop_groups: list[int] = field(default_factory=list)
    pop_jobs: list[int] = field(default_factory=list)
    num_sapient_pops: float | None = None
    stability: float | None = None
    crime: float | None = None
    amenities: float | None = None
    amenities_usage: float | None = None
    free_amenities: float | None = None
    free_housing: float | None = None
    total_housing: float | None = None
    housing_usage: float | None = None
    upkeep: dict[str, float] = field(default_factory=dict)
    produces: dict[str, float] = field(default_factory=dict)
    profits: dict[str, float] = field(default_factory=dict)


@dataclass(slots=True)
class StarbaseSummary:
    starbase_id: int
    name: str | None = None
    system_id: int | None = None
    system_name: str | None = None
    level: str | None = None
    starbase_type: str | None = None
    modules: list[str] = field(default_factory=list)
    buildings: list[str] = field(default_factory=list)
    station_id: int | None = None
    fleet_id: int | None = None
    military_power: float | None = None
    build_queue_id: int | None = None
    shipyard_build_queue_id: int | None = None
    construction_type: str | None = None


@dataclass(slots=True)
class MegastructureSummary:
    megastructure_id: int
    name: str | None = None
    megastructure_type: str | None = None
    owner: int | None = None
    system_id: int | None = None
    planet_id: int | None = None
    build_queue_id: int | None = None
    dismantle_progress: float | None = None


@dataclass(slots=True)
class ShipDesignSummary:
    design_id: int
    name: str | None = None
    ship_size: str | None = None
    auto_generated: bool | None = None
    section_templates: list[str] = field(default_factory=list)
    component_templates: list[str] = field(default_factory=list)
    required_components: list[str] = field(default_factory=list)


@dataclass(slots=True)
class EmpireSummary:
    country_id: int
    name: str | None = None
    founder_species_id: int | None = None
    ethics: list[str] = field(default_factory=list)
    government_type: str | None = None
    authority: str | None = None
    civics: list[str] = field(default_factory=list)
    origin: str | None = None
    council_agenda: str | None = None
    council_agenda_progress: float | None = None
    tradition_categories: list[str] = field(default_factory=list)
    traditions: list[str] = field(default_factory=list)
    ascension_perks: list[str] = field(default_factory=list)
    edicts: list[str] = field(default_factory=list)
    policy_flags: list[str] = field(default_factory=list)
    owned_leaders: list[int] = field(default_factory=list)
    leaders: list[LeaderSummary] = field(default_factory=list)
    pop_factions_applicable: bool | None = None
    pop_faction_members: int | None = None
    pop_faction_members_power: float | None = None
    owned_planets: list[int] = field(default_factory=list)
    planets: list[PlanetSummary] = field(default_factory=list)
    owned_fleets: list[int] = field(default_factory=list)
    starbase_capacity: int | None = None
    starbases: list[StarbaseSummary] = field(default_factory=list)
    megastructures: list[MegastructureSummary] = field(default_factory=list)
    ship_design_ids: list[int] = field(default_factory=list)
    ship_designs: list[ShipDesignSummary] = field(default_factory=list)
    technologies: dict[str, int] = field(default_factory=dict)
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
