from stellaris_advisor.display_names import compact_name, display_name


def test_display_name_keeps_raw_identifier() -> None:
    assert display_name("tech_starbase_2") == "Technology: Starbase II [tech_starbase_2]"
    assert display_name("ap_cosmogenesis") == "Ascension Perk: Cosmogenesis [ap_cosmogenesis]"


def test_compact_name_formats_components() -> None:
    assert compact_name("SMALL_MASS_DRIVER_1") == "Small Mass Driver I"
    assert compact_name("starbase_level_starhold") == "Starbase Level Starhold"
