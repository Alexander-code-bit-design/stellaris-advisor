from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .report_language import ReportLanguage


class LocalizationLoadError(RuntimeError):
    """Raised when official localization files cannot be loaded."""


@dataclass(slots=True)
class LocalizationCatalog:
    language: ReportLanguage
    entries: dict[str, str]

    def lookup(self, key: object) -> str | None:
        raw = str(key).strip().strip('"')
        if not raw:
            return None
        value = self.entries.get(raw)
        if value is None:
            return None
        return _clean_localized_text(value, self.entries)


def load_localization_catalog(
    root: str | Path, language: ReportLanguage
) -> LocalizationCatalog:
    root_path = Path(root)
    if not root_path.exists():
        raise LocalizationLoadError(f"Localization path does not exist: {root_path}")

    files = _find_localization_files(root_path, language)
    entries: dict[str, str] = {}
    for file_path in files:
        entries.update(_parse_localization_file(file_path))
    return LocalizationCatalog(language=language, entries=entries)


def _find_localization_files(root: Path, language: ReportLanguage) -> list[Path]:
    marker = "l_english" if language is ReportLanguage.EN else "l_simp_chinese"
    if root.is_file():
        return [root] if marker in root.name.lower() or root.suffix.lower() in {".yml", ".yaml"} else []

    search_roots = [root]
    for child in [
        root / "localisation",
        root / "localization",
        root / "localisation" / "english",
        root / "localisation" / "simp_chinese",
        root / "localization" / "english",
        root / "localization" / "simp_chinese",
    ]:
        if child.exists():
            search_roots.append(child)

    found: dict[Path, None] = {}
    for search_root in search_roots:
        for file_path in search_root.rglob("*.yml"):
            if marker in file_path.name.lower():
                found[file_path] = None
    return sorted(found)


def _parse_localization_file(path: Path) -> dict[str, str]:
    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise LocalizationLoadError(f"Could not read localization file {path}: {exc}") from exc

    entries: dict[str, str] = {}
    for line in text.splitlines():
        parsed = _parse_localization_line(line)
        if parsed is None:
            continue
        key, value = parsed
        entries[key] = value
    return entries


def _parse_localization_line(line: str) -> tuple[str, str] | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or stripped.endswith(":"):
        return None
    match = re.match(r"^([A-Za-z0-9_.\-]+):\d*\s+\"(.*)\"\s*$", stripped)
    if not match:
        return None
    key, value = match.groups()
    return key, _unescape(value)


def _unescape(value: str) -> str:
    return (
        value.replace(r"\"", '"')
        .replace(r"\n", " ")
        .replace(r"\t", " ")
        .replace("§!", "")
    )


def _clean_localized_text(value: str, entries: dict[str, str]) -> str:
    text = value
    for _ in range(4):
        replaced = re.sub(
            r"\$([A-Za-z0-9_.\-]+)\$",
            lambda match: entries.get(match.group(1), match.group(0)),
            text,
        )
        if replaced == text:
            break
        text = replaced
    text = re.sub(r"§[A-Za-z0-9!]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text
