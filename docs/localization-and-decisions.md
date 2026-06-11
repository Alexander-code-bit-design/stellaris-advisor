# Localization and Decision Advice

## Standard names

The advisor should not rely on fallback ID formatting as the final source of truth.
Fallback formatting is useful for early reports, but standard English and Chinese names should come from version-aware sources.

Preferred source order:

1. Game localization files for the active Stellaris version and enabled mods.
2. Version-tagged wiki/RAG records, with source URL, page version, retrieval date, and confidence.
3. Deterministic fallback formatting from raw IDs.

The report must preserve raw IDs such as `tech_starbase_2` even when it renders a readable name. Raw IDs are the stable join key for localization files, save data, wiki pages, and future advice rules.

## English and Chinese report output

Reports should be selectable with `--language zh` or `--language en`.

Language selection affects:

- section headings;
- summary labels;
- finding titles, details, and recommendations;
- next development or next-action text;
- eventually, localized game object names.

Language selection must not change the parsed facts.

## Detail levels

The parser should preserve detailed facts even when the report does not display them by default.

Report detail levels:

- `summary`: compact player-facing overview.
- `standard`: default report with moderate context.
- `full`: expanded facts for debugging and AI context, including leader traits, starbase modules and buildings, planet district/building IDs, and ship design components.

The assistant should use detailed facts internally when relevant, but should avoid dumping them into normal player-facing summaries.

Owned fleet objects should be parsed as facts before any strategic interpretation. Stellaris stores starbases, mining stations, research stations, construction ships, science ships, transports, and combat fleets in related fleet/ship structures. The parser should distinguish mobile combat fleets from station/base objects instead of treating `owned_fleets` as a pure military count.

Planet districts and buildings should also be resolved through their instance tables. Planet-local ID lists are not enough; the parser should preserve district type, district level, building type, building position, and construction queue IDs when present.

## Wiki verification

Wiki data is evidence, not the canonical parser contract. The current public English Stellaris Wiki technology pages are useful for validating player-facing names and mechanics, but may lag behind the current game version. Chinese wiki availability and naming consistency can vary.

For reliable bilingual names, local game files are usually better than public wiki pages. Wiki records should still be indexed because they explain mechanics and strategy, while game localization files should resolve exact labels.

## In-game decisions

Many Stellaris decisions are not static empire facts. Examples include event choices, first contact responses, agenda choices, traditions, ascension perks, war goals, diplomacy, colony designations, and crisis paths.

The long-term product should handle them with a decision workflow:

1. Detect active decision context from the save when possible, such as event targets, active agendas, research options, traditions, policies, and diplomacy state.
2. Let the player paste or screenshot the current decision text when the save does not expose enough UI context.
3. Convert the decision into structured options: option text, costs, rewards, risks, constraints, and hidden follow-up flags if known.
4. Retrieve version-tagged evidence from wiki, patch notes, and trusted community discussion.
5. Score each option against the player's stated goal, such as roleplay, conquest, economy, crisis rush, tall play, or no-spoiler mode.
6. Explain recommendations without leaking hidden information in `player_visible` mode.

Decision advice should be interactive. The assistant should ask the player for intent when the best choice depends on goals rather than objective strength.
