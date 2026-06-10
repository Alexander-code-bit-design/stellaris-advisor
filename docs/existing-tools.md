# Existing Tools Survey

This project should stay small at first, but these GitHub projects are useful references.

## Python

- [nthmost/stellaris-save-parser](https://github.com/nthmost/stellaris-save-parser)
  - Python library focused on Stellaris saves.
  - Claims support for empires, planets, leaders, districts, hyperlanes, bypasses, and resource budget analysis.
  - Best candidate to evaluate for reuse or API inspiration.

## AI / MCP

- [Meme-Theory/stellaris-save-mcp](https://github.com/Meme-Theory/stellaris-save-mcp)
  - MCP server exposing tools such as `list_saves`, `save_meta`, `save_empires`, and `save_empire_detail`.
  - Very close to the desired AI-agent shape.
  - Useful design reference for future local tool integration.

## Older / Reference Parsers

- [MrGrindor/Stellaris-Save-Parser](https://github.com/MrGrindor/Stellaris-Save-Parser)
  - .NET parser for planets, pops, systems, empires, buildings, fleets, and related data.
  - README says it is no longer developed, but it may still be useful for field discovery.

- [rikbrown/klausewitz-parser](https://github.com/rikbrown/klausewitz-parser)
  - Kotlin/ANTLR Clausewitz parser.
  - General parser reference, but heavier than this project's current Python MVP needs.

- [iTitus/PDXTools](https://github.com/iTitus/PDXTools)
  - General Paradox tooling.
  - Worth checking later if we need broader Clausewitz handling.

## Current Decision

For now, keep the MVP dependency-free and use a streaming/block-scanning parser. Revisit `nthmost/stellaris-save-parser` and `Meme-Theory/stellaris-save-mcp` after the project has stable report requirements.

