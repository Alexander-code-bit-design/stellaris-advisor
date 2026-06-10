# Visibility Policy

Stellaris save files contain more information than a normal player can see in game.
The advisor must avoid turning save analysis into an accidental map hack or intelligence leak.

群星存档包含远多于玩家正常视野的信息。智能顾问必须避免把存档分析变成意外的全图作弊或情报泄露。

## Default Mode: Player-Visible Advice

The default mode is `player_visible`.

In this mode, the advisor may use:

- the player's own empire data;
- owned planets, fleets, leaders, council, traditions, civics, ethics, origin, factions, policies, edicts, situations, relics, and starbases;
- systems the player has discovered or surveyed;
- empires the player has contacted;
- diplomatic, war, federation, subject, trade, and market information visible to the player;
- enemy fleet and economy information only if the save marks it as known or inferable from normal gameplay visibility.

默认模式是 `player_visible`。

在该模式下，顾问可以使用：

- 玩家自己的帝国数据；
- 玩家拥有的星球、舰队、领袖、内阁、传统、国民理念、思潮、起源、派系、政策、法令、局势、遗珍和恒星基地；
- 玩家已发现或已调查的星系；
- 玩家已经接触的帝国；
- 玩家可见的外交、战争、联邦、附庸、贸易和市场信息；
- 只有当存档表明敌方舰队/经济信息已知，或可由正常游戏视野推断时，才可使用这些信息。

## Restricted Information

The advisor must not reveal by default:

- hidden AI empire resources, fleets, ship designs, technologies, planets, or precise economy;
- undiscovered systems, unsurveyed hyperlanes, hidden chokepoints, crisis spawn details, archaeology outcomes, precursor locations, or secret event chains;
- exact enemy fleet movement or force distribution when the player lacks sensors or intel;
- end-game crisis or fallen empire behavior that is not yet visible in normal gameplay.

默认情况下，顾问不得泄露：

- 隐藏 AI 帝国的资源、舰队、舰船设计、科技、星球或精确经济；
- 未发现星系、未调查航道、隐藏咽喉、危机生成细节、考古结果、先驱者位置或秘密事件链；
- 玩家传感器或情报等级不足时的敌方舰队动向和兵力分布；
- 正常游玩尚不可见的终局危机或失落帝国行动。

## Analysis Modes

The project should support explicit modes:

```text
player_visible  Default. No hidden information leaks.
debug           Developer mode for parser validation.
omniscient      Explicit spoiler/cheat mode, never enabled by default.
```

项目应支持明确模式：

```text
player_visible  默认模式，不泄露隐藏信息。
debug           开发者验证解析器使用。
omniscient      明确的剧透/作弊模式，绝不默认启用。
```

If a user requests hidden information, the assistant should ask for explicit confirmation and label the result as spoiler/omniscient analysis.

如果用户要求查看隐藏信息，助手应先要求明确确认，并将结果标记为剧透/全知分析。

## Implementation Rules

- Parse complete save data internally only when needed for technical extraction.
- Apply visibility filters before building summaries for the LLM.
- Store visibility metadata on every extracted object where possible:
  - `owner`
  - `contacted`
  - `surveyed`
  - `sensor_visible`
  - `intel_level`
  - `is_player_owned`
- Keep hidden facts out of prompts, logs, generated reports, and follow-up answers in `player_visible` mode.
- Tests should include fixtures where hidden AI data exists but must not appear in the report.

实现规则：

- 技术解析可以读取完整存档，但在构建 LLM 摘要前必须应用可见性过滤。
- 尽可能为每个对象保留可见性元数据：
  - `owner`
  - `contacted`
  - `surveyed`
  - `sensor_visible`
  - `intel_level`
  - `is_player_owned`
- 在 `player_visible` 模式下，隐藏事实不得进入 prompt、日志、报告或追问回答。
- 测试应包含“存档中存在隐藏 AI 数据，但报告不得泄露”的 fixture。

