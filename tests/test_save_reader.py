from pathlib import Path
from zipfile import ZipFile

from stellaris_advisor.analyzer import build_report, render_markdown
from stellaris_advisor.save_reader import read_save
from stellaris_advisor.visibility import VisibilityMode


FIXTURE = Path(__file__).parent.parent / "examples" / "sample_meta_only.sav"


def test_read_save_metadata() -> None:
    save = read_save(FIXTURE)

    assert save.metadata.version == "3.12.5"
    assert save.metadata.name == "Example Campaign"
    assert save.metadata.date == "2230.01.01"
    assert save.metadata.player_country == 0
    assert save.metadata.ironman is False
    assert save.player_empire is not None
    assert save.player_empire.name == "United Nations of Earth"


def test_build_report_renders_markdown() -> None:
    save = read_save(FIXTURE)
    report = build_report(save)
    markdown = render_markdown(report)

    assert "Stellaris Advisor Report" in markdown
    assert report.visibility_mode is VisibilityMode.PLAYER_VISIBLE
    assert "可见性模式: `player_visible`" in markdown
    assert "游戏版本: 3.12.5" in markdown
    assert "下一步开发" in markdown


def test_read_player_empire_deep_fields(tmp_path: Path) -> None:
    save_path = tmp_path / "deep_fields.sav"
    meta = 'version="4.3.7"\nname="Deep Fields"\ndate="2253.09.14"\n'
    gamestate = """
version="4.3.7"
name="Deep Fields"
date="2253.09.14"
player=
{
    {
        name="unknown"
        country=0
    }
}
country=
{
    0=
    {
        name={ key="Test Hive" literal=yes }
        founder_species_ref=42
        ethos={ ethic="ethic_gestalt_consciousness" }
        government=
        {
            type="gov_hive_mind"
            authority="auth_hive_mind"
            civics={ "civic_hive_one_mind" "civic_environmental_architects_hive" }
            origin="origin_progenitor_hive"
            council_agenda="agenda_departmental_efficiency"
            council_agenda_progress=3387.2
        }
        policy_flags={ "diplo_stance_isolationist" "unrestricted_wars" }
        owned_leaders={ 10 11 12 }
        tradition_categories={ "tradition_prosperity" "tradition_supremacy" }
        traditions={ "tr_prosperity_adopt" "tr_supremacy_adopt" }
        ascension_perks={ "ap_technological_ascendancy" }
        edicts=
        {
            { edict="farming_subsidies" }
            { edict="drone_overdrive" }
        }
        owned_planets={ 3 197 }
        budget=
        {
            resources=
            {
                energy=100
                alloys=20
                physics_research=30
            }
        }
    }
}
"""
    with ZipFile(save_path, "w") as archive:
        archive.writestr("meta", meta)
        archive.writestr("gamestate", gamestate)

    save = read_save(save_path)

    assert save.metadata.player_country == 0
    assert save.player_empire is not None
    empire = save.player_empire
    assert empire.name == "Test Hive"
    assert empire.founder_species_id == 42
    assert empire.ethics == ["ethic_gestalt_consciousness"]
    assert empire.government_type == "gov_hive_mind"
    assert empire.authority == "auth_hive_mind"
    assert empire.civics == ["civic_hive_one_mind", "civic_environmental_architects_hive"]
    assert empire.origin == "origin_progenitor_hive"
    assert empire.council_agenda == "agenda_departmental_efficiency"
    assert empire.council_agenda_progress == 3387.2
    assert empire.tradition_categories == ["tradition_prosperity", "tradition_supremacy"]
    assert empire.traditions == ["tr_prosperity_adopt", "tr_supremacy_adopt"]
    assert empire.ascension_perks == ["ap_technological_ascendancy"]
    assert empire.edicts == ["farming_subsidies", "drone_overdrive"]
    assert empire.policy_flags == ["diplo_stance_isolationist", "unrestricted_wars"]
    assert empire.owned_leaders == [10, 11, 12]
    assert empire.owned_planets == [3, 197]
    assert empire.monthly_income["alloys"] == 20
