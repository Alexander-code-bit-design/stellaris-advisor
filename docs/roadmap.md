# Roadmap

## Phase 1: Save Intake

- Validate `.sav` archives.
- Extract `meta` and `gamestate`.
- Parse top-level game date, player country, version, ironman state, and checksum.
- Add fixtures for vanilla, ironman, and modded saves.

## Phase 2: Player Empire Model

- Locate the player `country` block.
- Extract resources, monthly balance, empire size, research, unity, traditions, civics, ethics, authority, origin, and ascension perks.
- Extract civics, ethics, government authority, origin, species traits, council, leaders, factions, edicts, relics, situations, agendas, traditions, ascension perks, diplomatic stance, policies, and subject/federation status.
- Extract anomalies, special projects, situations, astral actions, relics, collections, owned species traits, species rights, and controlled space fauna where visible to the player.
- Detect economic bottlenecks with simple thresholds.
- Track existing parser/tool candidates in `docs/existing-tools.md` before adding dependencies.

## Phase 3: Planet and Fleet Analysis

- Parse owned planets and colonies.
- Extract pops, jobs, housing, amenities, stability, crime, designation, districts, buildings, blockers, and queues.
- Parse fleets, naval cap, command limit, fleet power, armies, ship designs, components, upgrade status, and reinforcement queues.
- Parse fleet composition, ship stance, home base, per-ship build details, ship stats, reinforcement state, and production queues.
- Parse starbases, modules, buildings, defense platforms, shipyards, anchorages, trade hubs, chokepoint defenses, and border fortifications.
- Parse market prices and configured monthly automatic trades.

## Phase 4: Galaxy Map and Visibility

- Parse `galactic_object` as a graph of systems and hyperlanes.
- Extract coordinates, ownership, claims, surveyed status, starbases, bypasses, gateways, wormholes, L-Gates, borders, and known hostile routes.
- Parse player-made claims and all player-visible regular empire, enclave, city-state, and special diplomatic contacts.
- Detect chokepoints, exposed borders, disconnected territory, important bypasses, and shortest paths from threats to core worlds.
- Generate a simplified map artifact from structured save data, such as SVG/HTML with systems, hyperlanes, borders, colonies, starbases, threats, and chokepoint annotations.
- Implement player-visibility filtering before any AI-facing summary is generated.
- Follow `docs/visibility-policy.md` so the advisor does not leak hidden AI empire information by default.

## Phase 5: Knowledge Retrieval

- Build a local knowledge store with source metadata:
  - source type: wiki, patch notes, forum, Reddit, guide
  - game version
  - date fetched
  - topic tags
  - confidence level
- Prefer official mechanics sources.
- Use community sources only as strategy evidence.

## Phase 6: AI Advisor

- Implement tool-calling flow:
  - `read_save`
  - `summarize_campaign`
  - `detect_findings`
  - `retrieve_knowledge`
  - `generate_advice`
- Add Chinese-first report templates.
- Support broad advice styles for exploration, development, and conquest, while asking personalization questions before over-constraining player creativity.
- Add follow-up Q&A over the parsed campaign state.

## Phase 7: Product Surface

- CLI for power users.
- Local web UI for upload and report review.
- Optional GitHub Action for regression tests on fixture saves.
- Optional desktop packaging.
