from stellaris_advisor.display_names import (
    compact_name,
    display_name,
    set_localization_catalog,
)
from stellaris_advisor.localization import LocalizationCatalog
from stellaris_advisor.report_language import ReportLanguage


def test_display_name_keeps_raw_identifier() -> None:
    assert display_name("tech_starbase_2") == "Technology: Starbase II [tech_starbase_2]"
    assert display_name("ap_cosmogenesis") == "Ascension Perk: Cosmogenesis [ap_cosmogenesis]"


def test_compact_name_formats_components() -> None:
    assert compact_name("SMALL_MASS_DRIVER_1") == "Small Mass Driver I"
    assert compact_name("starbase_level_starhold") == "Starbase Level Starhold"


def test_display_name_prefers_loaded_localization() -> None:
    catalog = LocalizationCatalog(
        language=ReportLanguage.ZH,
        entries={
            "tech_starbase_2": "星垒",
            "shipclass_starbase": "恒星基地",
        },
    )

    assert display_name("tech_starbase_2", catalog=catalog) == "星垒 [tech_starbase_2]"
    assert compact_name("shipclass_starbase", catalog=catalog) == "恒星基地"


def test_display_name_global_catalog_can_be_reset() -> None:
    catalog = LocalizationCatalog(
        language=ReportLanguage.EN,
        entries={"civic_machine_servitor": "Rogue Servitor"},
    )
    set_localization_catalog(catalog)
    try:
        assert display_name("civic_machine_servitor") == "Rogue Servitor [civic_machine_servitor]"
    finally:
        set_localization_catalog(None)
