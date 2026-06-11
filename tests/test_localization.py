from __future__ import annotations

from pathlib import Path

from stellaris_advisor.localization import load_localization_catalog
from stellaris_advisor.report_language import ReportLanguage


def test_load_localization_catalog_from_directory(tmp_path: Path) -> None:
    localization_dir = tmp_path / "localisation" / "simp_chinese"
    localization_dir.mkdir(parents=True)
    (localization_dir / "test_l_simp_chinese.yml").write_text(
        """
l_simp_chinese:
 tech_starbase_2:0 "星垒"
 civic_machine_servitor:0 "失控机仆"
 civic_wrapped:0 "$civic_machine_servitor$"
 colored_name:0 "§Y高亮名称§!"
""",
        encoding="utf-8",
    )

    catalog = load_localization_catalog(tmp_path, ReportLanguage.ZH)

    assert catalog.lookup("tech_starbase_2") == "星垒"
    assert catalog.lookup("civic_wrapped") == "失控机仆"
    assert catalog.lookup("colored_name") == "高亮名称"


def test_load_localization_catalog_from_english_file(tmp_path: Path) -> None:
    file_path = tmp_path / "advisor_l_english.yml"
    file_path.write_text(
        """
l_english:
 civic_machine_servitor:0 "Rogue Servitor"
 tech_starbase_2:0 "Starhold"
""",
        encoding="utf-8",
    )

    catalog = load_localization_catalog(file_path, ReportLanguage.EN)

    assert catalog.lookup("civic_machine_servitor") == "Rogue Servitor"
    assert catalog.lookup("tech_starbase_2") == "Starhold"
