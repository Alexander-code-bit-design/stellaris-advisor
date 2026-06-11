from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


@dataclass(slots=True)
class KnowledgeRecord:
    record_id: str
    source_type: str
    title: str
    text: str
    url: str | None = None
    version: str | None = None
    fetched_at: str | None = None
    topics: list[str] = field(default_factory=list)
    confidence: str = "medium"


@dataclass(slots=True)
class KnowledgeHit:
    record: KnowledgeRecord
    score: float


class KnowledgeLoadError(RuntimeError):
    """Raised when a knowledge file cannot be loaded."""


def load_knowledge_records(path: str | Path) -> list[KnowledgeRecord]:
    root = Path(path)
    if not root.exists():
        return []
    if root.is_file():
        return list(_load_knowledge_file(root))

    records: list[KnowledgeRecord] = []
    for file_path in sorted(root.rglob("*")):
        if file_path.suffix.lower() in {".jsonl", ".md", ".txt"}:
            records.extend(_load_knowledge_file(file_path))
    return records


def retrieve_knowledge(
    records: Iterable[KnowledgeRecord],
    query: str,
    *,
    version: str | None = None,
    top_k: int = 5,
) -> list[KnowledgeHit]:
    candidates = list(records)
    if top_k <= 0 or not candidates:
        return []

    query_terms = _tokenize(query)
    if not query_terms:
        return []

    doc_terms = [_tokenize(_record_search_text(record)) for record in candidates]
    doc_count = len(candidates)
    document_frequency: dict[str, int] = {}
    for terms in doc_terms:
        for term in set(terms):
            document_frequency[term] = document_frequency.get(term, 0) + 1

    hits: list[KnowledgeHit] = []
    for record, terms in zip(candidates, doc_terms):
        if not terms:
            continue
        term_counts: dict[str, int] = {}
        for term in terms:
            term_counts[term] = term_counts.get(term, 0) + 1

        score = 0.0
        length_norm = math.sqrt(len(terms))
        for term in query_terms:
            frequency = term_counts.get(term, 0)
            if not frequency:
                continue
            idf = math.log((doc_count + 1) / (document_frequency.get(term, 0) + 0.5)) + 1
            score += (frequency * idf) / length_norm

        score += _metadata_boost(record, query_terms, version)
        if score > 0:
            hits.append(KnowledgeHit(record=record, score=score))

    return sorted(hits, key=lambda hit: hit.score, reverse=True)[:top_k]


def build_knowledge_query(summary_items: Iterable[str], focus: str | None = None) -> str:
    joined_summary = " ".join(summary_items)
    important_markers = [
        "版本",
        "Game version",
        "政体",
        "Government",
        "Authority",
        "思潮",
        "Ethics",
        "国民理念",
        "Civics",
        "传统",
        "Tradition",
        "飞升",
        "Ascension",
        "法令",
        "Edicts",
        "舰船设计",
        "Ship designs",
        "已研究科技",
        "Researched technologies",
        "恒星基地",
        "Starbases",
        "可见敌对目标",
        "Visible hostile targets",
        "舰队",
        "Fleet",
        "科研",
        "research",
    ]
    selected = [
        item
        for item in summary_items
        if any(marker in item for marker in important_markers)
    ]
    if not selected:
        selected = [joined_summary]
    if focus:
        selected.insert(0, focus)
    return "\n".join(selected)


def render_knowledge_evidence(hits: Iterable[KnowledgeHit], *, language: str) -> str:
    hit_list = list(hits)
    if not hit_list:
        return ""
    lines = (
        ["## Retrieved Knowledge Evidence", ""]
        if language == "en"
        else ["## 检索到的知识证据", ""]
    )
    for index, hit in enumerate(hit_list, start=1):
        record = hit.record
        source = record.url or record.source_type
        metadata = []
        if record.version:
            metadata.append(f"version {record.version}")
        metadata.append(f"confidence {record.confidence}")
        topics = ", ".join(record.topics) if record.topics else "untagged"
        snippet = _compact_whitespace(record.text)[:700]
        lines.extend(
            [
                f"{index}. {record.title} ({source}; {', '.join(metadata)}; topics: {topics}; score {hit.score:.2f})",
                f"   {snippet}",
            ]
        )
    return "\n".join(lines).strip()


def _load_knowledge_file(path: Path) -> Iterable[KnowledgeRecord]:
    try:
        if path.suffix.lower() == ".jsonl":
            yield from _load_jsonl(path)
        else:
            yield _load_text_file(path)
    except OSError as exc:
        raise KnowledgeLoadError(f"Could not read knowledge file {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise KnowledgeLoadError(f"Invalid JSONL in {path}: {exc}") from exc


def _load_jsonl(path: Path) -> Iterable[KnowledgeRecord]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            data = json.loads(stripped)
            yield KnowledgeRecord(
                record_id=str(data.get("id") or f"{path.stem}-{line_number}"),
                source_type=str(data.get("source_type") or "unknown"),
                title=str(data.get("title") or data.get("id") or path.stem),
                url=data.get("url"),
                version=data.get("version"),
                fetched_at=data.get("fetched_at"),
                topics=[str(topic) for topic in data.get("topics", [])],
                confidence=str(data.get("confidence") or "medium"),
                text=str(data.get("text") or ""),
            )


def _load_text_file(path: Path) -> KnowledgeRecord:
    text = path.read_text(encoding="utf-8")
    metadata, body = _split_frontmatter(text)
    return KnowledgeRecord(
        record_id=str(metadata.get("id") or path.stem),
        source_type=str(metadata.get("source_type") or "local_note"),
        title=str(metadata.get("title") or path.stem.replace("-", " ").title()),
        url=metadata.get("url"),
        version=metadata.get("version"),
        fetched_at=metadata.get("fetched_at"),
        topics=_split_csv(metadata.get("topics")),
        confidence=str(metadata.get("confidence") or "medium"),
        text=body.strip(),
    )


def _split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    raw_metadata = text[4:end]
    body = text[end + 5 :]
    metadata: dict[str, str] = {}
    for line in raw_metadata.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"')
    return metadata, body


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def _record_search_text(record: KnowledgeRecord) -> str:
    return " ".join(
        [
            record.title,
            record.version or "",
            " ".join(record.topics),
            record.source_type,
            record.confidence,
            record.text,
        ]
    )


def _metadata_boost(
    record: KnowledgeRecord, query_terms: list[str], version: str | None
) -> float:
    score = 0.0
    topic_terms = set(_tokenize(" ".join(record.topics)))
    score += len(topic_terms.intersection(query_terms)) * 0.75
    confidence_boost = {"high": 1.0, "medium": 0.5, "low": 0.1}
    score += confidence_boost.get(record.confidence.lower(), 0.25)
    if version and record.version:
        if _version_key(version) == _version_key(record.version):
            score += 2.0
        elif _version_key(version).split(".")[0] == _version_key(record.version).split(".")[0]:
            score += 0.75
    return score


def _version_key(value: str) -> str:
    match = re.search(r"\d+(?:\.\d+)*", value)
    return match.group(0) if match else value.lower()


def _tokenize(text: str) -> list[str]:
    return [token.lower() for token in re.findall(r"[A-Za-z0-9_\-\u4e00-\u9fff]+", text)]


def _compact_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()
