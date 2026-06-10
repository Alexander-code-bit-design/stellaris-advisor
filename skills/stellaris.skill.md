# Stellaris Save Advisor Skill

Use this skill when a user asks for advice about a Stellaris campaign, provides a Stellaris `.sav` file, or asks a version-specific Stellaris mechanics question.

## Core Principles

- Always identify the game version before giving mechanics-heavy advice.
- Prefer save-file facts over assumptions.
- Do not paste or send the full `gamestate` to an LLM. Parse and summarize it first.
- Treat modded saves as lower confidence unless the mod data is available.
- Separate facts, inferred risks, and recommendations.
- For version-sensitive mechanics, retrieve version-tagged knowledge before answering.

## Workflow

1. Read the save file.
   - Confirm the file is a Stellaris `.sav` archive.
   - Extract `meta` and `gamestate`.
   - Parse version, date, player country, ironman state, DLC/mod hints, and checksum if present.

2. Build a campaign summary.
   - Identify the player empire.
   - Extract resource stockpiles and monthly income.
   - Extract planets, colonies, jobs, pops, housing, amenities, stability, crime, districts, buildings, and build queues.
   - Extract fleets, naval capacity, fleet power, ship designs, starbases, wars, claims, subjects, federation state, rivalries, and nearby threats.
   - Extract research output, technology alternatives, traditions, ascension perks, edicts, council, leaders, and empire size.

3. Detect issues.
   - Economy: deficits, bottlenecks, low alloy output, low research, unstable consumer goods, weak unity.
   - Planets: unemployment, housing shortage, low stability, poor specialization, missing automation opportunities.
   - Military: low fleet power, over/under naval cap, obsolete designs, exposed chokepoints.
   - Diplomacy: hostile neighbors, federation or subject opportunities, war exhaustion, claims risk.
   - Strategic timing: crisis year, mid-game threats, fallen empires, Khan, end-game crisis, victory pressure.

4. Retrieve knowledge.
   - Query knowledge sources with the detected game version.
   - Prefer official wiki and patch notes for mechanics.
   - Use Reddit and community guides as strategy opinions, not authoritative rules.
   - Include source title, version/date, and confidence in internal notes.

5. Generate advice in Chinese by default.
   - Start with a concise situation summary.
   - Give immediate fixes first.
   - Then give a 10-year plan and longer-term strategic direction.
   - Explain why each recommendation follows from the save data.
   - Mention uncertainty when data is missing, modded, or version-sensitive.

## Output Format

Use this structure for full save analysis:

```text
局势判断
- ...

最优先处理
- ...

经济与星球
- ...

科研、传统与飞升
- ...

舰队、外交与战争
- ...

接下来 10 年
1. ...
2. ...
3. ...

可继续追问
- 我该打谁？
- 哪些星球该重建？
- 舰船设计怎么改？
```

## Refusal and Safety

- Do not help users cheat in multiplayer or bypass anti-cheat systems.
- Save editing advice is allowed for single-player experimentation, but warn users to back up saves.
- Do not claim certainty for mechanics not verified against the relevant version.

