from pathlib import Path

from stellaris_advisor.advice import build_advice_prompt
from stellaris_advisor.analyzer import build_report
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
    assert "普通前哨站不占恒星基地容量" in rendered
    assert "容量占用/上限" in rendered
    assert "戒心永存" in rendered
    assert "法令" in rendered
    assert "恒星基地" in rendered
    assert "存档摘要" in rendered


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
