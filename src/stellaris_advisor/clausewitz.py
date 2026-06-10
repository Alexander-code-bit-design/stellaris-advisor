from __future__ import annotations

import re
from collections.abc import Iterator
from typing import Any

TOKEN_RE = re.compile(r'"[^"]*"|[{}=]|#[^\n]*|[^\s{}=]+')


def tokenize(text: str) -> Iterator[str]:
    """Yield Clausewitz-like tokens, skipping comments."""
    for match in TOKEN_RE.finditer(text):
        token = match.group(0)
        if token.startswith("#"):
            continue
        yield token


def parse_scalar(token: str) -> Any:
    if token.startswith('"') and token.endswith('"'):
        return token[1:-1]
    if token == "yes":
        return True
    if token == "no":
        return False
    try:
        return int(token)
    except ValueError:
        pass
    try:
        return float(token)
    except ValueError:
        return token


def parse_top_level_assignments(text: str, wanted_keys: set[str] | None = None) -> dict[str, Any]:
    """Parse top-level `key=value` assignments.

    This intentionally avoids building a full in-memory tree for huge save files.
    Nested blocks are captured as compact text unless the value is scalar.
    """
    tokens = list(tokenize(text))
    result: dict[str, Any] = {}
    i = 0
    while i + 2 < len(tokens):
        key, eq, value = tokens[i], tokens[i + 1], tokens[i + 2]
        if eq != "=":
            i += 1
            continue

        if wanted_keys is not None and key not in wanted_keys:
            i = _skip_value(tokens, i + 2)
            continue

        if value == "{":
            end = _find_matching_brace(tokens, i + 2)
            result[key] = " ".join(tokens[i + 2 : end + 1])
            i = end + 1
        else:
            result[key] = parse_scalar(value)
            i += 3
    return result


def _skip_value(tokens: list[str], value_index: int) -> int:
    if value_index >= len(tokens) or tokens[value_index] != "{":
        return value_index + 1
    return _find_matching_brace(tokens, value_index) + 1


def _find_matching_brace(tokens: list[str], open_index: int) -> int:
    depth = 0
    for i in range(open_index, len(tokens)):
        if tokens[i] == "{":
            depth += 1
        elif tokens[i] == "}":
            depth -= 1
            if depth == 0:
                return i
    raise ValueError("Unclosed Clausewitz block")

