from pathlib import Path
from zipfile import ZipFile

from stellaris_advisor.analyzer import build_report, render_markdown
from stellaris_advisor.detail_level import DetailLevel
from stellaris_advisor.report_language import ReportLanguage
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


def test_build_report_renders_english_markdown() -> None:
    save = read_save(FIXTURE)
    report = build_report(save, language=ReportLanguage.EN)
    markdown = render_markdown(report)

    assert report.language is ReportLanguage.EN
    assert "Visibility mode: `player_visible`" in markdown
    assert "## Situation Summary" in markdown
    assert "Game version: 3.12.5" in markdown
    assert "## Next Development Steps" in markdown


def test_detail_level_controls_report_expansion() -> None:
    save = read_save(FIXTURE)
    summary_report = build_report(save, detail_level=DetailLevel.SUMMARY)
    full_report = build_report(save, detail_level=DetailLevel.FULL)

    summary_markdown = render_markdown(summary_report)
    full_markdown = render_markdown(full_report)

    assert "领袖概览" not in summary_markdown
    assert "领袖细节" in full_markdown
    assert "恒星基地细节" in full_markdown


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
        owned_fleets={ { fleet=100 } { fleet=101 } }
        starbase_capacity=5
        ship_design_collection=
        {
            ship_design={ 200 201 }
            auto_gen_design=no
        }
        tech_status=
        {
            technology="tech_space_exploration"
            level=1
            technology="tech_starbase_2"
            level=1
        }
        tradition_categories={ "tradition_prosperity" "tradition_supremacy" }
        traditions={ "tr_prosperity_adopt" "tr_supremacy_adopt" }
        ascension_perks={ "ap_technological_ascendancy" }
        edicts=
        {
            { edict="farming_subsidies" }
            { edict="drone_overdrive" }
        }
        standard_pop_factions_module=
        {
            total_faction_members_power=0
            total_faction_members=0
        }
        owned_planets={ 3 197 }
        budget=
        {
            current_month=
            {
                income=
                {
                    country_base=
                    {
                        energy=100
                        alloys=20
                    }
                    orbital_research_deposits=
                    {
                        physics_research=30
                    }
                }
            }
        }
    }
}
planets=
{
    3=
    {
        name={ key="Capital" literal=yes }
        planet_class="pc_continental"
        planet_size=20
        owner=0
        controller=0
        governor=10
        districts={ 1 2 3 }
        buildings_cache={ 4 5 }
        deposits={ 6 7 }
        pop_groups={ 8 9 }
        pop_jobs={ 10 11 12 }
        stability=70
        crime=1.5
        amenities=30
        amenities_usage=20
        free_amenities=10
        free_housing=5
        total_housing=60
        housing_usage=55
        num_sapient_pops=52
        designation="col_capital"
        final_designation="col_capital"
        ascension_tier=1
        upkeep={ energy=2 }
        produces={ minerals=10 }
        profits={ minerals=8 }
    }
    197=
    {
        name=
        {
            key="NEW_COLONY_NAME_1"
            variables={ { key="NAME" value={ key="Strom" } } }
        }
        planet_class="pc_ocean"
        planet_size=14
        owner=0
        controller=0
        stability=45
        free_housing=-1
        free_amenities=-2
        num_sapient_pops=10
    }
}
galactic_object=
{
    77=
    {
        name={ key="Test System" }
        starbases={ 5 }
    }
}
starbase_mgr=
{
    starbases=
    {
        5=
        {
            level="starbase_level_starport"
            type="sshipyard"
            modules={ 0=shipyard 1=solar_panel_network }
            buildings={ 0=crew_quarters }
            nested_table=
            {
                5={ should_not_duplicate=yes }
            }
            station=50
            build_queue=60
            shipyard_build_queue=61
            construction_type=starbase_shipyard
        }
        6=
        {
            level="starbase_level_outpost"
            station=51
        }
    }
}
ships=
{
    50={ fleet=100 }
    51={ fleet=999 }
}
fleet=
{
    100=
    {
        name={ key="shipclass_starbase_name" }
        ship_class=shipclass_starbase
        military_power=123.5
    }
    999=
    {
        ship_class=shipclass_starbase
        military_power=999
    }
}
megastructures=
{
    1=
    {
        name={ key="Grand Archive" }
        type="grand_archive_0"
        coordinate={ x=1 y=2 origin=77 }
        owner=0
        planet=3
        build_queue=4294967295
        dismantle_progress=0
    }
    2=
    {
        type="ring_world_ruined"
        owner=9
        planet=4294967295
    }
}
ship_design=
{
    200=
    {
        name={ key="Test Corvette" }
        auto_gen_design=yes
        growth_stages=
        {
            {
                ship_size="corvette"
                section=
                {
                    template="CORVETTE_MID_S3"
                    component={ slot="SMALL_GUN_01" template="SMALL_LASER_1" }
                    component={ slot="SMALL_UTILITY_1" template="SMALL_SHIELD_1" }
                }
                required_component="CORVETTE_FISSION_REACTOR"
                required_component="HYPER_DRIVE_1"
            }
        }
    }
    201=
    {
        name={ key="Test Constructor" }
        auto_gen_design=no
        growth_stages=
        {
            {
                ship_size="constructor"
                section={ template="BULWARK_BATTLEWRIGHT_SECTION" }
            }
        }
    }
}
leaders=
{
    10=
    {
        name={ full_names={ key="Leader One" } }
        class="official"
        gender=female
        age=40
        job="politician"
        ethic="ethic_authoritarian"
        location={ type=planet id=3 }
        council_location={ type=council_position id=99 }
        traits="leader_trait_principled"
        level=2
    }
    11=
    {
        name=
        {
            full_names=
            {
                key="%LEADER_2%"
                variables=
                {
                    { key="1" value={ key="First" } }
                    { key="2" value={ key="Second" } }
                }
            }
        }
        class="scientist"
        traits="leader_trait_spark_of_genius"
        level=3
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
    assert len(empire.leaders) == 2
    assert empire.leaders[0].name == "Leader One"
    assert empire.leaders[0].leader_class == "official"
    assert empire.leaders[0].level == 2
    assert empire.leaders[0].location_type == "planet"
    assert empire.leaders[0].location_id == 3
    assert empire.leaders[0].council_position_id == 99
    assert empire.leaders[0].traits == ["leader_trait_principled"]
    assert empire.leaders[1].name == "First Second"
    assert empire.leaders[1].leader_class == "scientist"
    assert empire.leaders[1].traits == ["leader_trait_spark_of_genius"]
    assert empire.pop_factions_applicable is False
    assert empire.pop_faction_members == 0
    assert empire.owned_fleets == [100, 101]
    assert empire.starbase_capacity == 5
    assert len(empire.starbases) == 1
    assert empire.starbases[0].starbase_id == 5
    assert empire.starbases[0].system_id == 77
    assert empire.starbases[0].system_name == "Test System"
    assert empire.starbases[0].level == "starbase_level_starport"
    assert empire.starbases[0].modules == ["shipyard", "solar_panel_network"]
    assert empire.starbases[0].buildings == ["crew_quarters"]
    assert empire.starbases[0].fleet_id == 100
    assert empire.starbases[0].military_power == 123.5
    assert len(empire.megastructures) == 1
    assert empire.megastructures[0].megastructure_type == "grand_archive_0"
    assert empire.megastructures[0].system_id == 77
    assert empire.megastructures[0].planet_id == 3
    assert empire.ship_design_ids == [200, 201]
    assert len(empire.ship_designs) == 2
    assert empire.ship_designs[0].name == "Test Corvette"
    assert empire.ship_designs[0].ship_size == "corvette"
    assert empire.ship_designs[0].auto_generated is True
    assert empire.ship_designs[0].section_templates == ["CORVETTE_MID_S3"]
    assert empire.ship_designs[0].component_templates == ["SMALL_LASER_1", "SMALL_SHIELD_1"]
    assert empire.ship_designs[0].required_components == [
        "CORVETTE_FISSION_REACTOR",
        "HYPER_DRIVE_1",
    ]
    assert empire.technologies == {
        "tech_space_exploration": 1,
        "tech_starbase_2": 1,
    }
    assert empire.owned_planets == [3, 197]
    assert len(empire.planets) == 2
    assert empire.planets[0].name == "Capital"
    assert empire.planets[0].planet_class == "pc_continental"
    assert empire.planets[0].planet_size == 20
    assert empire.planets[0].districts == [1, 2, 3]
    assert empire.planets[0].buildings == [4, 5]
    assert empire.planets[0].num_sapient_pops == 52
    assert empire.planets[0].stability == 70
    assert empire.planets[0].free_housing == 5
    assert empire.planets[0].profits["minerals"] == 8
    assert empire.planets[1].name == "Strom"
    assert empire.planets[1].free_housing == -1
    assert empire.monthly_income["alloys"] == 20


def test_read_normal_empire_pop_faction_module(tmp_path: Path) -> None:
    save_path = tmp_path / "normal_factions.sav"
    meta = 'version="4.3.7"\nname="Normal"\ndate="2200.01.10"\n'
    gamestate = """
version="4.3.7"
name="Normal"
date="2200.01.10"
player=
{
    {
        country=0
    }
}
country=
{
    0=
    {
        name={ key="Normal Empire" literal=yes }
        ethos=
        {
            ethic="ethic_authoritarian"
            ethic="ethic_materialist"
        }
        government=
        {
            type="gov_executive_committee"
            authority="auth_oligarchic"
            civics={ "civic_meritocracy" }
            origin="origin_default"
        }
        standard_pop_factions_module=
        {
            total_faction_members_power=0
            total_faction_members=0
        }
        budget=
        {
            current_month=
            {
                income=
                {
                    country_base={ energy=20 minerals=20 }
                    trade_policy={ energy=5 trade=5 }
                }
            }
        }
    }
}
"""
    with ZipFile(save_path, "w") as archive:
        archive.writestr("meta", meta)
        archive.writestr("gamestate", gamestate)

    save = read_save(save_path)

    assert save.player_empire is not None
    empire = save.player_empire
    assert empire.pop_factions_applicable is True
    assert empire.pop_faction_members == 0
    assert empire.monthly_income["energy"] == 25
    assert empire.monthly_income["minerals"] == 20
