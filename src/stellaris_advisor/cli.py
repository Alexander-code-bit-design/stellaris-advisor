from __future__ import annotations

import argparse
import sys

from .advice import (
    AdviceError,
    api_key_from_env,
    build_advice_prompt,
    request_openai_compatible_advice,
)
from .analyzer import build_report, render_markdown
from .detail_level import DetailLevel
from .display_names import set_localization_catalog
from .knowledge import (
    KnowledgeLoadError,
    build_knowledge_query,
    load_knowledge_records,
    retrieve_knowledge,
)
from .localization import LocalizationLoadError, load_localization_catalog
from .report_language import ReportLanguage
from .save_reader import SaveReadError, read_save
from .strategic_focus import StrategicFocus, focus_description
from .visibility import VisibilityMode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analyze a Stellaris save file.")
    parser.add_argument("save_file", help="Path to a Stellaris .sav file")
    parser.add_argument(
        "--visibility-mode",
        choices=[mode.value for mode in VisibilityMode],
        default=VisibilityMode.PLAYER_VISIBLE.value,
        help="Information visibility mode. Defaults to player_visible.",
    )
    parser.add_argument(
        "--language",
        choices=[language.value for language in ReportLanguage],
        default=ReportLanguage.ZH.value,
        help="Report language. Defaults to zh.",
    )
    parser.add_argument(
        "--detail-level",
        choices=[level.value for level in DetailLevel],
        default=DetailLevel.STANDARD.value,
        help="Report detail level. Defaults to standard.",
    )
    parser.add_argument(
        "--advice",
        action="store_true",
        help="Generate an LLM advice prompt, or call an OpenAI-compatible chat API.",
    )
    parser.add_argument(
        "--advice-provider",
        choices=["prompt", "openai-compatible"],
        default="prompt",
        help="Advice backend. 'prompt' prints a copy/paste prompt. Defaults to prompt.",
    )
    parser.add_argument(
        "--advice-focus",
        help="Optional player question or strategic focus for the advisor.",
    )
    parser.add_argument(
        "--strategic-focus",
        choices=[focus.value for focus in StrategicFocus],
        default=StrategicFocus.BALANCED.value,
        help="Advice style focus: balanced, explore, develop, or conquer. Defaults to balanced.",
    )
    parser.add_argument(
        "--advice-model",
        default=None,
        help="Model name for --advice-provider openai-compatible. May also use STELLARIS_ADVISOR_MODEL.",
    )
    parser.add_argument(
        "--advice-base-url",
        default=None,
        help="Base URL for an OpenAI-compatible API. May also use STELLARIS_ADVISOR_BASE_URL.",
    )
    parser.add_argument(
        "--advice-api-key-env",
        default="STELLARIS_ADVISOR_API_KEY",
        help="Environment variable containing the API key. Defaults to STELLARIS_ADVISOR_API_KEY.",
    )
    parser.add_argument(
        "--advice-timeout",
        type=int,
        default=60,
        help="LLM request timeout in seconds. Defaults to 60.",
    )
    parser.add_argument(
        "--knowledge-dir",
        default=None,
        help="Directory or file containing local RAG knowledge records (.jsonl, .md, .txt).",
    )
    parser.add_argument(
        "--rag-top-k",
        type=int,
        default=0,
        help="Number of local knowledge records to retrieve into --advice prompts. Defaults to 0.",
    )
    parser.add_argument(
        "--localization-dir",
        default=None,
        help=(
            "Stellaris installation, localisation directory, or localization .yml file. "
            "May also use STELLARIS_ADVISOR_LOCALIZATION_DIR."
        ),
    )
    args = parser.parse_args(argv)

    try:
        save = read_save(args.save_file)
    except SaveReadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    language = ReportLanguage(args.language)
    localization_dir = args.localization_dir or _env("STELLARIS_ADVISOR_LOCALIZATION_DIR")
    if localization_dir:
        try:
            set_localization_catalog(load_localization_catalog(localization_dir, language))
        except LocalizationLoadError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
    else:
        set_localization_catalog(None)

    report = build_report(
        save,
        VisibilityMode(args.visibility_mode),
        language,
        DetailLevel(args.detail_level),
    )
    if not args.advice:
        print(render_markdown(report))
        return 0

    knowledge_hits = []
    if args.rag_top_k > 0:
        if not args.knowledge_dir:
            print("error: --rag-top-k requires --knowledge-dir", file=sys.stderr)
            return 2
        try:
            knowledge_records = load_knowledge_records(args.knowledge_dir)
        except KnowledgeLoadError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        strategic_focus = StrategicFocus(args.strategic_focus)
        knowledge_query = build_knowledge_query(
            report.summary,
            " ".join(
                item
                for item in [
                    args.advice_focus,
                    focus_description(strategic_focus, zh=(language is ReportLanguage.ZH)),
                ]
                if item
            ),
        )
        knowledge_hits = retrieve_knowledge(
            knowledge_records,
            knowledge_query,
            version=save.metadata.version,
            top_k=args.rag_top_k,
        )

    prompt = build_advice_prompt(
        report,
        args.advice_focus,
        knowledge_hits,
        StrategicFocus(args.strategic_focus),
    )
    if args.advice_provider == "prompt":
        print(prompt.render())
        return 0

    model = args.advice_model or _env("STELLARIS_ADVISOR_MODEL")
    base_url = args.advice_base_url or _env("STELLARIS_ADVISOR_BASE_URL") or "https://api.openai.com/v1"
    api_key = api_key_from_env(args.advice_api_key_env)
    try:
        print(
            request_openai_compatible_advice(
                prompt,
                model=model,
                api_key=api_key,
                base_url=base_url,
                timeout_seconds=args.advice_timeout,
            )
        )
    except AdviceError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 3
    return 0


def _env(name: str) -> str:
    import os

    return os.environ.get(name, "")


if __name__ == "__main__":
    raise SystemExit(main())
