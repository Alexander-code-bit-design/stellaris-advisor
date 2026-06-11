from __future__ import annotations

from pathlib import Path

from stellaris_advisor.knowledge import (
    build_knowledge_query,
    load_knowledge_records,
    render_knowledge_evidence,
    retrieve_knowledge,
)


def test_load_jsonl_and_retrieve_versioned_record(tmp_path: Path) -> None:
    knowledge_file = tmp_path / "stellaris.jsonl"
    knowledge_file.write_text(
        "\n".join(
            [
                '{"id":"wiki-4.3-research","source_type":"wiki","title":"Technology","url":"https://example.test/technology","version":"4.3","topics":["research","technology","empire-size"],"confidence":"high","text":"Research output must keep pace with empire size and researcher jobs."}',
                '{"id":"reddit-old-fleet","source_type":"reddit","title":"Old Fleet Advice","version":"2.8","topics":["fleet"],"confidence":"low","text":"Always ignore starbases and build only corvettes."}',
            ]
        ),
        encoding="utf-8",
    )

    records = load_knowledge_records(tmp_path)
    hits = retrieve_knowledge(
        records,
        "Cetus v4.3 research technology empire size",
        version="Cetus v4.3.7",
        top_k=1,
    )

    assert len(records) == 2
    assert hits[0].record.record_id == "wiki-4.3-research"
    assert hits[0].record.confidence == "high"


def test_load_markdown_frontmatter_and_render_evidence(tmp_path: Path) -> None:
    note = tmp_path / "machine-servitor.md"
    note.write_text(
        """---
id: local-machine-servitor
source_type: local_note
title: Machine Servitor Economy
version: 4.3
topics: machine, economy, biotrophy
confidence: medium
---
Machine Servitor economies need to balance machine production with organic sanctuary support.
""",
        encoding="utf-8",
    )

    records = load_knowledge_records(tmp_path)
    hits = retrieve_knowledge(records, "machine servitor economy sanctuary", top_k=3)
    rendered = render_knowledge_evidence(hits, language="en")

    assert records[0].record_id == "local-machine-servitor"
    assert "Machine Servitor Economy" in rendered
    assert "confidence medium" in rendered


def test_build_knowledge_query_prefers_strategy_relevant_summary_lines() -> None:
    query = build_knowledge_query(
        [
            "Save name: Example",
            "Game version: Cetus v4.3.7",
            "Starbases: total 11; capacity used 2 / 4",
            "Monthly income: energy +20",
        ],
        focus="Should I build ships?",
    )

    assert "Should I build ships?" in query
    assert "Game version" in query
    assert "Starbases" in query
    assert "Save name" not in query
