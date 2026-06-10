from pathlib import Path

from stellaris_advisor.analyzer import build_report, render_markdown
from stellaris_advisor.save_reader import read_save


FIXTURE = Path(__file__).parent.parent / "examples" / "sample_meta_only.sav"


def test_read_save_metadata() -> None:
    save = read_save(FIXTURE)

    assert save.metadata.version == "3.12.5"
    assert save.metadata.name == "Example Campaign"
    assert save.metadata.date == "2230.01.01"
    assert save.metadata.player_country == 0
    assert save.metadata.ironman is False


def test_build_report_renders_markdown() -> None:
    save = read_save(FIXTURE)
    report = build_report(save)
    markdown = render_markdown(report)

    assert "Stellaris Advisor Report" in markdown
    assert "游戏版本: 3.12.5" in markdown
    assert "下一步开发" in markdown

