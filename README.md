# Stellaris Advisor

Stellaris Advisor is an experimental save-game analysis assistant for Stellaris players.
It reads a Stellaris `.sav` file, extracts version and campaign state, summarizes the player's empire, and prepares structured context for an AI assistant to give version-aware advice.

The project is designed around tools and retrieval, not model fine-tuning:

- Parse save files into structured data.
- Detect economic, military, research, planet, and diplomacy signals.
- Retrieve version-tagged knowledge from wiki pages, patch notes, and community discussions.
- Ask an LLM to explain the current situation and recommend concrete next steps.

## MVP Goals

1. Read `.sav` files and extract `meta` plus selected `gamestate` signals.
2. Identify game version, DLC/mod hints, player country, date, economy, planets, fleets, and wars where possible.
3. Generate a Chinese empire health report:
   - current situation
   - immediate risks
   - economy priorities
   - research/tradition direction
   - fleet and war posture
   - next 10-year plan
4. Use version-tagged knowledge retrieval before giving mechanism-specific advice.

## Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
python -m stellaris_advisor examples/sample_meta_only.sav
pytest
```

## Repository Layout

```text
src/stellaris_advisor/
  cli.py              Command-line entrypoint.
  save_reader.py      Reads Stellaris .sav archives.
  clausewitz.py       Lightweight Clausewitz text tokenizer/parser helpers.
  analyzer.py         Turns parsed state into player-facing findings.
  models.py           Data models for summaries and findings.
skills/
  stellaris.skill.md  Agent workflow for save analysis.
docs/
  roadmap.md          Implementation plan.
  existing-tools.md   GitHub survey of reusable parsers and MCP tools.
tests/
  test_save_reader.py MVP tests.
```

## Important Notes

- Stellaris save internals change between versions. Treat parsing as version-aware.
- Modded games can alter jobs, buildings, resources, ships, civics, traditions, and scripted values.
- Community data is useful but noisy. Store source, version, date, and confidence for every retrieved note.
- Do not put a whole `gamestate` directly into an LLM prompt. Parse and summarize first.
