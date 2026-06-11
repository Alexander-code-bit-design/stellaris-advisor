from __future__ import annotations

import re

from .localization import LocalizationCatalog


PREFIXES = {
    "tech": "Technology",
    "ap": "Ascension Perk",
    "civic": "Civic",
    "ethic": "Ethic",
    "auth": "Authority",
    "gov": "Government",
    "origin": "Origin",
    "agenda": "Agenda",
    "edict": "Edict",
    "policy": "Policy",
    "pc": "Planet Class",
    "tr": "Tradition",
    "tradition": "Tradition Tree",
    "leader_trait": "Leader Trait",
    "trait": "Trait",
    "col": "Designation",
}

TOKEN_REPLACEMENTS = {
    "ai": "AI",
    "bio": "Bio",
    "fe": "FE",
    "ftl": "FTL",
    "pd": "PD",
    "sct": "Standard Construction Templates",
}

_ACTIVE_CATALOG: LocalizationCatalog | None = None


def set_localization_catalog(catalog: LocalizationCatalog | None) -> None:
    global _ACTIVE_CATALOG
    _ACTIVE_CATALOG = catalog


def display_name(
    identifier: object,
    include_raw: bool = True,
    catalog: LocalizationCatalog | None = None,
) -> str:
    raw = str(identifier)
    cleaned = raw.strip().strip('"')
    if not cleaned:
        return cleaned

    selected_catalog = catalog if catalog is not None else _ACTIVE_CATALOG
    label = selected_catalog.lookup(cleaned) if selected_catalog is not None else None
    if not label:
        label = _format_identifier(cleaned)
    if include_raw and label != cleaned:
        return f"{label} [{cleaned}]"
    return label


def compact_name(
    identifier: object, catalog: LocalizationCatalog | None = None
) -> str:
    label = display_name(identifier, include_raw=False, catalog=catalog)
    for prefix in ["Planet Class: "]:
        if label.startswith(prefix):
            return label[len(prefix) :]
    return label


def _format_identifier(identifier: str) -> str:
    if identifier.startswith("NAME_"):
        identifier = identifier[5:]

    upper_label = _format_upper_component(identifier)
    if upper_label is not None:
        return upper_label

    prefix, body = _split_known_prefix(identifier)
    words = _format_words(body)
    if prefix is None:
        return words
    return f"{prefix}: {words}"


def _split_known_prefix(identifier: str) -> tuple[str | None, str]:
    for prefix in sorted(PREFIXES, key=len, reverse=True):
        marker = prefix + "_"
        if identifier.startswith(marker):
            return PREFIXES[prefix], identifier[len(marker) :]
    return None, identifier


def _format_upper_component(identifier: str) -> str | None:
    if not re.fullmatch(r"[A-Z0-9_]+", identifier):
        return None
    parts = [part for part in identifier.split("_") if part]
    if not parts:
        return identifier

    size_words = {
        "SMALL": "Small",
        "MEDIUM": "Medium",
        "LARGE": "Large",
        "AUX": "Auxiliary",
        "CORVETTE": "Corvette",
        "BULWARK": "Bulwark",
        "DEFAULT": "Default",
    }
    formatted = []
    for part in parts:
        formatted.append(_roman_or_word(size_words.get(part, part.title())))
    return " ".join(formatted)


def _format_words(body: str) -> str:
    parts = [part for part in body.split("_") if part]
    if not parts:
        return body
    formatted = []
    for part in parts:
        replacement = TOKEN_REPLACEMENTS.get(part.lower())
        if replacement is not None:
            formatted.append(replacement)
            continue
        formatted.append(_roman_or_word(part.replace("-", " ").title()))
    return " ".join(formatted)


def _roman_or_word(word: str) -> str:
    if word.isdigit():
        return _to_roman(int(word))
    return word


def _to_roman(value: int) -> str:
    if value <= 0 or value > 50:
        return str(value)
    numerals = [
        (50, "L"),
        (40, "XL"),
        (10, "X"),
        (9, "IX"),
        (5, "V"),
        (4, "IV"),
        (1, "I"),
    ]
    result = []
    remaining = value
    for number, numeral in numerals:
        while remaining >= number:
            result.append(numeral)
            remaining -= number
    return "".join(result)
