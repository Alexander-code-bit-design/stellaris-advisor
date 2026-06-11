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


def extract_block(text: str, key: str, start: int = 0) -> str | None:
    """Return the contents of the first `key={...}` block after `start`."""
    match = re.search(r"(?m)^\s*" + re.escape(key) + r"\s*=", text[start:])
    if not match:
        return None
    assign_start = start + match.start()
    open_index = text.find("{", assign_start)
    if open_index == -1:
        return None
    close_index = find_matching_brace(text, open_index)
    return text[open_index + 1 : close_index]


def extract_top_level_block(text: str, key: str, start: int = 0) -> str | None:
    """Return the contents of a top-level `key={...}` block.

    Stellaris saves often contain nested fields with the same name, such as
    `player={ country=0 }` before the top-level `country={...}` table.
    """
    match = re.search(r"(?m)^" + re.escape(key) + r"\s*=", text[start:])
    if not match:
        return None
    assign_start = start + match.start()
    open_index = text.find("{", assign_start)
    if open_index == -1:
        return None
    close_index = find_matching_brace(text, open_index)
    return text[open_index + 1 : close_index]


def extract_numbered_block(text: str, item_id: int) -> str | None:
    """Return the contents of an `123={...}` block inside a parent block."""
    match = re.search(r"(?m)^\s*" + re.escape(str(item_id)) + r"\s*=", text)
    if not match:
        return None
    open_index = text.find("{", match.start())
    if open_index == -1:
        return None
    close_index = find_matching_brace(text, open_index)
    return text[open_index + 1 : close_index]


def iter_numbered_blocks(text: str) -> Iterator[tuple[int, str]]:
    """Yield top-level `123={...}` blocks from a table body."""
    index = 0
    depth = 0
    in_string = False
    escaped = False
    while index < len(text):
        char = text[index]
        if in_string:
            if char == "\\" and not escaped:
                escaped = True
                index += 1
                continue
            if char == '"' and not escaped:
                in_string = False
            escaped = False
            index += 1
            continue

        if char == '"':
            in_string = True
            index += 1
            continue
        if char == "{":
            depth += 1
            index += 1
            continue
        if char == "}":
            depth -= 1
            index += 1
            continue

        if depth == 0 and (index == 0 or text[index - 1] == "\n"):
            match = re.match(r"[ \t]*(\d+)\s*=\s*\{", text[index:])
            if match:
                open_index = index + match.end() - 1
                close_index = find_matching_brace(text, open_index)
                yield int(match.group(1)), text[open_index + 1 : close_index]
                index = close_index + 1
                continue

        index += 1


def iter_named_blocks(text: str, key: str) -> Iterator[str]:
    """Yield top-level repeated `key={...}` blocks from a parent block."""
    index = 0
    depth = 0
    in_string = False
    escaped = False
    pattern = re.compile(r"[ \t]*" + re.escape(key) + r"\s*=\s*\{")
    while index < len(text):
        char = text[index]
        if in_string:
            if char == "\\" and not escaped:
                escaped = True
                index += 1
                continue
            if char == '"' and not escaped:
                in_string = False
            escaped = False
            index += 1
            continue

        if char == '"':
            in_string = True
            index += 1
            continue
        if char == "{":
            depth += 1
            index += 1
            continue
        if char == "}":
            depth -= 1
            index += 1
            continue

        if depth == 0 and (index == 0 or text[index - 1] == "\n"):
            match = pattern.match(text[index:])
            if match:
                open_index = index + match.end() - 1
                close_index = find_matching_brace(text, open_index)
                yield text[open_index + 1 : close_index]
                index = close_index + 1
                continue

        index += 1


def iter_anonymous_blocks(text: str) -> Iterator[str]:
    """Yield top-level anonymous `{...}` blocks from a parent block."""
    index = 0
    depth = 0
    in_string = False
    escaped = False
    while index < len(text):
        char = text[index]
        if in_string:
            if char == "\\" and not escaped:
                escaped = True
                index += 1
                continue
            if char == '"' and not escaped:
                in_string = False
            escaped = False
            index += 1
            continue

        if char == '"':
            in_string = True
            index += 1
            continue
        if char == "{":
            if depth == 0:
                close_index = find_matching_brace(text, index)
                yield text[index + 1 : close_index]
                index = close_index + 1
                continue
            depth += 1
            index += 1
            continue
        if char == "}":
            depth -= 1
            index += 1
            continue

        index += 1


def find_matching_brace(text: str, open_index: int) -> int:
    depth = 0
    in_string = False
    escaped = False
    for i in range(open_index, len(text)):
        char = text[i]
        if in_string:
            if char == "\\" and not escaped:
                escaped = True
                continue
            if char == '"' and not escaped:
                in_string = False
            escaped = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return i
    raise ValueError("Unclosed Clausewitz block")


def _brace_depth_at(text: str, offset: int) -> int:
    depth = 0
    in_string = False
    escaped = False
    for char in text[:offset]:
        if in_string:
            if char == "\\" and not escaped:
                escaped = True
                continue
            if char == '"' and not escaped:
                in_string = False
            escaped = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
    return depth


def find_scalar(text: str, key: str) -> Any:
    match = re.search(r"(?<![A-Za-z0-9_])" + re.escape(key) + r"\s*=\s*(\"[^\"]*\"|[^\s{}]+)", text)
    if not match:
        return None
    return parse_scalar(match.group(1))


def parse_resource_block(text: str) -> dict[str, float]:
    resources: dict[str, float] = {}
    for key, value in re.findall(r"(?m)^\s*([A-Za-z0-9_]+)\s*=\s*(-?\d+(?:\.\d+)?)", text):
        resources[key] = float(value)
    return resources


def sum_nested_resource_blocks(text: str) -> dict[str, float]:
    totals: dict[str, float] = {}
    for key, value in re.findall(r"(?<![A-Za-z0-9_])([A-Za-z0-9_]+)\s*=\s*(-?\d+(?:\.\d+)?)", text):
        totals[key] = totals.get(key, 0.0) + float(value)
    return totals


def parse_int_list_block(text: str) -> list[int]:
    return [int(item) for item in re.findall(r"-?\d+", text)]


def parse_quoted_list_block(text: str) -> list[str]:
    return re.findall(r'"([^"]+)"', text)


def parse_indexed_value_block(text: str) -> list[str]:
    return re.findall(r"(?<![A-Za-z0-9_])\d+\s*=\s*(\"[^\"]*\"|[A-Za-z0-9_]+)", text)


def find_all_scalars(text: str, key: str) -> list[Any]:
    pattern = r"(?<![A-Za-z0-9_])" + re.escape(key) + r"\s*=\s*(\"[^\"]*\"|[^\s{}]+)"
    return [parse_scalar(match.group(1)) for match in re.finditer(pattern, text)]


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
