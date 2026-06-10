from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Any

from .clausewitz import (
    extract_block,
    extract_numbered_block,
    extract_top_level_block,
    find_all_scalars,
    find_scalar,
    parse_int_list_block,
    parse_quoted_list_block,
    parse_resource_block,
    parse_top_level_assignments,
    sum_nested_resource_blocks,
)
from .models import EmpireSummary, LeaderSummary, PlanetSummary, SaveGame, SaveMetadata


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
    owned_leaders = parse_int_list_block(owned_leaders_block or "")
    owned_planets = parse_int_list_block(owned_planets_block or "")
    pop_factions_block = extract_block(country_block, "standard_pop_factions_module")
    is_gestalt = "ethic_gestalt_consciousness" in [
        str(item) for item in find_all_scalars(ethos_block, "ethic")
    ]

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
        monthly_income=monthly_income,
        fleet_size=_as_optional_float(find_scalar(country_block, "fleet_size")),
        used_naval_capacity=_as_optional_float(find_scalar(country_block, "used_naval_capacity")),
        empire_size=_as_optional_float(find_scalar(country_block, "empire_size")),
        sapient_pops=_as_optional_int(find_scalar(country_block, "num_sapient_pops")),
        military_power=_as_optional_float(find_scalar(country_block, "military_power")),
        economy_power=_as_optional_float(find_scalar(country_block, "economy_power")),
        victory_rank=_as_optional_int(find_scalar(country_block, "victory_rank")),
    )


def _extract_planets(gamestate_text: str, planet_ids: list[int]) -> list[PlanetSummary]:
    planets_block = extract_top_level_block(gamestate_text, "planets")
    if planets_block is None:
        return []

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
                districts=parse_int_list_block(districts_block or ""),
                buildings=parse_int_list_block(buildings_block or ""),
                deposits=parse_int_list_block(deposits_block or ""),
                pop_groups=parse_int_list_block(pop_groups_block or ""),
                pop_jobs=parse_int_list_block(pop_jobs_block or ""),
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
