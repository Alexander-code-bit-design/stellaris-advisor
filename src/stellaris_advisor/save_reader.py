from __future__ import annotations

import re
import zipfile
from collections import deque
from pathlib import Path
from typing import Any

from .clausewitz import (
    extract_block,
    extract_numbered_block,
    extract_top_level_block,
    find_all_scalars,
    find_scalar,
    iter_anonymous_blocks,
    iter_named_blocks,
    iter_numbered_blocks,
    parse_indexed_value_block,
    parse_int_list_block,
    parse_quoted_list_block,
    parse_resource_block,
    parse_top_level_assignments,
    sum_nested_resource_blocks,
)
from .models import (
    BuildingSummary,
    DistrictSummary,
    DiplomaticRelationSummary,
    EmpireSummary,
    FleetSummary,
    FirstContactSummary,
    HyperlaneSummary,
    LeaderSummary,
    MegastructureSummary,
    OpinionModifierSummary,
    PlanetSummary,
    SaveGame,
    SaveMetadata,
    ShipSummary,
    ShipDesignSummary,
    StarbaseSummary,
    StrategicPathSummary,
    SystemSummary,
    VisibleThreatSummary,
)


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

    player_country = _extract_player_country(meta_raw, gamestate, gamestate_text)

    metadata = SaveMetadata(
        version=_as_optional_str(meta_raw.get("version")),
        name=_as_optional_str(meta_raw.get("name")),
        date=_as_optional_str(meta_raw.get("date") or gamestate.get("date")),
        player_country=player_country,
        ironman=_as_optional_bool(meta_raw.get("ironman")),
        raw=meta_raw,
    )
    player_empire = _extract_player_empire(gamestate_text, player_country)
    return SaveGame(
        metadata=metadata,
        gamestate_text=gamestate_text,
        gamestate=gamestate,
        player_empire=player_empire,
    )


def _extract_player_country(
    meta_raw: dict[str, Any], gamestate: dict[str, Any], gamestate_text: str
) -> int | None:
    direct = _as_optional_int(meta_raw.get("player") or gamestate.get("player"))
    if direct is not None:
        return direct

    player_block = extract_block(gamestate_text, "player") or gamestate.get("player")
    if isinstance(player_block, str):
        country = find_scalar(player_block, "country")
        return _as_optional_int(country)
    return None


def _extract_player_empire(gamestate_text: str, country_id: int | None) -> EmpireSummary | None:
    if country_id is None:
        return None

    countries_block = extract_top_level_block(gamestate_text, "country")
    if countries_block is None:
        return None

    country_block = extract_numbered_block(countries_block, country_id)
    if country_block is None:
        return None

    budget_block = extract_block(country_block, "budget") or ""
    income_totals = extract_block(budget_block, "resources")
    current_month_block = extract_block(budget_block, "current_month") or ""
    income_block = extract_block(current_month_block, "income")
    monthly_income = parse_resource_block(income_totals or "")
    if not monthly_income and income_block:
        monthly_income = sum_nested_resource_blocks(income_block)

    owned_planets_block = extract_block(country_block, "owned_planets")
    government_block = extract_block(country_block, "government") or ""
    ethos_block = extract_block(country_block, "ethos") or ""
    civics_block = extract_block(government_block, "civics")
    tradition_categories_block = extract_block(country_block, "tradition_categories")
    traditions_block = extract_block(country_block, "traditions")
    ascension_perks_block = extract_block(country_block, "ascension_perks")
    edicts_block = extract_block(country_block, "edicts") or ""
    policy_flags_block = extract_block(country_block, "policy_flags")
    owned_leaders_block = extract_block(country_block, "owned_leaders")
    owned_fleets_block = extract_block(country_block, "owned_fleets")
    relations_manager_block = extract_block(country_block, "relations_manager") or ""
    intel_block = extract_block(country_block, "intel") or ""
    ship_design_collection_block = extract_block(country_block, "ship_design_collection") or ""
    ship_design_ids_block = extract_block(ship_design_collection_block, "ship_design")
    owned_leaders = parse_int_list_block(owned_leaders_block or "")
    owned_planets = parse_int_list_block(owned_planets_block or "")
    owned_fleets = [int(item) for item in find_all_scalars(owned_fleets_block or "", "fleet")]
    ship_design_ids = parse_int_list_block(ship_design_ids_block or "")
    pop_factions_block = extract_block(country_block, "standard_pop_factions_module")
    is_gestalt = "ethic_gestalt_consciousness" in [
        str(item) for item in find_all_scalars(ethos_block, "ethic")
    ]

    starbases = _extract_starbases(gamestate_text, owned_fleets)
    first_contacts = _extract_first_contacts(gamestate_text, country_id)
    known_systems = _extract_known_systems(
        gamestate_text,
        country_id,
        owned_planets,
        starbases,
        first_contacts,
    )
    visible_threats = _extract_visible_threats(intel_block)

    return EmpireSummary(
        country_id=country_id,
        name=_extract_localized_name(country_block),
        founder_species_id=_as_optional_int(find_scalar(country_block, "founder_species_ref")),
        ethics=[str(item) for item in find_all_scalars(ethos_block, "ethic")],
        government_type=_as_optional_str(find_scalar(government_block, "type")),
        authority=_as_optional_str(find_scalar(government_block, "authority")),
        civics=parse_quoted_list_block(civics_block or ""),
        origin=_as_optional_str(find_scalar(government_block, "origin")),
        council_agenda=_as_optional_str(find_scalar(government_block, "council_agenda")),
        council_agenda_progress=_as_optional_float(
            find_scalar(government_block, "council_agenda_progress")
        ),
        tradition_categories=parse_quoted_list_block(tradition_categories_block or ""),
        traditions=parse_quoted_list_block(traditions_block or ""),
        ascension_perks=parse_quoted_list_block(ascension_perks_block or ""),
        edicts=[str(item) for item in find_all_scalars(edicts_block, "edict")],
        policy_flags=parse_quoted_list_block(policy_flags_block or ""),
        owned_leaders=owned_leaders,
        leaders=_extract_leaders(gamestate_text, owned_leaders),
        pop_factions_applicable=False if is_gestalt else pop_factions_block is not None,
        pop_faction_members=_as_optional_int(
            find_scalar(pop_factions_block or "", "total_faction_members")
        ),
        pop_faction_members_power=_as_optional_float(
            find_scalar(pop_factions_block or "", "total_faction_members_power")
        ),
        owned_planets=owned_planets,
        planets=_extract_planets(gamestate_text, owned_planets),
        owned_fleets=owned_fleets,
        fleets=_extract_fleets(gamestate_text, owned_fleets),
        starbase_capacity=_as_optional_int(find_scalar(country_block, "starbase_capacity")),
        starbases=starbases,
        megastructures=_extract_megastructures(gamestate_text, country_id),
        ship_design_ids=ship_design_ids,
        ship_designs=_extract_ship_designs(gamestate_text, ship_design_ids),
        diplomatic_relations=_extract_diplomatic_relations(relations_manager_block, gamestate_text),
        first_contacts=first_contacts,
        known_systems=known_systems,
        visible_threats=visible_threats,
        strategic_paths=_build_strategic_paths(
            known_systems, starbases, first_contacts, visible_threats
        ),
        technologies=_extract_technologies(country_block),
        monthly_income=monthly_income,
        fleet_size=_as_optional_float(find_scalar(country_block, "fleet_size")),
        used_naval_capacity=_as_optional_float(find_scalar(country_block, "used_naval_capacity")),
        empire_size=_as_optional_float(find_scalar(country_block, "empire_size")),
        sapient_pops=_as_optional_int(find_scalar(country_block, "num_sapient_pops")),
        military_power=_as_optional_float(find_scalar(country_block, "military_power")),
        economy_power=_as_optional_float(find_scalar(country_block, "economy_power")),
        victory_rank=_as_optional_int(find_scalar(country_block, "victory_rank")),
    )


def _extract_diplomatic_relations(
    relations_manager_block: str, gamestate_text: str
) -> list[DiplomaticRelationSummary]:
    countries_block = extract_top_level_block(gamestate_text, "country") or ""
    relations: list[DiplomaticRelationSummary] = []
    for relation_block in iter_named_blocks(relations_manager_block, "relation"):
        country_id = _as_optional_int(find_scalar(relation_block, "country"))
        if country_id is None:
            continue
        target_block = extract_numbered_block(countries_block, country_id) or ""
        relations.append(
            DiplomaticRelationSummary(
                country_id=country_id,
                name=_extract_relation_name(relation_block, target_block),
                contact=_as_optional_bool(find_scalar(relation_block, "contact")),
                communications=_as_optional_bool(find_scalar(relation_block, "communications")),
                hostile=_as_optional_bool(find_scalar(relation_block, "hostile")),
                borders=_as_optional_bool(find_scalar(relation_block, "borders")),
                relation_current=_as_optional_float(find_scalar(relation_block, "relation_current")),
                relation_last_month=_as_optional_float(
                    find_scalar(relation_block, "relation_last_month")
                ),
                trust=_as_optional_float(find_scalar(relation_block, "trust")),
                threat=_as_optional_float(find_scalar(relation_block, "threat")),
                border_range=_as_optional_int(find_scalar(relation_block, "border_range")),
                shared_rivals=_as_optional_int(find_scalar(relation_block, "shared_rivals")),
                modifiers=_extract_opinion_modifiers(relation_block),
            )
        )
    return relations


def _extract_relation_name(relation_block: str, target_country_block: str) -> str | None:
    if _as_optional_bool(find_scalar(relation_block, "communications")):
        return _extract_localized_name(target_country_block) or _extract_localized_name(relation_block)
    pre_communications_block = extract_block(relation_block, "pre_communications_name") or ""
    return (
        _as_optional_str(find_scalar(pre_communications_block, "key"))
        or _extract_localized_name(pre_communications_block)
        or _extract_localized_name(relation_block)
    )


def _extract_opinion_modifiers(relation_block: str) -> list[OpinionModifierSummary]:
    modifiers: list[OpinionModifierSummary] = []
    for modifier_block in iter_named_blocks(relation_block, "modifier"):
        modifier = _as_optional_str(find_scalar(modifier_block, "modifier"))
        if modifier is None:
            continue
        modifiers.append(
            OpinionModifierSummary(
                modifier=modifier,
                value=_as_optional_float(find_scalar(modifier_block, "value")),
                start_date=_as_optional_str(find_scalar(modifier_block, "start_date")),
                decay=_as_optional_bool(find_scalar(modifier_block, "decay")),
            )
        )
    return modifiers


def _extract_first_contacts(gamestate_text: str, player_country_id: int) -> list[FirstContactSummary]:
    first_contacts_block = extract_top_level_block(gamestate_text, "first_contacts") or ""
    contacts_block = extract_block(first_contacts_block, "contacts") or ""
    contacts: list[FirstContactSummary] = []
    for contact_id, contact_block in iter_numbered_blocks(contacts_block):
        owner = _as_optional_int(find_scalar(contact_block, "owner"))
        country_id = _as_optional_int(find_scalar(contact_block, "country"))
        if owner != player_country_id and country_id != player_country_id:
            continue
        contacts.append(
            FirstContactSummary(
                contact_id=contact_id,
                owner=owner,
                country_id=country_id,
                name=_extract_localized_name(contact_block),
                location_id=_as_optional_int(find_scalar(contact_block, "location")),
                leader_id=_as_optional_int(find_scalar(contact_block, "leader")),
                date=_as_optional_str(find_scalar(contact_block, "date")),
                days_left=_as_optional_float(find_scalar(contact_block, "days_left")),
                difficulty=_as_optional_int(find_scalar(contact_block, "difficulty")),
                clues=_as_optional_int(find_scalar(contact_block, "clues")),
                stage=_as_optional_str(find_scalar(contact_block, "stage")),
                status=_as_optional_str(find_scalar(contact_block, "status")),
            )
        )
    return contacts


def _extract_visible_threats(intel_block: str) -> list[VisibleThreatSummary]:
    threats: list[VisibleThreatSummary] = []
    threat_id = 0
    for object_block in iter_anonymous_blocks(intel_block):
        object_system_id = _as_optional_int(find_scalar(object_block, "object"))
        hostile_block = extract_block(object_block, "hostile") or ""
        for hostile_entry in iter_anonymous_blocks(hostile_block):
            coordinate_block = extract_block(hostile_entry, "coordinate") or ""
            system_id = _as_optional_int(find_scalar(coordinate_block, "origin"))
            name = _extract_localized_name(hostile_entry)
            military_power = _as_optional_float(find_scalar(hostile_entry, "military_power"))
            threat_type, mobility, risk_hint = _classify_visible_threat(
                name, military_power
            )
            threats.append(
                VisibleThreatSummary(
                    threat_id=threat_id,
                    system_id=system_id if system_id is not None else object_system_id,
                    name=name,
                    owner=_as_optional_int(find_scalar(hostile_entry, "owner")),
                    military_power=military_power,
                    threat_type=threat_type,
                    mobility=mobility,
                    risk_hint=risk_hint,
                )
            )
            threat_id += 1
    return threats


def _classify_visible_threat(
    name: str | None, military_power: float | None
) -> tuple[str, str, str]:
    normalized = (name or "").lower()
    if any(token in normalized for token in ["amoeba", "voidworm", "space fauna", "spaceborne"]):
        return (
            "space_fauna",
            "mobile",
            "hostile space fauna; movement and aggression need mechanics/RAG validation",
        )
    if any(
        token in normalized
        for token in ["starbase", "military_station", "mining_station", "research_station", "observation_station"]
    ):
        return (
            "station_or_platform",
            "stationary",
            "static hostile installation; do not treat as an invading fleet by itself",
        )
    if "constructor" in normalized or "colonizer" in normalized or "science" in normalized:
        return (
            "civilian_ship",
            "mobile",
            "mobile non-combat or low-combat ship; war risk depends on owner diplomacy",
        )
    if military_power is not None and military_power <= 0:
        return (
            "noncombat_or_unknown",
            "unknown",
            "zero military power; do not treat as direct combat threat without more context",
        )
    if "fleet" in normalized:
        return (
            "military_fleet",
            "mobile",
            "mobile hostile fleet; evaluate owner diplomacy, path, and starbase defenses",
        )
    return (
        "unknown_hostile",
        "unknown",
        "hostile entry with unknown behavior; avoid assuming active attack without corroborating data",
    )


def _extract_known_systems(
    gamestate_text: str,
    player_country_id: int,
    owned_planets: list[int],
    starbases: list[StarbaseSummary],
    first_contacts: list[FirstContactSummary],
) -> list[SystemSummary]:
    galactic_objects = extract_top_level_block(gamestate_text, "galactic_object") or ""
    if not galactic_objects:
        return []

    anchor_system_ids = {
        starbase.system_id for starbase in starbases if starbase.system_id is not None
    }
    anchor_system_ids.update(
        contact.location_id for contact in first_contacts if contact.location_id is not None
    )
    systems: list[SystemSummary] = []
    for system_id, system_block in iter_numbered_blocks(galactic_objects):
        discovery_block = extract_block(system_block, "discovery") or ""
        discovered = player_country_id in parse_int_list_block(discovery_block)
        system_planets = [
            int(item)
            for item in find_all_scalars(system_block, "planet")
            if _as_optional_int(item) is not None
        ]
        has_owned_planet = any(planet_id in owned_planets for planet_id in system_planets)
        if not discovered and system_id not in anchor_system_ids and not has_owned_planet:
            continue

        starbases_block = extract_block(system_block, "starbases")
        colonies_block = extract_block(system_block, "colonies")
        fleet_presence_block = extract_block(system_block, "fleet_presence")
        bypasses_block = extract_block(system_block, "bypasses")
        systems.append(
            SystemSummary(
                system_id=system_id,
                name=_extract_localized_name(system_block),
                star_class=_as_optional_str(find_scalar(system_block, "star_class")),
                discovered=discovered,
                sector_id=_as_optional_int(find_scalar(system_block, "sector")),
                starbase_ids=[
                    item for item in parse_int_list_block(starbases_block or "") if item != 4294967295
                ],
                colonies=[
                    item for item in parse_int_list_block(colonies_block or "") if item != 4294967295
                ],
                fleet_ids=parse_int_list_block(fleet_presence_block or ""),
                bypass_ids=[
                    item for item in parse_int_list_block(bypasses_block or "") if item != 4294967295
                ],
                hyperlanes=_extract_hyperlanes(system_block),
            )
        )
    return systems


def _extract_hyperlanes(system_block: str) -> list[HyperlaneSummary]:
    hyperlane_block = extract_block(system_block, "hyperlane") or ""
    hyperlanes: list[HyperlaneSummary] = []
    for lane_block in iter_anonymous_blocks(hyperlane_block):
        to_system_id = _as_optional_int(find_scalar(lane_block, "to"))
        if to_system_id is None or to_system_id == 4294967295:
            continue
        hyperlanes.append(
            HyperlaneSummary(
                to_system_id=to_system_id,
                length=_as_optional_float(find_scalar(lane_block, "length")),
                bridge=_as_optional_bool(find_scalar(lane_block, "bridge")),
            )
        )
    return hyperlanes


def _build_strategic_paths(
    known_systems: list[SystemSummary],
    starbases: list[StarbaseSummary],
    first_contacts: list[FirstContactSummary],
    visible_threats: list[VisibleThreatSummary],
) -> list[StrategicPathSummary]:
    if not known_systems:
        return []

    systems_by_id = {system.system_id: system for system in known_systems}
    graph = _build_known_system_graph(known_systems)
    colony_system_ids = {system.system_id for system in known_systems if system.colonies}
    starbase_system_ids = {system.system_id for system in known_systems if system.starbase_ids}
    upgraded_starbase_system_ids = {
        starbase.system_id
        for starbase in starbases
        if starbase.system_id is not None and _uses_starbase_capacity(starbase.level)
    }
    shipyard_system_ids = {
        starbase.system_id
        for starbase in starbases
        if starbase.system_id is not None
        and any(str(module).strip('"') == "shipyard" for module in starbase.modules)
    }

    paths: list[StrategicPathSummary] = []
    seen_sources: set[tuple[str, int, int]] = set()
    for contact in first_contacts:
        if contact.status == "finished" or contact.location_id is None:
            continue
        source = ("first_contact", contact.contact_id, contact.location_id)
        if source in seen_sources:
            continue
        seen_sources.add(source)
        if contact.location_id not in systems_by_id:
            continue
        distances = _shortest_known_distances(graph, contact.location_id)
        nearest_colony = _nearest_system(distances, colony_system_ids)
        nearest_starbase = _nearest_system(distances, starbase_system_ids)
        nearest_upgraded = _nearest_system(distances, upgraded_starbase_system_ids)
        nearest_shipyard = _nearest_system(distances, shipyard_system_ids)
        source_system = systems_by_id.get(contact.location_id)
        paths.append(
            StrategicPathSummary(
                source_kind="first_contact",
                source_id=contact.contact_id,
                source_name=contact.name,
                source_system_id=contact.location_id,
                source_system_name=source_system.name if source_system else None,
                nearest_colony_system_id=nearest_colony,
                nearest_colony_system_name=_system_name(systems_by_id, nearest_colony),
                jumps_to_nearest_colony=_distance_to(distances, nearest_colony),
                nearest_starbase_system_id=nearest_starbase,
                nearest_starbase_system_name=_system_name(systems_by_id, nearest_starbase),
                jumps_to_nearest_starbase=_distance_to(distances, nearest_starbase),
                nearest_upgraded_starbase_system_id=nearest_upgraded,
                nearest_upgraded_starbase_system_name=_system_name(systems_by_id, nearest_upgraded),
                jumps_to_nearest_upgraded_starbase=_distance_to(distances, nearest_upgraded),
                nearest_shipyard_system_id=nearest_shipyard,
                nearest_shipyard_system_name=_system_name(systems_by_id, nearest_shipyard),
                jumps_to_nearest_shipyard=_distance_to(distances, nearest_shipyard),
            )
        )
    for threat in visible_threats:
        if threat.system_id is None:
            continue
        source = ("visible_threat", threat.threat_id, threat.system_id)
        if source in seen_sources:
            continue
        seen_sources.add(source)
        if threat.system_id not in systems_by_id:
            continue
        distances = _shortest_known_distances(graph, threat.system_id)
        nearest_colony = _nearest_system(distances, colony_system_ids)
        nearest_starbase = _nearest_system(distances, starbase_system_ids)
        nearest_upgraded = _nearest_system(distances, upgraded_starbase_system_ids)
        nearest_shipyard = _nearest_system(distances, shipyard_system_ids)
        source_system = systems_by_id.get(threat.system_id)
        paths.append(
            StrategicPathSummary(
                source_kind="visible_threat",
                source_id=threat.threat_id,
                source_name=threat.name,
                source_system_id=threat.system_id,
                source_system_name=source_system.name if source_system else None,
                nearest_colony_system_id=nearest_colony,
                nearest_colony_system_name=_system_name(systems_by_id, nearest_colony),
                jumps_to_nearest_colony=_distance_to(distances, nearest_colony),
                nearest_starbase_system_id=nearest_starbase,
                nearest_starbase_system_name=_system_name(systems_by_id, nearest_starbase),
                jumps_to_nearest_starbase=_distance_to(distances, nearest_starbase),
                nearest_upgraded_starbase_system_id=nearest_upgraded,
                nearest_upgraded_starbase_system_name=_system_name(systems_by_id, nearest_upgraded),
                jumps_to_nearest_upgraded_starbase=_distance_to(distances, nearest_upgraded),
                nearest_shipyard_system_id=nearest_shipyard,
                nearest_shipyard_system_name=_system_name(systems_by_id, nearest_shipyard),
                jumps_to_nearest_shipyard=_distance_to(distances, nearest_shipyard),
            )
        )
    return paths


def _build_known_system_graph(known_systems: list[SystemSummary]) -> dict[int, set[int]]:
    known_ids = {system.system_id for system in known_systems}
    graph: dict[int, set[int]] = {system.system_id: set() for system in known_systems}
    for system in known_systems:
        for lane in system.hyperlanes:
            if lane.to_system_id in known_ids:
                graph[system.system_id].add(lane.to_system_id)
                graph.setdefault(lane.to_system_id, set()).add(system.system_id)
    return graph


def _shortest_known_distances(graph: dict[int, set[int]], source_id: int) -> dict[int, int]:
    distances = {source_id: 0}
    queue: deque[int] = deque([source_id])
    while queue:
        current = queue.popleft()
        for neighbor in graph.get(current, set()):
            if neighbor in distances:
                continue
            distances[neighbor] = distances[current] + 1
            queue.append(neighbor)
    return distances


def _nearest_system(distances: dict[int, int], target_ids: set[int]) -> int | None:
    reachable = [(distances[target_id], target_id) for target_id in target_ids if target_id in distances]
    if not reachable:
        return None
    return min(reachable)[1]


def _distance_to(distances: dict[int, int], system_id: int | None) -> int | None:
    if system_id is None:
        return None
    return distances.get(system_id)


def _system_name(systems_by_id: dict[int, SystemSummary], system_id: int | None) -> str | None:
    if system_id is None:
        return None
    system = systems_by_id.get(system_id)
    return system.name if system else None


def _uses_starbase_capacity(level: str | None) -> bool:
    if level is None:
        return False
    normalized = level.strip('"')
    return normalized not in {"starbase_level_outpost", "outpost"}


def _extract_fleets(gamestate_text: str, owned_fleets: list[int]) -> list[FleetSummary]:
    fleets_block = extract_top_level_block(gamestate_text, "fleet") or ""
    ships_block = extract_top_level_block(gamestate_text, "ships") or ""
    summaries: list[FleetSummary] = []
    for fleet_id in owned_fleets:
        fleet_block = extract_numbered_block(fleets_block, fleet_id)
        if not fleet_block:
            continue
        ship_ids = parse_int_list_block(extract_block(fleet_block, "ships") or "")
        ships = _extract_ship_summaries(ships_block, ship_ids)
        movement_manager_block = extract_block(fleet_block, "movement_manager") or ""
        coordinate_block = extract_block(movement_manager_block, "coordinate") or ""
        summaries.append(
            FleetSummary(
                fleet_id=fleet_id,
                name=_extract_localized_name(fleet_block),
                ship_class=_as_optional_str(find_scalar(fleet_block, "ship_class")),
                station=_as_optional_bool(find_scalar(fleet_block, "station")),
                military_power=_as_optional_float(find_scalar(fleet_block, "military_power")),
                system_id=_as_optional_int(find_scalar(coordinate_block, "origin")),
                ship_ids=ship_ids,
                ships=ships,
            )
        )
    return summaries


def _extract_ship_summaries(ships_block: str, ship_ids: list[int]) -> list[ShipSummary]:
    ships: list[ShipSummary] = []
    for ship_id in ship_ids:
        ship = _extract_ship_summary(ships_block, ship_id)
        if ship is not None:
            ships.append(ship)
    return ships


def _extract_ship_summary(ships_block: str, ship_id: int) -> ShipSummary | None:
    ship_block = extract_numbered_block(ships_block, ship_id)
    if not ship_block:
        return None
    return ShipSummary(
        ship_id=ship_id,
        name=_extract_localized_name(ship_block),
        design_id=_as_optional_int(find_scalar(ship_block, "design")),
        fleet_id=_as_optional_int(find_scalar(ship_block, "fleet")),
        hit_points=_as_optional_float(find_scalar(ship_block, "hit_points")),
        military_power=_as_optional_float(find_scalar(ship_block, "military_power")),
    )


def _extract_megastructures(
    gamestate_text: str, country_id: int
) -> list[MegastructureSummary]:
    megastructures_block = extract_top_level_block(gamestate_text, "megastructures")
    if megastructures_block is None:
        return []

    summaries: list[MegastructureSummary] = []
    for megastructure_id, megastructure_block in iter_numbered_blocks(megastructures_block):
        owner = _as_optional_int(find_scalar(megastructure_block, "owner"))
        if owner != country_id:
            continue
        coordinate_block = extract_block(megastructure_block, "coordinate") or ""
        summaries.append(
            MegastructureSummary(
                megastructure_id=megastructure_id,
                name=_extract_localized_name(megastructure_block),
                megastructure_type=_as_optional_str(find_scalar(megastructure_block, "type")),
                owner=owner,
                system_id=_as_optional_int(find_scalar(coordinate_block, "origin")),
                planet_id=_as_optional_int(find_scalar(megastructure_block, "planet")),
                build_queue_id=_as_optional_int(find_scalar(megastructure_block, "build_queue")),
                dismantle_progress=_as_optional_float(
                    find_scalar(megastructure_block, "dismantle_progress")
                ),
            )
        )
    return summaries


def _extract_ship_designs(
    gamestate_text: str, ship_design_ids: list[int]
) -> list[ShipDesignSummary]:
    ship_designs_block = extract_top_level_block(gamestate_text, "ship_design")
    if ship_designs_block is None:
        return []

    summaries: list[ShipDesignSummary] = []
    for design_id in ship_design_ids:
        design_block = extract_numbered_block(ship_designs_block, design_id)
        if design_block is None:
            continue
        summaries.append(
            ShipDesignSummary(
                design_id=design_id,
                name=_extract_localized_name(design_block),
                ship_size=_as_optional_str(find_scalar(design_block, "ship_size")),
                auto_generated=_as_optional_bool(find_scalar(design_block, "auto_gen_design")),
                section_templates=_extract_section_templates(design_block),
                component_templates=_extract_component_templates(design_block),
                required_components=[
                    str(item) for item in find_all_scalars(design_block, "required_component")
                ],
            )
        )
    return summaries


def _extract_technologies(country_block: str) -> dict[str, int]:
    tech_status_block = extract_block(country_block, "tech_status")
    if not tech_status_block:
        return {}

    technologies: dict[str, int] = {}
    for tech, level in re.findall(
        r'technology\s*=\s*"([^"]+)"\s+level\s*=\s*(-?\d+)', tech_status_block
    ):
        technologies[tech] = int(level)
    return technologies


def _extract_section_templates(design_block: str) -> list[str]:
    sections: list[str] = []
    for section_match in re.finditer(r"(?m)^\s*section\s*=", design_block):
        section_block = extract_block(design_block, "section", section_match.start())
        template = find_scalar(section_block or "", "template")
        if template is not None:
            sections.append(str(template))
    return sections


def _extract_component_templates(design_block: str) -> list[str]:
    components: list[str] = []
    for component_match in re.finditer(r"(?m)^\s*component\s*=", design_block):
        component_block = extract_block(design_block, "component", component_match.start())
        template = find_scalar(component_block or "", "template")
        if template is not None:
            components.append(str(template))
    return components


def _extract_starbases(gamestate_text: str, owned_fleets: list[int]) -> list[StarbaseSummary]:
    starbase_mgr = extract_top_level_block(gamestate_text, "starbase_mgr") or ""
    starbases_table = extract_block(starbase_mgr, "starbases")
    ships_block = extract_top_level_block(gamestate_text, "ships") or ""
    fleets_block = extract_top_level_block(gamestate_text, "fleet") or ""
    galactic_objects = extract_top_level_block(gamestate_text, "galactic_object") or ""
    if starbases_table is None:
        return []

    system_by_starbase = _map_starbase_systems(galactic_objects)
    summaries: list[StarbaseSummary] = []
    for starbase_id, starbase_block in iter_numbered_blocks(starbases_table):
        station_id = _as_optional_int(find_scalar(starbase_block, "station"))
        ship_block = extract_numbered_block(ships_block, station_id) if station_id is not None else None
        fleet_id = _as_optional_int(find_scalar(ship_block or "", "fleet"))
        if fleet_id not in owned_fleets:
            continue
        fleet_block = extract_numbered_block(fleets_block, fleet_id) if fleet_id is not None else None
        system_id, system_name = system_by_starbase.get(starbase_id, (None, None))
        modules_block = extract_block(starbase_block, "modules")
        buildings_block = extract_block(starbase_block, "buildings")
        summaries.append(
            StarbaseSummary(
                starbase_id=starbase_id,
                name=_extract_localized_name(fleet_block or ship_block or starbase_block),
                system_id=system_id,
                system_name=system_name,
                level=_as_optional_str(find_scalar(starbase_block, "level")),
                starbase_type=_as_optional_str(find_scalar(starbase_block, "type")),
                modules=[str(item).strip('"') for item in parse_indexed_value_block(modules_block or "")],
                buildings=[str(item).strip('"') for item in parse_indexed_value_block(buildings_block or "")],
                station_id=station_id,
                fleet_id=fleet_id,
                military_power=_as_optional_float(find_scalar(fleet_block or "", "military_power")),
                build_queue_id=_as_optional_int(find_scalar(starbase_block, "build_queue")),
                shipyard_build_queue_id=_as_optional_int(find_scalar(starbase_block, "shipyard_build_queue")),
                construction_type=_as_optional_str(find_scalar(starbase_block, "construction_type")),
            )
        )
    return summaries


def _map_starbase_systems(galactic_objects: str) -> dict[int, tuple[int, str | None]]:
    mapping: dict[int, tuple[int, str | None]] = {}
    for system_id, system_block in iter_numbered_blocks(galactic_objects):
        starbases_block = extract_block(system_block, "starbases")
        for starbase_id in parse_int_list_block(starbases_block or ""):
            if starbase_id == 4294967295:
                continue
            mapping[starbase_id] = (system_id, _extract_localized_name(system_block))
    return mapping


def _extract_planets(gamestate_text: str, planet_ids: list[int]) -> list[PlanetSummary]:
    planets_block = extract_top_level_block(gamestate_text, "planets")
    if planets_block is None:
        return []

    districts_table = extract_top_level_block(gamestate_text, "districts") or ""
    buildings_table = extract_top_level_block(gamestate_text, "buildings") or ""
    planets: list[PlanetSummary] = []
    for planet_id in planet_ids:
        planet_block = extract_numbered_block(planets_block, planet_id)
        if planet_block is None or not planet_block.strip():
            continue
        districts_block = extract_block(planet_block, "districts")
        buildings_block = extract_block(planet_block, "buildings_cache")
        deposits_block = extract_block(planet_block, "deposits")
        pop_groups_block = extract_block(planet_block, "pop_groups")
        pop_jobs_block = extract_block(planet_block, "pop_jobs")
        upkeep_block = extract_block(planet_block, "upkeep")
        produces_block = extract_block(planet_block, "produces")
        profits_block = extract_block(planet_block, "profits")
        district_ids = parse_int_list_block(districts_block or "")
        building_ids = parse_int_list_block(buildings_block or "")
        planets.append(
            PlanetSummary(
                planet_id=planet_id,
                name=_extract_localized_name(planet_block),
                planet_class=_as_optional_str(find_scalar(planet_block, "planet_class")),
                planet_size=_as_optional_int(find_scalar(planet_block, "planet_size")),
                owner=_as_optional_int(find_scalar(planet_block, "owner")),
                controller=_as_optional_int(find_scalar(planet_block, "controller")),
                governor_id=_as_optional_int(find_scalar(planet_block, "governor")),
                designation=_as_optional_str(find_scalar(planet_block, "designation")),
                final_designation=_as_optional_str(find_scalar(planet_block, "final_designation")),
                ascension_tier=_as_optional_int(find_scalar(planet_block, "ascension_tier")),
                districts=district_ids,
                district_details=_extract_district_details(districts_table, district_ids),
                buildings=building_ids,
                building_details=_extract_building_details(buildings_table, building_ids),
                deposits=parse_int_list_block(deposits_block or ""),
                pop_groups=parse_int_list_block(pop_groups_block or ""),
                pop_jobs=parse_int_list_block(pop_jobs_block or ""),
                build_queue_id=_as_optional_int(find_scalar(planet_block, "build_queue")),
                army_build_queue_id=_as_optional_int(find_scalar(planet_block, "army_build_queue")),
                last_building_changed=_as_optional_str(find_scalar(planet_block, "last_building_changed")),
                last_district_changed=_as_optional_str(find_scalar(planet_block, "last_district_changed")),
                num_sapient_pops=_as_optional_float(find_scalar(planet_block, "num_sapient_pops")),
                stability=_as_optional_float(find_scalar(planet_block, "stability")),
                crime=_as_optional_float(find_scalar(planet_block, "crime")),
                amenities=_as_optional_float(find_scalar(planet_block, "amenities")),
                amenities_usage=_as_optional_float(find_scalar(planet_block, "amenities_usage")),
                free_amenities=_as_optional_float(find_scalar(planet_block, "free_amenities")),
                free_housing=_as_optional_float(find_scalar(planet_block, "free_housing")),
                total_housing=_as_optional_float(find_scalar(planet_block, "total_housing")),
                housing_usage=_as_optional_float(find_scalar(planet_block, "housing_usage")),
                upkeep=parse_resource_block(upkeep_block or ""),
                produces=parse_resource_block(produces_block or ""),
                profits=parse_resource_block(profits_block or ""),
            )
        )
    return planets


def _extract_district_details(
    districts_table: str, district_ids: list[int]
) -> list[DistrictSummary]:
    details: list[DistrictSummary] = []
    for district_id in district_ids:
        district_block = extract_numbered_block(districts_table, district_id)
        if not district_block:
            continue
        zones_block = extract_block(district_block, "zones")
        details.append(
            DistrictSummary(
                district_id=district_id,
                district_type=_as_optional_str(find_scalar(district_block, "type")),
                level=_as_optional_int(find_scalar(district_block, "level")),
                zones=[
                    zone_id
                    for zone_id in parse_int_list_block(zones_block or "")
                    if zone_id != 4294967295
                ],
            )
        )
    return details


def _extract_building_details(
    buildings_table: str, building_ids: list[int]
) -> list[BuildingSummary]:
    details: list[BuildingSummary] = []
    for building_id in building_ids:
        building_block = extract_numbered_block(buildings_table, building_id)
        if not building_block:
            continue
        details.append(
            BuildingSummary(
                building_id=building_id,
                building_type=_as_optional_str(find_scalar(building_block, "type")),
                position=_as_optional_int(find_scalar(building_block, "position")),
                ruined=_as_optional_bool(find_scalar(building_block, "ruined")),
                disabled=_as_optional_bool(find_scalar(building_block, "disabled")),
            )
        )
    return details


def _extract_leaders(gamestate_text: str, leader_ids: list[int]) -> list[LeaderSummary]:
    leaders_block = extract_top_level_block(gamestate_text, "leaders")
    if leaders_block is None:
        return []

    leaders: list[LeaderSummary] = []
    for leader_id in leader_ids:
        leader_block = extract_numbered_block(leaders_block, leader_id)
        if leader_block is None:
            continue
        location_block = extract_block(leader_block, "location") or ""
        council_location_block = extract_block(leader_block, "council_location") or ""
        leaders.append(
            LeaderSummary(
                leader_id=leader_id,
                name=_extract_leader_name(leader_block),
                leader_class=_as_optional_str(find_scalar(leader_block, "class")),
                level=_as_optional_int(find_scalar(leader_block, "level")),
                age=_as_optional_int(find_scalar(leader_block, "age")),
                gender=_as_optional_str(find_scalar(leader_block, "gender")),
                ethic=_as_optional_str(find_scalar(leader_block, "ethic")),
                job=_as_optional_str(find_scalar(leader_block, "job")),
                traits=[str(item) for item in find_all_scalars(leader_block, "traits")],
                location_type=_as_optional_str(find_scalar(location_block, "type")),
                location_id=_as_optional_int(find_scalar(location_block, "id")),
                council_position_id=_as_optional_int(find_scalar(council_location_block, "id")),
            )
        )
    return leaders


def _extract_leader_name(block: str) -> str | None:
    name_block = extract_block(block, "name")
    if name_block is None:
        return _as_optional_str(find_scalar(block, "name"))

    full_names_block = extract_block(name_block, "full_names") or name_block
    variables_block = extract_block(full_names_block, "variables")
    if variables_block:
        parts = [
            str(item)
            for item in find_all_scalars(variables_block, "key")
            if not str(item).isdigit()
        ]
        if parts:
            return " ".join(parts)

    key = find_scalar(full_names_block, "key") or find_scalar(name_block, "key")
    return _as_optional_str(key)


def _extract_localized_name(block: str) -> str | None:
    name_block = extract_block(block, "name")
    if name_block is None:
        value = find_scalar(block, "name")
        return _as_optional_str(value)
    variables_block = extract_block(name_block, "variables")
    if variables_block:
        name_variable_match = find_scalar(variables_block, "NAME")
        if name_variable_match is not None:
            return _as_optional_str(name_variable_match)
        variable_keys = [
            str(item)
            for item in find_all_scalars(variables_block, "key")
            if str(item) not in {"NAME"} and not str(item).isdigit()
        ]
        if variable_keys:
            return " ".join(variable_keys)
    key = find_scalar(name_block, "key")
    return _as_optional_str(key)


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


def _as_optional_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
