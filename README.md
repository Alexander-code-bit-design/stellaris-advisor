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
- generate a Chinese Markdown report with early findings.

当前 MVP 已经能够：

- 读取真实 Stellaris `.sav` 存档；
- 提取 `meta` 和部分 `gamestate` 数据；
- 识别存档名、游戏版本、日期和玩家国家；
- 定位玩家帝国的 `country` 数据块；
- 提取初步帝国摘要，包括殖民地数量、帝国规模、人口、军事实力、经济实力、胜利排名和月收入；
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

