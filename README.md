# Stellaris Advisor / 群星智能顾问

Stellaris Advisor is an experimental save-game analysis assistant for Stellaris players.
It reads a Stellaris `.sav` file, extracts version and campaign state, summarizes the player's empire, and prepares structured context for an AI assistant to give version-aware advice.

群星智能顾问是一个实验性的 Stellaris 存档分析助手。它读取 `.sav` 存档，提取版本和局势数据，总结玩家帝国状态，并为 AI 助手准备结构化上下文，从而生成按版本区分的游玩建议。

## Current Status / 当前状态

The MVP can already:

- read real Stellaris `.sav` archives;
- extract `meta` and selected `gamestate` data;
- identify save name, game version, date, and player country;
- locate the player empire's `country` block;
- extract a first empire summary, including colonies, empire size, pops, military/economy score, victory rank, and monthly income;
- extract first-pass empire identity fields, including ethics, civics, authority, government type, origin, traditions, ascension perks, edicts, policy flags, council agenda, and owned leader IDs;
- detect whether pop factions are applicable, unavailable for gestalt empires, or applicable but not yet formed;
- extract player-visible diplomatic relations and first-contact progress, including communications, hostile/border flags, opinion values, trust, threat, and active first contacts;
- fall back to summing current-month income entries when a save lacks a precomputed monthly resource summary;
- map owned leader IDs to first-pass leader details, including name localization keys, class, level, age, job, ethic, traits, location, and council position;
- map owned planet IDs to first-pass planet details, including planet class, size, pops, stability, crime/deviancy, amenities, housing, designation, districts, building cache IDs, production, upkeep, and net output;
- resolve owned planet district/building instance IDs to parsed types, levels, positions, and queue IDs where present;
- map owned starbases to systems, levels, modules, buildings, station fleets, and military power;
- parse owned fleet objects and ship instances, separating mobile fleets from station/base objects;
- extract player-owned megastructures, ship designs, researched technologies, grouped tradition details, and ascension perks;
- render common game identifiers as readable labels while preserving raw IDs for later wiki/RAG lookup;
- generate a Chinese Markdown report with early findings.

当前 MVP 已经能够：

- 读取真实 Stellaris `.sav` 存档；
- 提取 `meta` 和部分 `gamestate` 数据；
- 识别存档名、游戏版本、日期和玩家国家；
- 定位玩家帝国的 `country` 数据块；
- 提取初步帝国摘要，包括殖民地数量、帝国规模、人口、军事实力、经济实力、胜利排名和月收入；
- 提取第一批帝国身份信息，包括思潮、国民理念、权力制度、政体、起源、传统、飞升、法令、政策标记、内阁议程和拥有的领袖 ID；
- 判断派系是否适用、格式塔是否不适用，或普通政体是否尚未形成派系；
- 提取玩家可见的外交关系和首次接触进度，包括是否已通信、敌对/接壤标记、关系值、信任、威胁和进行中的首次接触；
- 当存档没有预先汇总的月收入时，回退为累加当月收入分项；
- 将拥有的领袖 ID 映射到第一批领袖详情，包括姓名本地化 key、职业、等级、年龄、岗位、思潮、特质、位置和内阁席位；
- 将拥有的星球 ID 映射到第一批星球详情，包括星球类型、大小、人口、稳定度、犯罪/偏差、舒适度、住房、定位、区划、建筑缓存 ID、产出、维护和净产出；
- 将玩家星球上的区划/建筑实例 ID 回查为类型、等级、位置和队列 ID 等结构化事实；
- 将玩家拥有的恒星基地映射到星系、等级、模块、建筑、基地舰队和军事实力；
- 解析玩家拥有的 fleet 对象和舰船实例，区分机动舰队与空间站/基地对象；
- 提取玩家拥有的巨型结构、舰船设计、已研究科技、按传统树分组的传统明细和飞升天赋；
- 将常见游戏 ID 渲染为更可读的名称，同时保留原始 ID 供后续 wiki/RAG 检索使用；
- 生成中文 Markdown 局势报告和基础问题提示。

## Design Philosophy / 设计思路

The project is designed around tools and retrieval, not model fine-tuning:

- Parse save files into structured data.
- Detect economic, military, research, planet, and diplomacy signals.
- Retrieve version-tagged knowledge from wiki pages, patch notes, and community discussions.
- Ask an LLM to explain the current situation and recommend concrete next steps.

本项目优先采用“工具调用 + 检索增强”，而不是一开始就微调模型：

- 将存档解析为结构化数据；
- 检测经济、军事、科研、星球和外交信号；
- 从带版本标签的 wiki、补丁说明和社区讨论中检索知识；
- 让 LLM 基于存档事实和检索证据解释局势，并给出具体建议。

## Quick Start / 快速开始

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
python -m stellaris_advisor examples/sample_meta_only.sav
pytest
```

On MSYS2-style Python environments, the virtual environment may use `bin` instead of `Scripts`:

如果你的 Python 环境生成的是 MSYS2 风格虚拟环境，可能需要使用 `bin` 而不是 `Scripts`：

```powershell
python -m venv .venv
.\.venv\bin\python.exe -m pip install -e ".[dev]"
.\.venv\bin\python.exe -m pytest
.\.venv\bin\python.exe -m stellaris_advisor examples/sample_meta_only.sav
```

Analyze a real save:

分析真实存档：

```powershell
python -m stellaris_advisor "C:\Users\<you>\Documents\Paradox Interactive\Stellaris\save games\<folder>\<save>.sav"
```

Choose an explicit visibility mode:

选择明确的可见性模式：

```powershell
python -m stellaris_advisor --visibility-mode player_visible "C:\path\to\save.sav"
python -m stellaris_advisor --visibility-mode omniscient "C:\path\to\save.sav"
```

Choose report language:

选择报告语言：

```powershell
python -m stellaris_advisor --language zh "C:\path\to\save.sav"
python -m stellaris_advisor --language en "C:\path\to\save.sav"
```

Choose report detail level:

选择报告详细程度：

```powershell
python -m stellaris_advisor --detail-level summary "C:\path\to\save.sav"
python -m stellaris_advisor --detail-level standard "C:\path\to\save.sav"
python -m stellaris_advisor --detail-level full "C:\path\to\save.sav"
```

`summary` keeps the overview compact. `standard` is the default. `full` exposes parsed details such as leader traits, starbase modules/buildings, planet district/building IDs, and ship design components.

`summary` 保持概览简洁。`standard` 是默认值。`full` 会展开已解析的细节，例如领袖特质、恒星基地模块/建筑、星球区划/建筑 ID 和舰船设计组件。

`player_visible` is the default and must not leak hidden AI empire data or undiscovered map information. `omniscient` is reserved for explicit spoiler/debug analysis.

`player_visible` 是默认模式，不应泄露隐藏 AI 帝国数据或未发现地图信息。`omniscient` 仅用于明确的剧透/调试分析。

## AI Advice Trial / AI 建议试用

The advisor can now turn the parsed report into a copy/paste LLM prompt:

```powershell
python -m stellaris_advisor --advice --language zh --detail-level standard "C:\path\to\save.sav"
python -m stellaris_advisor --advice --language en --detail-level standard "C:\path\to\save.sav"
```

You can add your own question:

```powershell
python -m stellaris_advisor --advice --advice-focus "我应该先补舰队、科研，还是继续扩张？" "C:\path\to\save.sav"
```

This default mode prints a prompt that can be pasted into ChatGPT, DeepSeek, or another model. It is intentionally model-independent.

If you want the CLI to call an OpenAI-compatible API directly, set an API key and model:

```powershell
$env:STELLARIS_ADVISOR_API_KEY="your_api_key"
$env:STELLARIS_ADVISOR_MODEL="your_model_name"
python -m stellaris_advisor --advice --advice-provider openai-compatible "C:\path\to\save.sav"
```

For another OpenAI-compatible provider, set the base URL as well:

```powershell
$env:STELLARIS_ADVISOR_BASE_URL="https://api.deepseek.com/v1"
$env:STELLARIS_ADVISOR_MODEL="deepseek-chat"
python -m stellaris_advisor --advice --advice-provider openai-compatible "C:\path\to\save.sav"
```

The first advice version uses only parsed save facts. Wiki, patch-note, and community retrieval are still planned as a later RAG layer, so mechanic-specific advice should be treated as provisional.

现阶段已经可以把读取器输出变成可复制给大模型的顾问提示词：

```powershell
python -m stellaris_advisor --advice --language zh --detail-level standard "C:\path\to\save.sav"
python -m stellaris_advisor --advice --language en --detail-level standard "C:\path\to\save.sav"
```

也可以附加你的具体问题：

```powershell
python -m stellaris_advisor --advice --advice-focus "我应该先补舰队、科研，还是继续扩张？" "C:\path\to\save.sav"
```

默认模式只打印提示词，你可以复制到 ChatGPT、DeepSeek 或其他模型中测试。读取器和模型是解耦的，所以后续切换模型不需要重写存档解析。

如果要让命令行直接调用兼容 OpenAI Chat Completions 的接口，可以设置 API Key 和模型：

```powershell
$env:STELLARIS_ADVISOR_API_KEY="your_api_key"
$env:STELLARIS_ADVISOR_MODEL="your_model_name"
python -m stellaris_advisor --advice --advice-provider openai-compatible "C:\path\to\save.sav"
```

如果使用其他兼容接口，再设置 base URL：

```powershell
$env:STELLARIS_ADVISOR_BASE_URL="https://api.deepseek.com/v1"
$env:STELLARIS_ADVISOR_MODEL="deepseek-chat"
python -m stellaris_advisor --advice --advice-provider openai-compatible "C:\path\to\save.sav"
```

第一版建议只基于已经解析出的存档事实。Wiki、补丁说明、社区讨论的检索增强层还在后续计划中，因此涉及具体机制强度的建议应视为待验证。

## MVP Goals / MVP 目标

1. Read `.sav` files and extract `meta` plus selected `gamestate` signals.
2. Identify game version, DLC/mod hints, player country, date, economy, planets, fleets, and wars where possible.
3. Generate an empire health report:
   - current situation;
   - immediate risks;
   - economy priorities;
   - research/tradition direction;
   - fleet and war posture;
   - next 10-year plan.
4. Use version-tagged knowledge retrieval before giving mechanism-specific advice.

---

1. 读取 `.sav` 存档，并提取 `meta` 与部分 `gamestate` 信号。
2. 尽可能识别游戏版本、DLC/mod 信息、玩家国家、日期、经济、星球、舰队和战争状态。
3. 生成帝国体检报告：
   - 当前局势；
   - 立即风险；
   - 经济优先级；
   - 科研/传统方向；
   - 舰队和战争态势；
   - 接下来 10 年计划。
4. 在给出机制相关建议前，先检索带版本标签的知识来源。

## Repository Layout / 仓库结构

```text
src/stellaris_advisor/
  cli.py              Command-line entrypoint / 命令行入口
  save_reader.py      Reads Stellaris .sav archives / 读取 Stellaris .sav 存档
  clausewitz.py       Clausewitz parser helpers / Clausewitz 文本解析辅助
  analyzer.py         Builds player-facing findings / 生成面向玩家的发现和建议
  models.py           Data models / 数据模型
skills/
  stellaris.skill.md  Agent workflow / 智能体工作流
docs/
  roadmap.md          Implementation plan / 实现路线图
  knowledge-design.md Knowledge/RAG design / 知识库与 RAG 设计
  existing-tools.md   Existing tool survey / 现有工具调研
  visibility-policy.md Player-visibility rules / 玩家可见性规则
  localization-and-decisions.md Localization and decision advice design / 本地化与决策建议设计
tests/
  test_save_reader.py MVP tests / MVP 测试
```

## Important Notes / 注意事项

- Stellaris save internals change between versions. Treat parsing as version-aware.
- Modded games can alter jobs, buildings, resources, ships, civics, traditions, and scripted values.
- Community data is useful but noisy. Store source, version, date, and confidence for every retrieved note.
- Do not put a whole `gamestate` directly into an LLM prompt. Parse and summarize first.

---

- Stellaris 存档结构会随版本变化，解析逻辑必须按版本处理。
- Mod 会改变岗位、建筑、资源、舰船、公民性、传统和脚本值。
- 社区数据有价值，但噪声较大；每条资料都应记录来源、版本、日期和可信度。
- 不要把完整 `gamestate` 直接塞进 LLM prompt；必须先解析和摘要。

## Related Work / 相关项目

See [docs/existing-tools.md](docs/existing-tools.md).

可参考 [docs/existing-tools.md](docs/existing-tools.md)。

## Player Visibility / 玩家可见性

The default advisor mode must not leak hidden AI empire data, undiscovered systems, or other information unavailable to the player in normal gameplay. See [docs/visibility-policy.md](docs/visibility-policy.md).

默认顾问模式不得泄露隐藏 AI 帝国数据、未发现星系或玩家正常游玩无法得知的信息。详见 [docs/visibility-policy.md](docs/visibility-policy.md)。
