# Knowledge Design

The advisor should use retrieval-augmented generation instead of fine-tuning as the default approach.

## Why RAG First

- Stellaris changes often across patches.
- Community strategy shifts after balance updates.
- Save analysis depends more on structured game state than memorized prose.
- Sources can be updated without retraining a model.

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

