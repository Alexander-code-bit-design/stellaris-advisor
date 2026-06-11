from __future__ import annotations

from .detail_level import DetailLevel
from .display_names import compact_name, display_name
from .models import AdvisorReport, EmpireSummary, Finding, SaveGame
from .report_language import ReportLanguage
from .visibility import VisibilityMode


def build_report(
    save: SaveGame,
    visibility_mode: VisibilityMode = VisibilityMode.PLAYER_VISIBLE,
    language: ReportLanguage = ReportLanguage.ZH,
    detail_level: DetailLevel = DetailLevel.STANDARD,
) -> AdvisorReport:
    if language is ReportLanguage.EN:
        return _build_english_report(save, visibility_mode, language, detail_level)

    meta = save.metadata
    empire = save.player_empire
    summary = [
        f"存档名称: {meta.name or '未知'}",
        f"游戏版本: {meta.version or '未知'}",
        f"当前日期: {meta.date or '未知'}",
        f"玩家国家 ID: {meta.player_country if meta.player_country is not None else '未知'}",
        f"铁人模式: {_format_bool(meta.ironman)}",
    ]
    if empire is not None:
        summary.extend(
            [
                f"玩家帝国: {empire.name or '未知'}",
                f"政体/权力: {_format_id_value(empire.government_type)} / {_format_id_value(empire.authority)}",
                f"起源: {_format_id_value(empire.origin)}",
                f"思潮: {_format_id_list(empire.ethics)}",
                f"国民理念: {_format_id_list(empire.civics)}",
                f"传统组: {_format_id_list(empire.tradition_categories)}",
                f"已选传统数: {len(empire.traditions)}",
                f"传统明细: {_format_tradition_details(empire)}",
                f"飞升: {_format_id_list(empire.ascension_perks)}",
                f"当前议程: {_format_id_value(empire.council_agenda)} ({_format_number(empire.council_agenda_progress)})",
                f"启用法令: {_format_id_list(empire.edicts)}",
                f"政策标记: {_format_id_list(empire.policy_flags, limit=6)}",
                f"领袖数量: {len(empire.leaders) or len(empire.owned_leaders)}",
                f"派系状态: {_format_faction_status(empire)}",
                f"殖民地数量: {len(empire.planets) or len(empire.owned_planets)}",
                f"星球概览: {_format_planets(empire)}",
                f"恒星基地: {len(empire.starbases)} / {_format_number(empire.starbase_capacity)}",
                f"恒星基地概览: {_format_starbases(empire, detail_level)}",
                f"巨型结构: {_format_megastructures(empire)}",
                f"舰船设计: {_format_ship_designs(empire, detail_level)}",
                f"已研究科技: {_format_technologies(empire)}",
                f"帝国规模: {_format_number(empire.empire_size)}",
                f"智慧人口: {_format_number(empire.sapient_pops)}",
                f"舰队容量使用: {_format_number(empire.used_naval_capacity)}",
                f"经济实力: {_format_number(empire.economy_power)}",
                f"军事实力: {_format_number(empire.military_power)}",
                f"胜利排名: {_format_number(empire.victory_rank)}",
            ]
        )
        if detail_level is not DetailLevel.SUMMARY:
            summary.insert(21, f"领袖概览: {_format_leaders(empire, detail_level)}")
        if empire.monthly_income:
            summary.append(f"月收入概览: {_format_resources(empire.monthly_income)}")
        if detail_level is DetailLevel.FULL:
            summary.extend(_format_full_detail_lines(empire))

    findings: list[Finding] = []
    if meta.version is None:
        findings.append(
            Finding(
                title="缺少版本信息",
                severity="medium",
                detail="没有从 meta 中解析到明确的 Stellaris 版本。",
                recommendation="后续建议必须降低置信度，并优先让用户确认游戏版本、DLC 和 mod 列表。",
            )
        )

    if empire is None:
        findings.append(
            Finding(
                title="尚未定位玩家帝国",
                severity="medium",
                detail="没有从 player/country 数据中找到玩家国家对应的 country block。",
                recommendation="先确认 player country ID 的解析规则，再展开该 country block。",
            )
        )

    if empire is not None and not empire.monthly_income:
        findings.append(
            Finding(
                title="尚未提取月收入",
                severity="medium",
                detail="已定位玩家帝国，但没有找到 budget/current_month/income/resources 汇总。",
                recommendation="检查该版本存档中的 budget 字段结构，并补充兼容解析。",
            )
        )

    if empire is not None:
        findings.extend(_build_empire_findings(empire))
        findings.extend(_build_planet_findings(empire))

    if empire is not None and not empire.planets:
        findings.append(
            Finding(
                title="星球数据尚未结构化",
                severity="low",
                detail="MVP 已读取 gamestate，但还没有展开星球块。",
                recommendation="下一步实现 planet block 解析，提取住房、就业、稳定度、区划和建筑队列。",
            )
        )

    next_steps = [
        "细化星球解析：把区划、建筑、岗位 ID 映射到定义名，并提取建造队列和失业/岗位缺口。",
        "解析舰队、外交、边境与 chokepoint，用上下文判断无常备舰队是否是合理维护费策略。",
        "解析领袖详情和内阁席位，把 owned_leaders ID 映射到姓名、等级、岗位和特质。",
        "解析 galactic_object 和超空间航道，并在 player_visible 模式下做边境与 chokepoint 分析。",
        "建立按版本标记的 wiki/patch/community 知识库，让 LLM 基于结构化摘要和检索证据生成建议。",
    ]

    return AdvisorReport(
        visibility_mode=visibility_mode,
        language=language,
        detail_level=detail_level,
        summary=summary,
        findings=findings,
        next_steps=next_steps,
    )


def _build_english_report(
    save: SaveGame,
    visibility_mode: VisibilityMode,
    language: ReportLanguage,
    detail_level: DetailLevel,
) -> AdvisorReport:
    meta = save.metadata
    empire = save.player_empire
    summary = [
        f"Save name: {meta.name or 'unknown'}",
        f"Game version: {meta.version or 'unknown'}",
        f"Current date: {meta.date or 'unknown'}",
        f"Player country ID: {meta.player_country if meta.player_country is not None else 'unknown'}",
        f"Ironman: {_format_bool_en(meta.ironman)}",
    ]
    if empire is not None:
        summary.extend(
            [
                f"Player empire: {empire.name or 'unknown'}",
                f"Government/authority: {_format_id_value(empire.government_type)} / {_format_id_value(empire.authority)}",
                f"Origin: {_format_id_value(empire.origin)}",
                f"Ethics: {_format_id_list(empire.ethics)}",
                f"Civics: {_format_id_list(empire.civics)}",
                f"Tradition trees: {_format_id_list_en(empire.tradition_categories)}",
                f"Selected traditions: {len(empire.traditions)}",
                f"Tradition details: {_format_tradition_details_en(empire)}",
                f"Ascension perks: {_format_id_list_en(empire.ascension_perks)}",
                f"Current agenda: {_format_id_value(empire.council_agenda)} ({_format_number(empire.council_agenda_progress)})",
                f"Active edicts: {_format_id_list_en(empire.edicts)}",
                f"Policy flags: {_format_id_list_en(empire.policy_flags, limit=6)}",
                f"Leaders: {len(empire.leaders) or len(empire.owned_leaders)}",
                f"Faction status: {_format_faction_status_en(empire)}",
                f"Colonies: {len(empire.planets) or len(empire.owned_planets)}",
                f"Planet overview: {_format_planets(empire)}",
                f"Starbases: {len(empire.starbases)} / {_format_number(empire.starbase_capacity)}",
                f"Starbase overview: {_format_starbases(empire, detail_level)}",
                f"Megastructures: {_format_megastructures_en(empire)}",
                f"Ship designs: {_format_ship_designs(empire, detail_level)}",
                f"Researched technologies: {_format_technologies_en(empire)}",
                f"Empire size: {_format_number(empire.empire_size)}",
                f"Sapient pops: {_format_number(empire.sapient_pops)}",
                f"Used naval capacity: {_format_number(empire.used_naval_capacity)}",
                f"Economy power: {_format_number(empire.economy_power)}",
                f"Military power: {_format_number(empire.military_power)}",
                f"Victory rank: {_format_number(empire.victory_rank)}",
            ]
        )
        if detail_level is not DetailLevel.SUMMARY:
            summary.insert(21, f"Leader overview: {_format_leaders(empire, detail_level)}")
        if empire.monthly_income:
            summary.append(f"Monthly income: {_format_resources(empire.monthly_income)}")
        if detail_level is DetailLevel.FULL:
            summary.extend(_format_full_detail_lines_en(empire))

    findings: list[Finding] = []
    if meta.version is None:
        findings.append(
            Finding(
                title="Missing game version",
                severity="medium",
                detail="No clear Stellaris version was parsed from the save metadata.",
                recommendation="Lower advice confidence and ask the player to confirm version, DLCs, and mods.",
            )
        )
    if empire is None:
        findings.append(
            Finding(
                title="Player empire not located",
                severity="medium",
                detail="The parser could not match the player country ID to a country block.",
                recommendation="Confirm player country parsing before analyzing empire state.",
            )
        )
    if empire is not None and not empire.monthly_income:
        findings.append(
            Finding(
                title="Monthly income not extracted",
                severity="medium",
                detail="The player empire was found, but no monthly resource income summary was parsed.",
                recommendation="Inspect this save version's budget/current_month/income structure and add compatibility handling.",
            )
        )
    if empire is not None:
        findings.extend(_build_empire_findings_en(empire))
        findings.extend(_build_planet_findings_en(empire))
        if not empire.planets:
            findings.append(
                Finding(
                    title="Planet data not structured",
                    severity="low",
                    detail="The save was read, but no owned planet details were extracted.",
                    recommendation="Expand planet parsing for housing, jobs, stability, districts, and construction queues.",
                )
            )

    next_steps = [
        "Replace fallback ID formatting with version-aware game localization data for English and Chinese.",
        "Extract planet construction queues, unemployment/job gaps, districts, and building definition names.",
        "Parse fleets, diplomacy, borders, and chokepoints so a zero standing fleet can be judged in context.",
        "Parse galactic objects and hyperlanes for player-visible border and chokepoint analysis.",
        "Build a version-tagged wiki/patch/community knowledge index for evidence-backed LLM answers.",
    ]

    return AdvisorReport(
        visibility_mode=visibility_mode,
        language=language,
        detail_level=detail_level,
        summary=summary,
        findings=findings,
        next_steps=next_steps,
    )


def render_markdown(report: AdvisorReport) -> str:
    is_en = report.language is ReportLanguage.EN
    lines = [
        "# Stellaris Advisor Report",
        "",
        f"{'Visibility mode' if is_en else '可见性模式'}: `{report.visibility_mode.value}`",
        "",
        f"## {'Situation Summary' if is_en else '局势摘要'}",
    ]
    if report.visibility_mode is VisibilityMode.PLAYER_VISIBLE:
        lines.extend(
            [
                "",
                "> Advice is generated from player-visible information only; hidden AI intelligence, undiscovered systems, and spoiler data must not enter the report."
                if is_en
                else "> 默认仅基于玩家可见信息生成建议；隐藏 AI 情报、未发现星系和剧透信息不得进入报告。",
            ]
        )
    elif report.visibility_mode is VisibilityMode.OMNISCIENT:
        lines.extend(
            [
                "",
                "> Warning: omniscient/spoiler mode may include information not normally visible during play."
                if is_en
                else "> 警告：当前为全知/剧透模式，后续版本可能显示正常游玩不可见的信息。",
            ]
        )
    lines.extend(f"- {item}" for item in report.summary)
    lines.extend(["", f"## {'Findings' if is_en else '发现的问题'}"])
    if report.findings:
        for finding in report.findings:
            lines.extend(
                [
                    f"### [{finding.severity}] {finding.title}",
                    finding.detail,
                    "",
                    f"{'Recommendation' if is_en else '建议'}: {finding.recommendation}",
                    "",
                ]
            )
    else:
        lines.append("- No obvious issues found." if is_en else "- 暂未发现明显问题。")
    lines.extend(["", f"## {'Next Development Steps' if is_en else '下一步开发'}"])
    lines.extend(f"- {step}" for step in report.next_steps)
    return "\n".join(lines).strip() + "\n"


def _format_bool(value: bool | None) -> str:
    if value is None:
        return "未知"
    return "是" if value else "否"


def _format_bool_en(value: bool | None) -> str:
    if value is None:
        return "unknown"
    return "yes" if value else "no"


def _format_number(value: object) -> str:
    if value is None:
        return "未知"
    if isinstance(value, float):
        return f"{value:.1f}".rstrip("0").rstrip(".")
    return str(value)


def _format_value(value: object) -> str:
    if value is None or value == "":
        return "未知"
    return str(value)


def _format_id_value(value: object) -> str:
    if value is None or value == "":
        return "未知"
    return display_name(value)


def _format_name(value: object) -> str | None:
    if value is None or value == "":
        return None
    text = str(value)
    if text.startswith(("NAME_", "SPEC_")):
        return compact_name(text)
    return text


def _format_list(values: list[object], limit: int = 8) -> str:
    if not values:
        return "未知"
    shown = [str(value) for value in values[:limit]]
    suffix = f" (+{len(values) - limit})" if len(values) > limit else ""
    return ", ".join(shown) + suffix


def _format_id_list(values: list[object], limit: int = 8) -> str:
    if not values:
        return "未知"
    shown = [display_name(value) for value in values[:limit]]
    suffix = f" (+{len(values) - limit})" if len(values) > limit else ""
    return ", ".join(shown) + suffix


def _format_id_list_en(values: list[object], limit: int = 8) -> str:
    if not values:
        return "unknown"
    shown = [display_name(value) for value in values[:limit]]
    suffix = f" (+{len(values) - limit})" if len(values) > limit else ""
    return ", ".join(shown) + suffix


def _format_faction_status(empire: EmpireSummary) -> str:
    if empire.pop_factions_applicable is False:
        return "不适用（格式塔或无派系政体）"
    if empire.pop_factions_applicable is None:
        return "未知"
    if empire.pop_faction_members is None:
        return "适用，但尚未解析成员数"
    if empire.pop_faction_members == 0:
        return "适用，但当前尚未形成派系"
    return f"适用，派系成员 {empire.pop_faction_members}"


def _format_faction_status_en(empire: EmpireSummary) -> str:
    if empire.pop_factions_applicable is False:
        return "not applicable (gestalt or factionless authority)"
    if empire.pop_factions_applicable is None:
        return "unknown"
    if empire.pop_faction_members is None:
        return "applicable, but member count has not been parsed"
    if empire.pop_faction_members == 0:
        return "applicable, but no factions have formed yet"
    return f"applicable, {empire.pop_faction_members} faction members"


def _format_leaders(
    empire: EmpireSummary,
    detail_level: DetailLevel = DetailLevel.STANDARD,
    limit: int = 6,
) -> str:
    if not empire.leaders:
        return "尚未解析详情"
    parts = []
    for leader in empire.leaders[:limit]:
        traits = ""
        if detail_level is DetailLevel.FULL and leader.traits:
            traits = f"; traits {', '.join(display_name(trait) for trait in leader.traits)}"
        location = ""
        if leader.location_type:
            location = f"; {leader.location_type}"
            if leader.location_id is not None:
                location += f" {leader.location_id}"
        council = ""
        if leader.council_position_id is not None:
            council = f"; council {leader.council_position_id}"
        parts.append(
            f"{_format_name(leader.name) or leader.leader_id} ({leader.leader_class or 'unknown'} L{_format_number(leader.level)}{location}{council}{traits})"
        )
    suffix = f" (+{len(empire.leaders) - limit})" if len(empire.leaders) > limit else ""
    return " | ".join(parts) + suffix


def _format_planets(empire: EmpireSummary, limit: int = 6) -> str:
    if not empire.planets:
        return "尚未解析详情"
    parts = []
    for planet in empire.planets[:limit]:
        stats = [
            compact_name(planet.planet_class) if planet.planet_class else "unknown",
            f"size {_format_number(planet.planet_size)}",
            f"pops {_format_number(planet.num_sapient_pops)}",
            f"stab {_format_number(planet.stability)}",
            f"housing {_format_number(planet.free_housing)}",
            f"amen {_format_number(planet.free_amenities)}",
        ]
        if planet.designation:
            stats.append(compact_name(planet.designation))
        parts.append(f"{_format_name(planet.name) or planet.planet_id} ({', '.join(stats)})")
    suffix = f" (+{len(empire.planets) - limit})" if len(empire.planets) > limit else ""
    return " | ".join(parts) + suffix


def _format_starbases(
    empire: EmpireSummary,
    detail_level: DetailLevel = DetailLevel.STANDARD,
    limit: int = 6,
) -> str:
    if not empire.starbases:
        return "尚未解析详情"
    parts = []
    for starbase in empire.starbases[:limit]:
        system = _format_name(starbase.system_name) or (
            f"system {starbase.system_id}" if starbase.system_id is not None else "unknown system"
        )
        modules = ""
        buildings = ""
        if detail_level is DetailLevel.FULL:
            modules = (
                f"; modules {', '.join(compact_name(module) for module in starbase.modules)}"
                if starbase.modules
                else ""
            )
            buildings = (
                f"; buildings {', '.join(compact_name(building) for building in starbase.buildings)}"
                if starbase.buildings
                else ""
            )
        parts.append(
            f"{system} ({compact_name(starbase.level) if starbase.level else 'unknown'}, power {_format_number(starbase.military_power)}{modules}{buildings})"
        )
    suffix = f" (+{len(empire.starbases) - limit})" if len(empire.starbases) > limit else ""
    return " | ".join(parts) + suffix


def _format_megastructures(empire: EmpireSummary, limit: int = 6) -> str:
    if not empire.megastructures:
        return "未发现玩家拥有的巨型结构"
    parts = []
    for megastructure in empire.megastructures[:limit]:
        location = ""
        if megastructure.system_id is not None:
            location = f", system {megastructure.system_id}"
        parts.append(
            f"{_format_name(megastructure.name) or megastructure.megastructure_id} "
            f"({_format_id_value(megastructure.megastructure_type)}{location})"
        )
    suffix = (
        f" (+{len(empire.megastructures) - limit})"
        if len(empire.megastructures) > limit
        else ""
    )
    return " | ".join(parts) + suffix


def _format_megastructures_en(empire: EmpireSummary, limit: int = 6) -> str:
    if not empire.megastructures:
        return "no player-owned megastructures found"
    return _format_megastructures(empire, limit=limit)


def _format_ship_designs(
    empire: EmpireSummary,
    detail_level: DetailLevel = DetailLevel.STANDARD,
    limit: int = 6,
) -> str:
    if not empire.ship_designs:
        if empire.ship_design_ids:
            return f"已发现 {len(empire.ship_design_ids)} 个设计 ID，尚未解析详情"
        return "尚未发现舰船设计"
    parts = []
    for design in empire.ship_designs[:limit]:
        mode = "auto" if design.auto_generated else "manual"
        components = ""
        if detail_level is DetailLevel.FULL and design.component_templates:
            components = (
                f"; components {', '.join(compact_name(component) for component in design.component_templates)}"
            )
        parts.append(
            f"{_format_name(design.name) or design.design_id} "
            f"({compact_name(design.ship_size) if design.ship_size else 'unknown'}, {mode}{components})"
        )
    suffix = f" (+{len(empire.ship_designs) - limit})" if len(empire.ship_designs) > limit else ""
    return " | ".join(parts) + suffix


def _format_full_detail_lines(empire: EmpireSummary) -> list[str]:
    return [
        f"领袖细节: {_format_leader_details(empire)}",
        f"恒星基地细节: {_format_starbase_details(empire)}",
        f"星球建筑/区划细节: {_format_planet_details(empire)}",
        f"舰船设计细节: {_format_ship_design_details(empire)}",
    ]


def _format_full_detail_lines_en(empire: EmpireSummary) -> list[str]:
    return [
        f"Leader details: {_format_leader_details(empire)}",
        f"Starbase details: {_format_starbase_details(empire)}",
        f"Planet building/district details: {_format_planet_details(empire)}",
        f"Ship design details: {_format_ship_design_details(empire)}",
    ]


def _format_leader_details(empire: EmpireSummary, limit: int = 20) -> str:
    if not empire.leaders:
        return "not parsed"
    parts = []
    for leader in empire.leaders[:limit]:
        traits = ", ".join(display_name(trait) for trait in leader.traits) if leader.traits else "none"
        location = leader.location_type or "unknown"
        if leader.location_id is not None:
            location += f" {leader.location_id}"
        parts.append(
            f"{_format_name(leader.name) or leader.leader_id}: {leader.leader_class or 'unknown'} "
            f"L{_format_number(leader.level)}, traits {traits}, location {location}"
        )
    suffix = f" (+{len(empire.leaders) - limit})" if len(empire.leaders) > limit else ""
    return " | ".join(parts) + suffix


def _format_starbase_details(empire: EmpireSummary, limit: int = 30) -> str:
    if not empire.starbases:
        return "not parsed"
    parts = []
    for starbase in empire.starbases[:limit]:
        system = _format_name(starbase.system_name) or str(starbase.system_id or "unknown")
        modules = ", ".join(compact_name(module) for module in starbase.modules) or "none"
        buildings = ", ".join(compact_name(building) for building in starbase.buildings) or "none"
        parts.append(
            f"{system}: {compact_name(starbase.level) if starbase.level else 'unknown'}, "
            f"modules {modules}, buildings {buildings}"
        )
    suffix = f" (+{len(empire.starbases) - limit})" if len(empire.starbases) > limit else ""
    return " | ".join(parts) + suffix


def _format_planet_details(empire: EmpireSummary, limit: int = 20) -> str:
    if not empire.planets:
        return "not parsed"
    parts = []
    for planet in empire.planets[:limit]:
        districts = ", ".join(str(item) for item in planet.districts) or "none"
        buildings = ", ".join(str(item) for item in planet.buildings) or "none"
        parts.append(
            f"{_format_name(planet.name) or planet.planet_id}: districts {districts}; "
            f"buildings {buildings}; designation {compact_name(planet.designation) if planet.designation else 'unknown'}"
        )
    suffix = f" (+{len(empire.planets) - limit})" if len(empire.planets) > limit else ""
    return " | ".join(parts) + suffix


def _format_ship_design_details(empire: EmpireSummary, limit: int = 20) -> str:
    if not empire.ship_designs:
        return "not parsed"
    parts = []
    for design in empire.ship_designs[:limit]:
        sections = ", ".join(compact_name(section) for section in design.section_templates) or "none"
        components = ", ".join(compact_name(component) for component in design.component_templates) or "none"
        required = ", ".join(compact_name(component) for component in design.required_components) or "none"
        parts.append(
            f"{_format_name(design.name) or design.design_id}: {compact_name(design.ship_size) if design.ship_size else 'unknown'}, "
            f"sections {sections}, components {components}, required {required}"
        )
    suffix = f" (+{len(empire.ship_designs) - limit})" if len(empire.ship_designs) > limit else ""
    return " | ".join(parts) + suffix


def _format_technologies(empire: EmpireSummary, limit: int = 10) -> str:
    if not empire.technologies:
        return "尚未解析"
    shown = [display_name(tech) for tech in list(empire.technologies.keys())[:limit]]
    suffix = f" (+{len(empire.technologies) - limit})" if len(empire.technologies) > limit else ""
    return f"{len(empire.technologies)} 项: " + ", ".join(shown) + suffix


def _format_technologies_en(empire: EmpireSummary, limit: int = 10) -> str:
    if not empire.technologies:
        return "not parsed yet"
    shown = [display_name(tech) for tech in list(empire.technologies.keys())[:limit]]
    suffix = f" (+{len(empire.technologies) - limit})" if len(empire.technologies) > limit else ""
    return f"{len(empire.technologies)} items: " + ", ".join(shown) + suffix


def _format_tradition_details(empire: EmpireSummary, limit: int = 6) -> str:
    if not empire.traditions:
        return "尚未选择传统"
    grouped: dict[str, list[str]] = {}
    for tradition in empire.traditions:
        tree = _tradition_tree_name(tradition)
        grouped.setdefault(tree, []).append(tradition)
    parts = []
    for tree, traditions in grouped.items():
        shown = ", ".join(display_name(tradition) for tradition in traditions[:limit])
        suffix = f" (+{len(traditions) - limit})" if len(traditions) > limit else ""
        parts.append(f"{tree}: {shown}{suffix}")
    return " | ".join(parts)


def _format_tradition_details_en(empire: EmpireSummary, limit: int = 6) -> str:
    if not empire.traditions:
        return "no traditions selected"
    return _format_tradition_details(empire, limit=limit)


def _tradition_tree_name(tradition: str) -> str:
    if not tradition.startswith("tr_"):
        return "unknown"
    remainder = tradition[3:]
    return remainder.split("_", 1)[0] if "_" in remainder else remainder


def _format_resources(resources: dict[str, float]) -> str:
    preferred = [
        "energy",
        "minerals",
        "food",
        "alloys",
        "unity",
        "physics_research",
        "society_research",
        "engineering_research",
        "influence",
    ]
    parts = []
    for key in preferred:
        if key in resources:
            parts.append(f"{key} {resources[key]:+.1f}")
    return " / ".join(parts) if parts else "未知"


def _build_empire_findings(empire: EmpireSummary) -> list[Finding]:
    findings: list[Finding] = []

    if empire.origin is None or not empire.civics or not empire.ethics:
        findings.append(
            Finding(
                title="帝国身份信息不完整",
                severity="low",
                detail="没有完整提取起源、国民理念或思潮。",
                recommendation="继续扩展玩家 country block 解析，并为不同版本/政体添加兼容测试。",
            )
        )

    if (
        empire.military_power is not None
        and empire.used_naval_capacity is not None
        and empire.military_power <= 0
        and empire.used_naval_capacity <= 0
    ):
        findings.append(
            Finding(
                title="常备舰队为零，需要结合外交判断",
                severity="medium",
                detail="存档显示当前军事实力和已用舰队容量都是 0。这可能是有意节省维护费的和平策略，不应脱离邻国关系、边境形状和星港防御直接判定为危机。",
                recommendation="后续应结合相邻帝国关系、宿敌/宣称、边境 chokepoint、星港火力和玩家战略目标判断风险；若邻国友好且无敌对接壤，无常备舰队可能是合理选择。",
            )
        )

    alloy_income = empire.monthly_income.get("alloys")
    if alloy_income is not None and alloy_income < 30:
        findings.append(
            Finding(
                title="合金月收入偏低",
                severity="medium",
                detail=f"当前合金月收入约为 {alloy_income:.1f}，对 2250 年后的扩张、防御和星际基地建设来说偏紧。",
                recommendation="优先检查是否有星球可转向合金/生物舰相关生产，并减少不必要的矿物转化压力；如果附近威胁较低，也至少维持一条持续造舰或补防线。",
            )
        )

    research_total = sum(
        empire.monthly_income.get(key, 0)
        for key in ["physics_research", "society_research", "engineering_research"]
    )
    if empire.empire_size and research_total and research_total / empire.empire_size < 1.5:
        findings.append(
            Finding(
                title="科研密度偏低",
                severity="medium",
                detail=f"三系科研月收入合计约 {research_total:.1f}，帝国规模约 {empire.empire_size:.1f}，科研/规模比偏低。",
                recommendation="在不破坏基础资源盈余的前提下，提高研究岗位、研究站和科研加成；蜂群局也要避免只扩张人口与地盘而科技跟不上。",
            )
        )

    return findings


def _build_empire_findings_en(empire: EmpireSummary) -> list[Finding]:
    findings: list[Finding] = []

    if empire.origin is None or not empire.civics or not empire.ethics:
        findings.append(
            Finding(
                title="Incomplete empire identity data",
                severity="low",
                detail="Origin, civics, or ethics were not fully extracted.",
                recommendation="Continue expanding player country block parsing and add version-specific compatibility tests.",
            )
        )

    if (
        empire.military_power is not None
        and empire.used_naval_capacity is not None
        and empire.military_power <= 0
        and empire.used_naval_capacity <= 0
    ):
        findings.append(
            Finding(
                title="No standing fleet; evaluate with diplomacy and borders",
                severity="medium",
                detail="The save reports both military power and used naval capacity as 0. This can be an intentional upkeep-saving peace strategy, so it should not be treated as a crisis without diplomacy, border shape, and starbase defenses.",
                recommendation="Evaluate neighboring empire relations, rivalries/claims, chokepoints, starbase firepower, and the player's strategic goal before recommending fleet construction.",
            )
        )

    alloy_income = empire.monthly_income.get("alloys")
    if alloy_income is not None and alloy_income < 30:
        findings.append(
            Finding(
                title="Low monthly alloy income",
                severity="medium",
                detail=f"Current alloy income is about {alloy_income:.1f}, which is tight for expansion, defense, and starbase construction.",
                recommendation="Check whether any planets can shift toward alloy or biological ship production while protecting basic resource balance.",
            )
        )

    research_total = sum(
        empire.monthly_income.get(key, 0)
        for key in ["physics_research", "society_research", "engineering_research"]
    )
    if empire.empire_size and research_total and research_total / empire.empire_size < 1.5:
        findings.append(
            Finding(
                title="Low research density",
                severity="medium",
                detail=f"Total monthly research is about {research_total:.1f} against empire size {empire.empire_size:.1f}.",
                recommendation="Increase researcher jobs, research stations, and research modifiers without breaking the basic economy.",
            )
        )

    return findings


def _build_planet_findings(empire: EmpireSummary) -> list[Finding]:
    findings: list[Finding] = []
    for planet in empire.planets:
        label = _format_name(planet.name) or str(planet.planet_id)
        if planet.stability is not None and planet.stability < 50:
            findings.append(
                Finding(
                    title=f"{label} 稳定度偏低",
                    severity="medium",
                    detail=f"该星球稳定度约为 {_format_number(planet.stability)}。",
                    recommendation="优先检查住房、舒适度、犯罪/偏差、岗位和派系/幸福度来源。",
                )
            )
        if planet.free_housing is not None and planet.free_housing < 0:
            findings.append(
                Finding(
                    title=f"{label} 住房不足",
                    severity="medium",
                    detail=f"该星球空余住房约为 {_format_number(planet.free_housing)}。",
                    recommendation="考虑建设住房区划/建筑、调整星球定位，或迁移/控制人口增长。",
                )
            )
        if planet.free_amenities is not None and planet.free_amenities < 0:
            findings.append(
                Finding(
                    title=f"{label} 舒适度不足",
                    severity="medium",
                    detail=f"该星球空余舒适度约为 {_format_number(planet.free_amenities)}。",
                    recommendation="补充维护/服务类岗位或相关建筑，避免稳定度继续下滑。",
                )
            )
    return findings


def _build_planet_findings_en(empire: EmpireSummary) -> list[Finding]:
    findings: list[Finding] = []
    for planet in empire.planets:
        label = _format_name(planet.name) or str(planet.planet_id)
        if planet.stability is not None and planet.stability < 50:
            findings.append(
                Finding(
                    title=f"{label} has low stability",
                    severity="medium",
                    detail=f"This planet's stability is about {_format_number(planet.stability)}.",
                    recommendation="Check housing, amenities, crime/deviancy, jobs, and faction or happiness sources.",
                )
            )
        if planet.free_housing is not None and planet.free_housing < 0:
            findings.append(
                Finding(
                    title=f"{label} lacks housing",
                    severity="medium",
                    detail=f"This planet has about {_format_number(planet.free_housing)} free housing.",
                    recommendation="Consider housing districts/buildings, designation changes, resettlement, or growth controls.",
                )
            )
        if planet.free_amenities is not None and planet.free_amenities < 0:
            findings.append(
                Finding(
                    title=f"{label} lacks amenities",
                    severity="medium",
                    detail=f"This planet has about {_format_number(planet.free_amenities)} free amenities.",
                    recommendation="Add maintenance/service jobs or related buildings before stability drops further.",
                )
            )
    return findings
