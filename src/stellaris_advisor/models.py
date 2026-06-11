from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .detail_level import DetailLevel
from .report_language import ReportLanguage
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
class DistrictSummary:
    district_id: int
    district_type: str | None = None
    level: int | None = None
    zones: list[int] = field(default_factory=list)


@dataclass(slots=True)
class BuildingSummary:
    building_id: int
    building_type: str | None = None
    position: int | None = None
    ruined: bool | None = None
    disabled: bool | None = None


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
    district_details: list[DistrictSummary] = field(default_factory=list)
    buildings: list[int] = field(default_factory=list)
    building_details: list[BuildingSummary] = field(default_factory=list)
    deposits: list[int] = field(default_factory=list)
    pop_groups: list[int] = field(default_factory=list)
    pop_jobs: list[int] = field(default_factory=list)
    build_queue_id: int | None = None
    army_build_queue_id: int | None = None
    last_building_changed: str | None = None
    last_district_changed: str | None = None
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
class ShipSummary:
    ship_id: int
    name: str | None = None
    design_id: int | None = None
    fleet_id: int | None = None
    hit_points: float | None = None
    military_power: float | None = None
    armor: float | None = None
    shield: float | None = None
    experience: float | None = None
    build_progress: float | None = None
    upgrade_progress: float | None = None
    order: str | None = None


@dataclass(slots=True)
class FleetSummary:
    fleet_id: int
    name: str | None = None
    ship_class: str | None = None
    station: bool | None = None
    military_power: float | None = None
    system_id: int | None = None
    home_base_id: int | None = None
    stance: str | None = None
    fleet_activity: str | None = None
    orbit_target_id: int | None = None
    target_system_id: int | None = None
    target_fleet_id: int | None = None
    speed: float | None = None
    reinforcement: bool | None = None
    upgrading: bool | None = None
    build_queue_id: int | None = None
    reinforcement_queue_id: int | None = None
    ship_ids: list[int] = field(default_factory=list)
    ships: list[ShipSummary] = field(default_factory=list)


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
class OpinionModifierSummary:
    modifier: str
    value: float | None = None
    start_date: str | None = None
    decay: bool | None = None


@dataclass(slots=True)
class DiplomaticRelationSummary:
    country_id: int
    name: str | None = None
    contact: bool | None = None
    communications: bool | None = None
    hostile: bool | None = None
    borders: bool | None = None
    relation_current: float | None = None
    relation_last_month: float | None = None
    trust: float | None = None
    threat: float | None = None
    border_range: int | None = None
    shared_rivals: int | None = None
    risk_hint: str | None = None
    deescalation_hint: str | None = None
    modifiers: list[OpinionModifierSummary] = field(default_factory=list)


@dataclass(slots=True)
class FirstContactSummary:
    contact_id: int
    owner: int | None = None
    country_id: int | None = None
    name: str | None = None
    location_id: int | None = None
    leader_id: int | None = None
    date: str | None = None
    days_left: float | None = None
    difficulty: int | None = None
    clues: int | None = None
    stage: str | None = None
    status: str | None = None


@dataclass(slots=True)
class HyperlaneSummary:
    to_system_id: int
    length: float | None = None
    bridge: bool | None = None


@dataclass(slots=True)
class SystemSummary:
    system_id: int
    name: str | None = None
    star_class: str | None = None
    discovered: bool | None = None
    sector_id: int | None = None
    starbase_ids: list[int] = field(default_factory=list)
    colonies: list[int] = field(default_factory=list)
    fleet_ids: list[int] = field(default_factory=list)
    bypass_ids: list[int] = field(default_factory=list)
    hyperlanes: list[HyperlaneSummary] = field(default_factory=list)


@dataclass(slots=True)
class VisibleThreatSummary:
    threat_id: int
    system_id: int | None = None
    name: str | None = None
    owner: int | None = None
    military_power: float | None = None
    threat_type: str | None = None
    mobility: str | None = None
    risk_hint: str | None = None


@dataclass(slots=True)
class StrategicPathSummary:
    source_kind: str
    source_id: int
    source_system_id: int
    source_name: str | None = None
    source_system_name: str | None = None
    nearest_colony_system_id: int | None = None
    nearest_colony_system_name: str | None = None
    jumps_to_nearest_colony: int | None = None
    nearest_starbase_system_id: int | None = None
    nearest_starbase_system_name: str | None = None
    jumps_to_nearest_starbase: int | None = None
    nearest_upgraded_starbase_system_id: int | None = None
    nearest_upgraded_starbase_system_name: str | None = None
    jumps_to_nearest_upgraded_starbase: int | None = None
    nearest_shipyard_system_id: int | None = None
    nearest_shipyard_system_name: str | None = None
    jumps_to_nearest_shipyard: int | None = None


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
    fleets: list[FleetSummary] = field(default_factory=list)
    starbase_capacity: int | None = None
    starbases: list[StarbaseSummary] = field(default_factory=list)
    megastructures: list[MegastructureSummary] = field(default_factory=list)
    ship_design_ids: list[int] = field(default_factory=list)
    ship_designs: list[ShipDesignSummary] = field(default_factory=list)
    diplomatic_relations: list[DiplomaticRelationSummary] = field(default_factory=list)
    first_contacts: list[FirstContactSummary] = field(default_factory=list)
    known_systems: list[SystemSummary] = field(default_factory=list)
    visible_threats: list[VisibleThreatSummary] = field(default_factory=list)
    strategic_paths: list[StrategicPathSummary] = field(default_factory=list)
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
    language: ReportLanguage
    detail_level: DetailLevel
    summary: list[str]
    findings: list[Finding]
    next_steps: list[str]
