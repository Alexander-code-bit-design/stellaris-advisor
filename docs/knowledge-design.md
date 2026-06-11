# Knowledge Design

The advisor should use retrieval-augmented generation instead of fine-tuning as the default approach.

群星智能顾问默认应采用检索增强生成（RAG），而不是一开始就微调模型。

## Why RAG First

- Stellaris changes often across patches.
- Community strategy shifts after balance updates.
- Save analysis depends more on structured game state than memorized prose.
- Sources can be updated without retraining a model.

选择 RAG 的原因：

- Stellaris 机制和数值会随版本频繁变化。
- 社区攻略会在平衡补丁后快速过时。
- 存档分析更依赖结构化局势数据，而不是模型背诵文本。
- 知识库可以持续更新，不需要重新训练模型。

## Data Pipeline

1. Ingest sources.
   - Wiki pages for mechanics.
   - Patch notes for version changes.
   - Community guides for strategy ideas.
   - Reddit/forum posts only as low-confidence player opinions.
2. Normalize records.
   - Preserve source URL, title, author/site, fetch date, game version, topic tags, and confidence.
   - Split long pages into small topic-focused chunks.
   - Avoid storing large copyrighted passages when summaries or short excerpts are enough.
3. Index records.
   - Store metadata in SQLite or Postgres.
   - Store embeddings in a local vector store such as Chroma, LanceDB, or Qdrant.
4. Retrieve before answering.
   - Use save version, empire type, crisis year, resources, and user question as retrieval filters.
   - Prefer exact version matches.
   - Surface uncertainty when only older knowledge is available.
5. Generate the answer.
   - The LLM receives structured save facts plus short retrieved evidence.
   - The final answer separates facts, inference, and recommendations.

## Current Prototype

The first implemented RAG layer is a dependency-free local retriever:

- load `.jsonl`, `.md`, and `.txt` records from a local directory;
- preserve source type, title, URL, version, fetched date, topics, confidence, and text;
- retrieve with lexical scoring plus version/topic/confidence boosts;
- insert short evidence snippets into the `--advice` prompt when `--knowledge-dir` and `--rag-top-k` are provided.

This is meant to validate the advisor flow before adding web ingestion, embeddings, or a vector database.

## 当前原型

第一版已实现的 RAG 层是零额外依赖的本地检索器：

- 从本地目录读取 `.jsonl`、`.md` 和 `.txt` 记录；
- 保留来源类型、标题、URL、版本、抓取日期、主题、置信度和正文；
- 用词法评分叠加版本/主题/置信度权重进行检索；
- 当命令提供 `--knowledge-dir` 和 `--rag-top-k` 时，把短证据片段插入 `--advice` 提示词。

这一步用于先验证顾问流程，后续再加入网页采集、embedding 或向量数据库。

## 数据流程

1. 采集资料。
   - Wiki 用于机制事实。
   - 补丁说明用于版本变化。
   - 社区攻略用于策略思路。
   - Reddit/论坛帖子只作为低置信度玩家经验。
2. 规范化记录。
   - 保留来源 URL、标题、作者/站点、抓取日期、游戏版本、主题标签和置信度。
   - 将长页面切分为小的主题片段。
   - 对受版权保护的内容尽量保存摘要或短摘录，不保存大段原文。
3. 建立索引。
   - 元数据存 SQLite 或 Postgres。
   - 向量索引可用 Chroma、LanceDB 或 Qdrant。
4. 回答前检索。
   - 用存档版本、帝国类型、危机年份、资源状态和用户问题过滤资料。
   - 优先使用精确版本匹配。
   - 如果只能找到旧版本资料，必须标注不确定性。
5. 生成回答。
   - LLM 只接收结构化存档事实和短检索证据。
   - 最终回答区分事实、推断和建议。

## Suggested Record Schema

```json
{
  "id": "wiki-3.12-research",
  "source_type": "wiki",
  "title": "Technology",
  "url": "https://stellaris.paradoxwikis.com/Technology",
  "version": "3.12",
  "fetched_at": "2026-06-10",
  "topics": ["research", "technology", "empire-size"],
  "confidence": "high",
  "text": "..."
}
```

## Source Confidence

- High: official wiki, official patch notes, in-game files for the matching version.
- Medium: well-maintained guides with explicit version tags.
- Low: Reddit comments, short posts, outdated videos, unsourced tier lists.

## Retrieval Rules

- Match exact version first.
- If exact version is missing, use nearest compatible minor version and mark uncertainty.
- Do not mix pre-major-update advice with post-major-update mechanics unless explicitly comparing versions.
- Keep retrieved snippets short and cite their source in internal reasoning or report footnotes.

## Model Strategy

Use a strong reasoning model for full campaign advice and a cheaper model for routine extraction or report formatting.

- Full strategic analysis: use a top reasoning/coding model such as `gpt-5.5` when available.
- Low-latency chat and repeated follow-up questions: use a mini model such as `gpt-5.4-mini`.
- Embeddings: use the current OpenAI embedding model family or a local embedding model, depending on cost and deployment goals.
- Local/offline option: later evaluate open-weight models for privacy-focused users, but keep the parser and RAG layer model-agnostic.

模型策略：

- 完整战略分析：优先使用强推理/代码模型，例如可用时使用 `gpt-5.5`。
- 低延迟追问和普通报告润色：使用 mini 模型，例如 `gpt-5.4-mini`。
- 向量嵌入：根据成本和部署目标，选择 OpenAI 当前嵌入模型或本地嵌入模型。
- 本地/离线方案：后续可以评估开源权重模型，但解析器和 RAG 层应保持模型无关。
