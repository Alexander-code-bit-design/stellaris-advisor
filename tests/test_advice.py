from pathlib import Path

from stellaris_advisor.advice import build_advice_prompt
from stellaris_advisor.analyzer import build_report
from stellaris_advisor.knowledge import KnowledgeHit, KnowledgeRecord
from stellaris_advisor.report_language import ReportLanguage
from stellaris_advisor.save_reader import read_save
from stellaris_advisor.visibility import VisibilityMode


FIXTURE = Path(__file__).parent.parent / "examples" / "sample_meta_only.sav"


def test_build_chinese_advice_prompt_includes_visibility_guard() -> None:
    save = read_save(FIXTURE)
    report = build_report(save, visibility_mode=VisibilityMode.PLAYER_VISIBLE)

    prompt = build_advice_prompt(report, focus="我应该先发展科研还是舰队？")
    rendered = prompt.render()

    assert "player_visible" in rendered
    assert "不得主动泄露" in rendered
    assert "我应该先发展科研还是舰队？" in rendered
    assert "不要把“军事实力为 0”自动判定为极端危机" in rendered
    assert "不要把所有 hostile 目标都当成会主动进攻的敌国舰队" in rendered
    assert "普通前哨站不占恒星基地容量" in rendered
    assert "容量占用/上限" in rendered
    assert "戒心永存" in rendered
    assert "法令" in rendered
    assert "恒星基地" in rendered
    assert "存档事实摘要" in rendered
    assert "发现的问题" not in rendered
    assert "下一步开发" not in rendered


def test_build_english_advice_prompt_uses_english_structure() -> None:
    save = read_save(FIXTURE)
    report = build_report(save, language=ReportLanguage.EN)

    prompt = build_advice_prompt(report)
    rendered = prompt.render()

    assert "Reply in English" in rendered
    assert "Known facts" in rendered
    assert "capacity used / cap" in rendered
    assert "Concrete actions" in rendered
    assert "Starbases" in rendered
    assert "Game version: 3.12.5" in rendered
    assert "Findings" not in rendered
    assert "Next Development Steps" not in rendered


def test_build_advice_prompt_can_include_retrieved_knowledge() -> None:
    save = read_save(FIXTURE)
    report = build_report(save, language=ReportLanguage.EN)
    hit = KnowledgeHit(
        record=KnowledgeRecord(
            record_id="wiki-starbase-cap",
            source_type="wiki",
            title="Starbase Capacity",
            url="https://example.test/starbase",
            version="3.12",
            topics=["starbase"],
            confidence="high",
            text="Outposts do not use upgraded starbase capacity.",
        ),
        score=3.5,
    )

    prompt = build_advice_prompt(report, knowledge_hits=[hit])
    rendered = prompt.render()

    assert "Retrieved Knowledge Evidence" in rendered
    assert "Starbase Capacity" in rendered
    assert "Outposts do not use upgraded starbase capacity." in rendered
