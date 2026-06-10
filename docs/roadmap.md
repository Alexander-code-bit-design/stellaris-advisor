# Roadmap

## Phase 1: Save Intake

- Validate `.sav` archives.
- Extract `meta` and `gamestate`.
- Parse top-level game date, player country, version, ironman state, and checksum.
- Add fixtures for vanilla, ironman, and modded saves.

## Phase 2: Player Empire Model

- Locate the player `country` block.
- Extract resources, monthly balance, empire size, research, unity, traditions, civics, ethics, authority, origin, and ascension perks.
- Detect economic bottlenecks with simple thresholds.
- Track existing parser/tool candidates in `docs/existing-tools.md` before adding dependencies.

## Phase 3: Planet and Fleet Analysis

- Parse owned planets and colonies.
- Extract pops, jobs, housing, amenities, stability, crime, designation, districts, buildings, blockers, and queues.
- Parse fleets, naval cap, command limit, fleet power, starbases, ship designs, and upgrade status.

## Phase 4: Knowledge Retrieval

- Build a local knowledge store with source metadata:
  - source type: wiki, patch notes, forum, Reddit, guide
  - game version
  - date fetched
  - topic tags
  - confidence level
- Prefer official mechanics sources.
- Use community sources only as strategy evidence.

## Phase 5: AI Advisor

- Implement tool-calling flow:
  - `read_save`
  - `summarize_campaign`
  - `detect_findings`
  - `retrieve_knowledge`
  - `generate_advice`
- Add Chinese-first report templates.
- Add follow-up Q&A over the parsed campaign state.

## Phase 6: Product Surface

- CLI for power users.
- Local web UI for upload and report review.
- Optional GitHub Action for regression tests on fixture saves.
- Optional desktop packaging.
