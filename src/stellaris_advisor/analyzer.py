from __future__ import annotations

from collections.abc import Iterable

from .detail_level import DetailLevel
from .display_names import compact_name, display_name
from .models import AdvisorReport, DiplomaticRelationSummary, EmpireSummary, Finding, SaveGame
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
                f"外交/接触: {_format_diplomacy(empire)}",
                f"可见星图/航道: {_format_known_map(empire)}",
                f"可见敌对目标: {_format_visible_threats(empire)}",
                f"威胁/边境跳数: {_format_strategic_paths(empire)}",
                f"殖民地数量: {len(empire.planets) or len(empire.owned_planets)}",
                f"星球概览: {_format_planets(empire)}",
                f"恒星基地: {_format_starbase_count(empire)}",
                f"恒星基地概览: {_format_starbases(empire, detail_level)}",
                f"舰队实例: {_format_fleet_counts(empire)}",
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
            summary.insert(25, f"领袖概览: {_format_leaders(empire, detail_level)}")
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
        "细化舰队、外交、边境、可见敌对情报与 chokepoint 权重，用上下文判断无常备舰队是否是合理维护费策略。",
        "继续完善领袖详情和内阁席位，把特质、岗位、位置与内阁议程纳入建议上下文。",
        "扩展 player_visible 地图分析，识别关键 chokepoint、边境星港和威胁方向的防御价值。",
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
                f"Government/authority: {_format_id_value_en(empire.government_type)} / {_format_id_value_en(empire.authority)}",
                f"Origin: {_format_id_value_en(empire.origin)}",
                f"Ethics: {_format_id_list_en(empire.ethics)}",
                f"Civics: {_format_id_list_en(empire.civics)}",
                f"Tradition trees: {_format_id_list_en(empire.tradition_categories)}",
                f"Selected traditions: {len(empire.traditions)}",
                f"Tradition details: {_format_tradition_details_en(empire)}",
                f"Ascension perks: {_format_id_list_en(empire.ascension_perks)}",
                f"Current agenda: {_format_id_value_en(empire.council_agenda)} ({_format_number_en(empire.council_agenda_progress)})",
                f"Active edicts: {_format_id_list_en(empire.edicts)}",
                f"Policy flags: {_format_id_list_en(empire.policy_flags, limit=6)}",
                f"Leaders: {len(empire.leaders) or len(empire.owned_leaders)}",
                f"Faction status: {_format_faction_status_en(empire)}",
                f"Diplomacy/contacts: {_format_diplomacy_en(empire)}",
                f"Known map/hyperlanes: {_format_known_map_en(empire)}",
                f"Visible hostile targets: {_format_visible_threats_en(empire)}",
                f"Threat/border jump distances: {_format_strategic_paths_en(empire)}",
                f"Colonies: {len(empire.planets) or len(empire.owned_planets)}",
                f"Planet overview: {_format_planets_en(empire)}",
                f"Starbases: {_format_starbase_count_en(empire)}",
                f"Starbase overview: {_format_starbases_en(empire, detail_level)}",
                f"Fleet instances: {_format_fleet_counts_en(empire)}",
                f"Megastructures: {_format_megastructures_en(empire)}",
                f"Ship designs: {_format_ship_designs_en(empire, detail_level)}",
                f"Researched technologies: {_format_technologies_en(empire)}",
                f"Empire size: {_format_number_en(empire.empire_size)}",
                f"Sapient pops: {_format_number_en(empire.sapient_pops)}",
                f"Used naval capacity: {_format_number_en(empire.used_naval_capacity)}",
                f"Economy power: {_format_number_en(empire.economy_power)}",
                f"Military power: {_format_number_en(empire.military_power)}",
                f"Victory rank: {_format_number_en(empire.victory_rank)}",
            ]
        )
        if detail_level is not DetailLevel.SUMMARY:
            summary.insert(25, f"Leader overview: {_format_leaders_en(empire, detail_level)}")
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
        "Refine fleet, diplomacy, border, visible hostile intel, and chokepoint weights so a zero standing fleet can be judged in context.",
        "Expand player-visible map analysis for key chokepoints, border starbases, and likely threat directions.",
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


def _format_number_en(value: object) -> str:
    if value is None:
        return "unknown"
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


def _format_id_value_en(value: object) -> str:
    if value is None or value == "":
        return "unknown"
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


def _format_diplomacy(empire: EmpireSummary) -> str:
    relation_count = len(empire.diplomatic_relations)
    communications = sum(1 for relation in empire.diplomatic_relations if relation.communications)
    hostile = sum(1 for relation in empire.diplomatic_relations if relation.hostile)
    borders = sum(1 for relation in empire.diplomatic_relations if relation.borders)
    severe_hostile = sum(
        1
        for relation in empire.diplomatic_relations
        if relation.risk_hint == "severe hostile border contact"
    )
    deescalation_candidates = sum(
        1
        for relation in empire.diplomatic_relations
        if _is_deescalation_candidate(relation)
    )
    active_first_contacts = sum(
        1 for contact in empire.first_contacts if contact.status != "finished"
    )
    if relation_count == 0 and not empire.first_contacts:
        return "尚未解析"
    return (
        f"关系 {relation_count}，已通信 {communications}，敌对 {hostile}，"
        f"接壤 {borders}，严重敌对接壤 {severe_hostile}，"
        f"可评估外交降温 {deescalation_candidates}，进行中首次接触 {active_first_contacts}"
    )


def _format_diplomacy_en(empire: EmpireSummary) -> str:
    relation_count = len(empire.diplomatic_relations)
    communications = sum(1 for relation in empire.diplomatic_relations if relation.communications)
    hostile = sum(1 for relation in empire.diplomatic_relations if relation.hostile)
    borders = sum(1 for relation in empire.diplomatic_relations if relation.borders)
    severe_hostile = sum(
        1
        for relation in empire.diplomatic_relations
        if relation.risk_hint == "severe hostile border contact"
    )
    deescalation_candidates = sum(
        1
        for relation in empire.diplomatic_relations
        if _is_deescalation_candidate(relation)
    )
    active_first_contacts = sum(
        1 for contact in empire.first_contacts if contact.status != "finished"
    )
    if relation_count == 0 and not empire.first_contacts:
        return "not parsed"
    return (
        f"relations {relation_count}, communications {communications}, hostile {hostile}, "
        f"border contacts {borders}, severe hostile borders {severe_hostile}, "
        f"de-escalation candidates {deescalation_candidates}, active first contacts {active_first_contacts}"
    )


def _is_deescalation_candidate(relation: DiplomaticRelationSummary) -> bool:
    return bool(
        relation.communications
        and (
            relation.hostile
            or relation.borders
            or (relation.relation_current is not None and relation.relation_current < 0)
            or (relation.threat is not None and relation.threat > 0)
        )
    )


def _format_known_map(empire: EmpireSummary) -> str:
    if not empire.known_systems:
        return "尚未解析"
    known_ids = {system.system_id for system in empire.known_systems}
    starbase_systems = sum(1 for system in empire.known_systems if system.starbase_ids)
    first_contact_locations = {
        contact.location_id for contact in empire.first_contacts if contact.location_id is not None
    }
    frontier_links = _frontier_hyperlane_count(empire, known_ids)
    return (
        f"已知/相关星系 {len(empire.known_systems)}，有星港 {starbase_systems}，"
        f"首次接触位置 {len(first_contact_locations)}，外缘航道候选 {frontier_links}"
    )


def _format_known_map_en(empire: EmpireSummary) -> str:
    if not empire.known_systems:
        return "not parsed"
    known_ids = {system.system_id for system in empire.known_systems}
    starbase_systems = sum(1 for system in empire.known_systems if system.starbase_ids)
    first_contact_locations = {
        contact.location_id for contact in empire.first_contacts if contact.location_id is not None
    }
    frontier_links = _frontier_hyperlane_count(empire, known_ids)
    return (
        f"known/relevant systems {len(empire.known_systems)}, starbase systems {starbase_systems}, "
        f"first-contact locations {len(first_contact_locations)}, frontier link candidates {frontier_links}"
    )


def _format_visible_threats(empire: EmpireSummary) -> str:
    if not empire.visible_threats:
        return "尚未解析或未发现"
    highest_power = max(
        (threat.military_power for threat in empire.visible_threats if threat.military_power is not None),
        default=None,
    )
    types = _count_labels(threat.threat_type for threat in empire.visible_threats)
    mobility = _count_labels(threat.mobility for threat in empire.visible_threats)
    threat_paths = [
        path for path in empire.strategic_paths if path.source_kind == "visible_threat"
    ]
    nearest_colony = _min_known_distance(
        path.jumps_to_nearest_colony for path in threat_paths
    )
    return (
        f"目标 {len(empire.visible_threats)}，最高军力 {_format_number(highest_power)}，"
        f"最近殖民地 {_format_number(nearest_colony)} 跳，类型 {types}，移动性 {mobility}"
    )


def _format_visible_threats_en(empire: EmpireSummary) -> str:
    if not empire.visible_threats:
        return "not parsed or none found"
    highest_power = max(
        (threat.military_power for threat in empire.visible_threats if threat.military_power is not None),
        default=None,
    )
    types = _count_labels(threat.threat_type for threat in empire.visible_threats)
    mobility = _count_labels(threat.mobility for threat in empire.visible_threats)
    threat_paths = [
        path for path in empire.strategic_paths if path.source_kind == "visible_threat"
    ]
    nearest_colony = _min_known_distance(
        path.jumps_to_nearest_colony for path in threat_paths
    )
    return (
        f"targets {len(empire.visible_threats)}, highest power {_format_number_en(highest_power)}, "
        f"nearest colony {_format_number_en(nearest_colony)} jumps, types {types}, mobility {mobility}"
    )


def _count_labels(values: Iterable[object]) -> str:
    counts: dict[str, int] = {}
    for value in values:
        label = str(value) if value else "unknown"
        counts[label] = counts.get(label, 0) + 1
    return ", ".join(f"{label} {count}" for label, count in sorted(counts.items()))


def _frontier_hyperlane_count(empire: EmpireSummary, known_ids: set[int]) -> int:
    return sum(
        1
        for system in empire.known_systems
        for lane in system.hyperlanes
        if lane.to_system_id not in known_ids
    )


def _format_strategic_paths(empire: EmpireSummary) -> str:
    if not empire.strategic_paths:
        return "尚未解析"
    nearest_colony = _min_known_distance(
        path.jumps_to_nearest_colony for path in empire.strategic_paths
    )
    nearest_starbase = _min_known_distance(
        path.jumps_to_nearest_starbase for path in empire.strategic_paths
    )
    nearest_upgraded = _min_known_distance(
        path.jumps_to_nearest_upgraded_starbase for path in empire.strategic_paths
    )
    return (
        f"来源 {len(empire.strategic_paths)}，最近殖民地 {_format_number(nearest_colony)} 跳，"
        f"最近星港 {_format_number(nearest_starbase)} 跳，最近升级星港 {_format_number(nearest_upgraded)} 跳"
    )


def _format_strategic_paths_en(empire: EmpireSummary) -> str:
    if not empire.strategic_paths:
        return "not parsed"
    nearest_colony = _min_known_distance(
        path.jumps_to_nearest_colony for path in empire.strategic_paths
    )
    nearest_starbase = _min_known_distance(
        path.jumps_to_nearest_starbase for path in empire.strategic_paths
    )
    nearest_upgraded = _min_known_distance(
        path.jumps_to_nearest_upgraded_starbase for path in empire.strategic_paths
    )
    return (
        f"sources {len(empire.strategic_paths)}, nearest colony {_format_number_en(nearest_colony)} jumps, "
        f"nearest starbase {_format_number_en(nearest_starbase)} jumps, "
        f"nearest upgraded starbase {_format_number_en(nearest_upgraded)} jumps"
    )


def _min_known_distance(values: object) -> int | None:
    distances = [value for value in values if isinstance(value, int)]
    return min(distances) if distances else None


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


def _format_leaders_en(
    empire: EmpireSummary,
    detail_level: DetailLevel = DetailLevel.STANDARD,
    limit: int = 6,
) -> str:
    if not empire.leaders:
        return "not parsed"
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
            f"{_format_name(leader.name) or leader.leader_id} ({leader.leader_class or 'unknown'} L{_format_number_en(leader.level)}{location}{council}{traits})"
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


def _format_planets_en(empire: EmpireSummary, limit: int = 6) -> str:
    if not empire.planets:
        return "not parsed"
    parts = []
    for planet in empire.planets[:limit]:
        stats = [
            compact_name(planet.planet_class) if planet.planet_class else "unknown",
            f"size {_format_number_en(planet.planet_size)}",
            f"pops {_format_number_en(planet.num_sapient_pops)}",
            f"stab {_format_number_en(planet.stability)}",
            f"housing {_format_number_en(planet.free_housing)}",
            f"amen {_format_number_en(planet.free_amenities)}",
        ]
        if planet.designation:
            stats.append(compact_name(planet.designation))
        parts.append(f"{_format_name(planet.name) or planet.planet_id} ({', '.join(stats)})")
    suffix = f" (+{len(empire.planets) - limit})" if len(empire.planets) > limit else ""
    return " | ".join(parts) + suffix


def _format_starbase_count(empire: EmpireSummary) -> str:
    capacity_used = _starbase_capacity_used(empire)
    return (
        f"总数 {len(empire.starbases)}；"
        f"容量占用 {capacity_used} / {_format_number(empire.starbase_capacity)}"
    )


def _format_starbase_count_en(empire: EmpireSummary) -> str:
    capacity_used = _starbase_capacity_used(empire)
    return (
        f"total {len(empire.starbases)}; "
        f"capacity used {capacity_used} / {_format_number_en(empire.starbase_capacity)}"
    )


def _starbase_capacity_used(empire: EmpireSummary) -> int:
    return sum(1 for starbase in empire.starbases if _uses_starbase_capacity(starbase.level))


def _uses_starbase_capacity(level: str | None) -> bool:
    if level is None:
        return False
    normalized = level.strip('"')
    return normalized not in {"starbase_level_outpost", "outpost"}


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


def _format_starbases_en(
    empire: EmpireSummary,
    detail_level: DetailLevel = DetailLevel.STANDARD,
    limit: int = 6,
) -> str:
    if not empire.starbases:
        return "not parsed"
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
            f"{system} ({compact_name(starbase.level) if starbase.level else 'unknown'}, power {_format_number_en(starbase.military_power)}{modules}{buildings})"
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


def _format_ship_designs_en(
    empire: EmpireSummary,
    detail_level: DetailLevel = DetailLevel.STANDARD,
    limit: int = 6,
) -> str:
    if not empire.ship_designs:
        if empire.ship_design_ids:
            return f"found {len(empire.ship_design_ids)} design IDs, details not parsed"
        return "no ship designs found"
    return _format_ship_designs(empire, detail_level=detail_level, limit=limit)


def _format_full_detail_lines(empire: EmpireSummary) -> list[str]:
    return [
        f"领袖细节: {_format_leader_details(empire)}",
        f"外交/接触细节: {_format_diplomacy_details(empire)}",
        f"可见星图/航道细节: {_format_known_map_details(empire)}",
        f"可见敌对目标细节: {_format_visible_threat_details(empire)}",
        f"威胁/边境跳数细节: {_format_strategic_path_details(empire)}",
        f"舰队实例细节: {_format_fleet_details(empire)}",
        f"恒星基地细节: {_format_starbase_details(empire)}",
        f"星球建筑/区划细节: {_format_planet_details(empire)}",
        f"舰船设计细节: {_format_ship_design_details(empire)}",
    ]


def _format_full_detail_lines_en(empire: EmpireSummary) -> list[str]:
    return [
        f"Leader details: {_format_leader_details(empire)}",
        f"Diplomacy/contact details: {_format_diplomacy_details(empire)}",
        f"Known map/hyperlane details: {_format_known_map_details(empire)}",
        f"Visible hostile target details: {_format_visible_threat_details(empire)}",
        f"Threat/border jump details: {_format_strategic_path_details(empire)}",
        f"Fleet instance details: {_format_fleet_details(empire)}",
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


def _format_diplomacy_details(empire: EmpireSummary, limit: int = 20) -> str:
    parts: list[str] = []
    for relation in empire.diplomatic_relations[:limit]:
        flags = []
        if relation.contact:
            flags.append("contact")
        if relation.communications:
            flags.append("communications")
        if relation.hostile:
            flags.append("hostile")
        if relation.borders:
            flags.append("borders")
        modifier_text = ""
        if relation.modifiers:
            shown_modifiers = ", ".join(
                f"{compact_name(modifier.modifier)} {_format_number(modifier.value)}"
                for modifier in relation.modifiers[:3]
            )
            modifier_text = f", modifiers {shown_modifiers}"
        parts.append(
            f"country {relation.country_id} {_format_name(relation.name) or 'unknown'}: "
            f"{'/'.join(flags) or 'no flags'}, opinion {_format_number(relation.relation_current)}, "
            f"trust {_format_number(relation.trust)}, threat {_format_number(relation.threat)}, "
            f"border_range {_format_number(relation.border_range)}, "
            f"risk {relation.risk_hint or 'unknown'}, "
            f"de-escalation {relation.deescalation_hint or 'unknown'}{modifier_text}"
        )
    relation_suffix = (
        f" (+{len(empire.diplomatic_relations) - limit} relations)"
        if len(empire.diplomatic_relations) > limit
        else ""
    )
    contact_parts = []
    for contact in empire.first_contacts[:limit]:
        target = contact.country_id
        contact_parts.append(
            f"first_contact {contact.contact_id} {_format_name(contact.name) or 'unknown'}: "
            f"owner {contact.owner}, country {target}, status {contact.status or 'unknown'}, "
            f"stage {compact_name(contact.stage) if contact.stage else 'unknown'}, "
            f"clues {_format_number(contact.clues)}, difficulty {_format_number(contact.difficulty)}, "
            f"days_left {_format_number(contact.days_left)}, location {_format_number(contact.location_id)}"
        )
    contact_suffix = (
        f" (+{len(empire.first_contacts) - limit} first contacts)"
        if len(empire.first_contacts) > limit
        else ""
    )
    if not parts and not contact_parts:
        return "not parsed"
    relation_text = " | ".join(parts) + relation_suffix if parts else "relations not parsed"
    contact_text = " | ".join(contact_parts) + contact_suffix if contact_parts else "first contacts not parsed"
    return f"relations: {relation_text}; first contacts: {contact_text}"


def _format_known_map_details(empire: EmpireSummary, limit: int = 30) -> str:
    if not empire.known_systems:
        return "not parsed"
    known_ids = {system.system_id for system in empire.known_systems}
    parts = []
    for system in empire.known_systems[:limit]:
        lanes = ", ".join(
            f"{lane.to_system_id}{'*' if lane.to_system_id not in known_ids else ''}"
            for lane in system.hyperlanes
        ) or "none"
        flags = []
        if system.discovered:
            flags.append("discovered")
        if system.starbase_ids:
            flags.append(f"starbases {','.join(str(item) for item in system.starbase_ids)}")
        if system.colonies:
            flags.append(f"colonies {','.join(str(item) for item in system.colonies)}")
        if system.bypass_ids:
            flags.append(f"bypasses {','.join(str(item) for item in system.bypass_ids)}")
        parts.append(
            f"{system.system_id} {_format_name(system.name) or 'unknown'}: "
            f"{compact_name(system.star_class) if system.star_class else 'unknown'}, "
            f"{'; '.join(flags) or 'no flags'}, lanes {lanes}"
        )
    suffix = f" (+{len(empire.known_systems) - limit})" if len(empire.known_systems) > limit else ""
    return " | ".join(parts) + suffix


def _format_visible_threat_details(empire: EmpireSummary, limit: int = 30) -> str:
    if not empire.visible_threats:
        return "not parsed or none found"
    system_names = {system.system_id: system.name for system in empire.known_systems}
    parts = []
    for threat in empire.visible_threats[:limit]:
        system_label = (
            _format_system_label(threat.system_id, system_names.get(threat.system_id))
            if threat.system_id is not None
            else "unknown system"
        )
        parts.append(
            f"{threat.threat_id} {_format_name(threat.name) or 'unknown'}: "
            f"system {system_label}, owner {_format_number(threat.owner)}, "
            f"power {_format_number(threat.military_power)}, "
            f"type {threat.threat_type or 'unknown'}, mobility {threat.mobility or 'unknown'}, "
            f"risk {threat.risk_hint or 'unknown'}"
        )
    suffix = f" (+{len(empire.visible_threats) - limit})" if len(empire.visible_threats) > limit else ""
    return " | ".join(parts) + suffix


def _format_strategic_path_details(empire: EmpireSummary, limit: int = 20) -> str:
    if not empire.strategic_paths:
        return "not parsed"
    parts = []
    for path in empire.strategic_paths[:limit]:
        source = (
            f"{path.source_kind} {path.source_id} at "
            f"{_format_system_label(path.source_system_id, path.source_system_name)}"
        )
        if path.source_name:
            source = (
                f"{path.source_kind} {path.source_id} {_format_name(path.source_name) or path.source_name} "
                f"at {_format_system_label(path.source_system_id, path.source_system_name)}"
            )
        colony = _format_path_target(
            "colony",
            path.nearest_colony_system_id,
            path.nearest_colony_system_name,
            path.jumps_to_nearest_colony,
        )
        starbase = _format_path_target(
            "starbase",
            path.nearest_starbase_system_id,
            path.nearest_starbase_system_name,
            path.jumps_to_nearest_starbase,
        )
        upgraded = _format_path_target(
            "upgraded",
            path.nearest_upgraded_starbase_system_id,
            path.nearest_upgraded_starbase_system_name,
            path.jumps_to_nearest_upgraded_starbase,
        )
        shipyard = _format_path_target(
            "shipyard",
            path.nearest_shipyard_system_id,
            path.nearest_shipyard_system_name,
            path.jumps_to_nearest_shipyard,
        )
        parts.append(f"{source}: {colony}; {starbase}; {upgraded}; {shipyard}")
    suffix = f" (+{len(empire.strategic_paths) - limit})" if len(empire.strategic_paths) > limit else ""
    return " | ".join(parts) + suffix


def _format_path_target(
    label: str,
    system_id: int | None,
    system_name: str | None,
    jumps: int | None,
) -> str:
    if system_id is None or jumps is None:
        return f"{label} unknown"
    return f"{label} {_format_system_label(system_id, system_name)} {jumps} jumps"


def _format_system_label(system_id: int, system_name: str | None) -> str:
    name = _format_name(system_name)
    return f"{name or 'system'} ({system_id})"


def _format_fleet_counts(empire: EmpireSummary) -> str:
    if not empire.fleets:
        return "尚未解析"
    station_count = sum(1 for fleet in empire.fleets if fleet.station)
    mobile_count = len(empire.fleets) - station_count
    mobile_military_count = sum(
        1
        for fleet in empire.fleets
        if not fleet.station and (fleet.military_power or 0) > 0
    )
    home_base_count = sum(1 for fleet in empire.fleets if fleet.home_base_id is not None)
    stance_count = sum(1 for fleet in empire.fleets if fleet.stance is not None)
    reinforcing_count = sum(1 for fleet in empire.fleets if fleet.reinforcement)
    return (
        f"总计 {len(empire.fleets)}，机动 {mobile_count}，"
        f"机动战斗 {mobile_military_count}，空间站/基地 {station_count}，"
        f"母港已解析 {home_base_count}，姿态已解析 {stance_count}，补员中 {reinforcing_count}"
    )


def _format_fleet_counts_en(empire: EmpireSummary) -> str:
    if not empire.fleets:
        return "not parsed"
    station_count = sum(1 for fleet in empire.fleets if fleet.station)
    mobile_count = len(empire.fleets) - station_count
    mobile_military_count = sum(
        1
        for fleet in empire.fleets
        if not fleet.station and (fleet.military_power or 0) > 0
    )
    home_base_count = sum(1 for fleet in empire.fleets if fleet.home_base_id is not None)
    stance_count = sum(1 for fleet in empire.fleets if fleet.stance is not None)
    reinforcing_count = sum(1 for fleet in empire.fleets if fleet.reinforcement)
    return (
        f"total {len(empire.fleets)}, mobile {mobile_count}, "
        f"mobile military {mobile_military_count}, stations/bases {station_count}, "
        f"home bases parsed {home_base_count}, stances parsed {stance_count}, reinforcing {reinforcing_count}"
    )


def _format_fleet_details(empire: EmpireSummary, limit: int = 40) -> str:
    if not empire.fleets:
        return "not parsed"
    parts = []
    sorted_fleets = sorted(
        empire.fleets,
        key=lambda fleet: (
            1 if fleet.station else 0,
            -float(fleet.military_power or 0),
            fleet.fleet_id,
        ),
    )
    for fleet in sorted_fleets[:limit]:
        kind = "station/base" if fleet.station else "mobile"
        ships = ", ".join(
            (
                f"{ship.ship_id}:design {ship.design_id}, hp {_format_number(ship.hit_points)}, "
                f"armor {_format_number(ship.armor)}, shield {_format_number(ship.shield)}, "
                f"power {_format_number(ship.military_power)}, build {_format_number(ship.build_progress)}, "
                f"upgrade {_format_number(ship.upgrade_progress)}"
            )
            for ship in fleet.ships[:8]
        ) or "none"
        if len(fleet.ships) > 8:
            ships += f" (+{len(fleet.ships) - 8} ships)"
        system = f", system {fleet.system_id}" if fleet.system_id is not None else ""
        posture = (
            f", home {_format_number(fleet.home_base_id)}, stance {fleet.stance or 'unknown'}, "
            f"activity {fleet.fleet_activity or 'unknown'}, orbit {_format_number(fleet.orbit_target_id)}, "
            f"target_system {_format_number(fleet.target_system_id)}, target_fleet {_format_number(fleet.target_fleet_id)}, "
            f"speed {_format_number(fleet.speed)}, reinforcement {_format_bool(fleet.reinforcement)}, "
            f"upgrading {_format_bool(fleet.upgrading)}, build_queue {_format_number(fleet.build_queue_id)}, "
            f"reinforcement_queue {_format_number(fleet.reinforcement_queue_id)}"
        )
        parts.append(
            f"{fleet.fleet_id} {_format_name(fleet.name) or 'unnamed'}: "
            f"{compact_name(fleet.ship_class) if fleet.ship_class else 'unknown'}, "
            f"{kind}, power {_format_number(fleet.military_power)}{system}{posture}, ships {ships}"
        )
    suffix = f" (+{len(empire.fleets) - limit})" if len(empire.fleets) > limit else ""
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
        districts = ", ".join(
            f"{district.district_id}:{compact_name(district.district_type) if district.district_type else 'unknown'}"
            f" L{_format_number(district.level)}"
            for district in planet.district_details
        ) or ", ".join(str(item) for item in planet.districts) or "none"
        buildings = ", ".join(
            f"{building.building_id}:{compact_name(building.building_type) if building.building_type else 'unknown'}"
            f" pos {_format_number(building.position)}"
            for building in planet.building_details
        ) or ", ".join(str(item) for item in planet.buildings) or "none"
        queues = (
            f"; build queue {planet.build_queue_id}, army queue {planet.army_build_queue_id}"
            if planet.build_queue_id is not None or planet.army_build_queue_id is not None
            else ""
        )
        parts.append(
            f"{_format_name(planet.name) or planet.planet_id}: districts {districts}; "
            f"buildings {buildings}; designation {compact_name(planet.designation) if planet.designation else 'unknown'}"
            f"{queues}"
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
        hostile_border_contacts = sum(
            1 for relation in empire.diplomatic_relations if relation.hostile and relation.borders
        )
        active_first_contacts = sum(
            1 for contact in empire.first_contacts if contact.status != "finished"
        )
        if hostile_border_contacts:
            nearest_colony = _min_known_distance(
                path.jumps_to_nearest_colony for path in empire.strategic_paths
            )
            nearest_upgraded = _min_known_distance(
                path.jumps_to_nearest_upgraded_starbase for path in empire.strategic_paths
            )
            distance_note = ""
            if nearest_colony is not None or nearest_upgraded is not None:
                distance_note = (
                    f" 已解析可见航道显示，相关接触源距离最近殖民地 {_format_number(nearest_colony)} 跳，"
                    f"距离最近升级星港 {_format_number(nearest_upgraded)} 跳。"
                )
            highest_threat_power = max(
                (
                    threat.military_power
                    for threat in empire.visible_threats
                    if threat.military_power is not None
                ),
                default=None,
            )
            threat_note = ""
            if highest_threat_power is not None:
                threat_note = (
                    f" 玩家可见敌对目标最高军力约 {_format_number(highest_threat_power)}；"
                    f"类型分布 {_count_labels(threat.threat_type for threat in empire.visible_threats)}，"
                    f"移动性分布 {_count_labels(threat.mobility for threat in empire.visible_threats)}。"
                )
            detail = (
                f"存档显示当前军事实力和已用舰队容量都是 0；同时玩家可见外交关系中有 "
                f"{hostile_border_contacts} 个敌对且接壤的对象，另有 {active_first_contacts} 个进行中的首次接触。"
                f"{distance_note}{threat_note}"
            )
            recommendation = (
                "零舰队省维护费策略已经需要重新评估：优先结合该接壤方向的星港火力、超空间 chokepoint、"
                "敌对对象类型和可见舰队情报决定是否补充最低限度防御舰队。"
            )
            severity = "high"
        else:
            detail = (
                "存档显示当前军事实力和已用舰队容量都是 0。这可能是有意节省维护费的和平策略，"
                f"当前已解析到 {len(empire.diplomatic_relations)} 条外交关系和 {active_first_contacts} 个进行中的首次接触。"
            )
            recommendation = (
                "继续结合相邻帝国关系、宿敌/宣称、边境 chokepoint、星港火力和玩家战略目标判断风险；"
                "若邻国友好且无敌对接壤，无常备舰队可能是合理选择。"
            )
            severity = "medium"
        findings.append(
            Finding(
                title="常备舰队为零，需要结合外交判断",
                severity=severity,
                detail=detail,
                recommendation=recommendation,
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
        hostile_border_contacts = sum(
            1 for relation in empire.diplomatic_relations if relation.hostile and relation.borders
        )
        active_first_contacts = sum(
            1 for contact in empire.first_contacts if contact.status != "finished"
        )
        if hostile_border_contacts:
            nearest_colony = _min_known_distance(
                path.jumps_to_nearest_colony for path in empire.strategic_paths
            )
            nearest_upgraded = _min_known_distance(
                path.jumps_to_nearest_upgraded_starbase for path in empire.strategic_paths
            )
            distance_note = ""
            if nearest_colony is not None or nearest_upgraded is not None:
                distance_note = (
                    f" Parsed visible hyperlanes put the relevant contact source(s) "
                    f"{_format_number_en(nearest_colony)} jump(s) from the nearest colony and "
                    f"{_format_number_en(nearest_upgraded)} jump(s) from the nearest upgraded starbase."
                )
            highest_threat_power = max(
                (
                    threat.military_power
                    for threat in empire.visible_threats
                    if threat.military_power is not None
                ),
                default=None,
            )
            threat_note = ""
            if highest_threat_power is not None:
                threat_note = (
                    f" The highest visible hostile target power is about "
                    f"{_format_number_en(highest_threat_power)}; "
                    f"type distribution {_count_labels(threat.threat_type for threat in empire.visible_threats)}, "
                    f"mobility distribution {_count_labels(threat.mobility for threat in empire.visible_threats)}."
                )
            detail = (
                f"The save reports both military power and used naval capacity as 0; visible diplomacy also shows "
                f"{hostile_border_contacts} hostile border contact(s), with {active_first_contacts} active first contact(s)."
                f"{distance_note}{threat_note}"
            )
            recommendation = (
                "Re-evaluate the upkeep-saving zero-fleet strategy with starbase firepower, hyperlane chokepoints, "
                "hostile contact type, and visible fleet intelligence before deciding on a minimum defensive fleet."
            )
            severity = "high"
        else:
            detail = (
                "The save reports both military power and used naval capacity as 0. This can be an intentional "
                f"upkeep-saving peace strategy; {len(empire.diplomatic_relations)} diplomatic relation(s) and "
                f"{active_first_contacts} active first contact(s) were parsed."
            )
            recommendation = (
                "Evaluate neighboring relations, rivalries/claims, chokepoints, starbase firepower, and the player's "
                "strategic goal before recommending fleet construction."
            )
            severity = "medium"
        findings.append(
            Finding(
                title="No standing fleet; evaluate with diplomacy and borders",
                severity=severity,
                detail=detail,
                recommendation=recommendation,
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
