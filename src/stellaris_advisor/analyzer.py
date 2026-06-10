from __future__ import annotations

from .models import AdvisorReport, EmpireSummary, Finding, SaveGame
from .visibility import VisibilityMode


def build_report(
    save: SaveGame, visibility_mode: VisibilityMode = VisibilityMode.PLAYER_VISIBLE
) -> AdvisorReport:
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
                f"政体/权力: {_format_value(empire.government_type)} / {_format_value(empire.authority)}",
                f"起源: {_format_value(empire.origin)}",
                f"思潮: {_format_list(empire.ethics)}",
                f"国民理念: {_format_list(empire.civics)}",
                f"传统组: {_format_list(empire.tradition_categories)}",
                f"已选传统数: {len(empire.traditions)}",
                f"传统明细: {_format_tradition_details(empire)}",
                f"飞升: {_format_list(empire.ascension_perks)}",
                f"当前议程: {_format_value(empire.council_agenda)} ({_format_number(empire.council_agenda_progress)})",
                f"启用法令: {_format_list(empire.edicts)}",
                f"政策标记: {_format_list(empire.policy_flags, limit=6)}",
                f"领袖数量: {len(empire.leaders) or len(empire.owned_leaders)}",
                f"领袖概览: {_format_leaders(empire)}",
                f"派系状态: {_format_faction_status(empire)}",
                f"殖民地数量: {len(empire.planets) or len(empire.owned_planets)}",
                f"星球概览: {_format_planets(empire)}",
                f"恒星基地: {len(empire.starbases)} / {_format_number(empire.starbase_capacity)}",
                f"恒星基地概览: {_format_starbases(empire)}",
                f"巨型结构: {_format_megastructures(empire)}",
                f"舰船设计: {_format_ship_designs(empire)}",
                f"已研究科技: {_format_technologies(empire)}",
                f"帝国规模: {_format_number(empire.empire_size)}",
                f"智慧人口: {_format_number(empire.sapient_pops)}",
                f"舰队容量使用: {_format_number(empire.used_naval_capacity)}",
                f"经济实力: {_format_number(empire.economy_power)}",
                f"军事实力: {_format_number(empire.military_power)}",
                f"胜利排名: {_format_number(empire.victory_rank)}",
            ]
        )
        if empire.monthly_income:
            summary.append(f"月收入概览: {_format_resources(empire.monthly_income)}")

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
        "解析恒星基地、舰队、舰船设计和补员队列，确认军事实力为零是否为真实局势或生物舰船字段差异。",
        "解析领袖详情和内阁席位，把 owned_leaders ID 映射到姓名、等级、岗位和特质。",
        "解析 galactic_object 和超空间航道，并在 player_visible 模式下做边境与 chokepoint 分析。",
        "建立按版本标记的 wiki/patch/community 知识库，让 LLM 基于结构化摘要和检索证据生成建议。",
    ]

    return AdvisorReport(
        visibility_mode=visibility_mode,
        summary=summary,
        findings=findings,
        next_steps=next_steps,
    )


def render_markdown(report: AdvisorReport) -> str:
    lines = [
        "# Stellaris Advisor Report",
        "",
        f"可见性模式: `{report.visibility_mode.value}`",
        "",
        "## 局势摘要",
    ]
    if report.visibility_mode is VisibilityMode.PLAYER_VISIBLE:
        lines.extend(
            [
                "",
                "> 默认仅基于玩家可见信息生成建议；隐藏 AI 情报、未发现星系和剧透信息不得进入报告。",
            ]
        )
    elif report.visibility_mode is VisibilityMode.OMNISCIENT:
        lines.extend(
            [
                "",
                "> 警告：当前为全知/剧透模式，后续版本可能显示正常游玩不可见的信息。",
            ]
        )
    lines.extend(f"- {item}" for item in report.summary)
    lines.extend(["", "## 发现的问题"])
    if report.findings:
        for finding in report.findings:
            lines.extend(
                [
                    f"### [{finding.severity}] {finding.title}",
                    finding.detail,
                    "",
                    f"建议: {finding.recommendation}",
                    "",
                ]
            )
    else:
        lines.append("- 暂未发现明显问题。")
    lines.extend(["", "## 下一步开发"])
    lines.extend(f"- {step}" for step in report.next_steps)
    return "\n".join(lines).strip() + "\n"


def _format_bool(value: bool | None) -> str:
    if value is None:
        return "未知"
    return "是" if value else "否"


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


def _format_list(values: list[object], limit: int = 8) -> str:
    if not values:
        return "未知"
    shown = [str(value) for value in values[:limit]]
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


def _format_leaders(empire: EmpireSummary, limit: int = 6) -> str:
    if not empire.leaders:
        return "尚未解析详情"
    parts = []
    for leader in empire.leaders[:limit]:
        traits = f"; {', '.join(leader.traits[:2])}" if leader.traits else ""
        location = ""
        if leader.location_type:
            location = f"; {leader.location_type}"
            if leader.location_id is not None:
                location += f" {leader.location_id}"
        council = ""
        if leader.council_position_id is not None:
            council = f"; council {leader.council_position_id}"
        parts.append(
            f"{leader.name or leader.leader_id} ({leader.leader_class or 'unknown'} L{_format_number(leader.level)}{location}{council}{traits})"
        )
    suffix = f" (+{len(empire.leaders) - limit})" if len(empire.leaders) > limit else ""
    return " | ".join(parts) + suffix


def _format_planets(empire: EmpireSummary, limit: int = 6) -> str:
    if not empire.planets:
        return "尚未解析详情"
    parts = []
    for planet in empire.planets[:limit]:
        stats = [
            planet.planet_class or "unknown",
            f"size {_format_number(planet.planet_size)}",
            f"pops {_format_number(planet.num_sapient_pops)}",
            f"stab {_format_number(planet.stability)}",
            f"housing {_format_number(planet.free_housing)}",
            f"amen {_format_number(planet.free_amenities)}",
        ]
        if planet.designation:
            stats.append(planet.designation)
        parts.append(f"{planet.name or planet.planet_id} ({', '.join(stats)})")
    suffix = f" (+{len(empire.planets) - limit})" if len(empire.planets) > limit else ""
    return " | ".join(parts) + suffix


def _format_starbases(empire: EmpireSummary, limit: int = 6) -> str:
    if not empire.starbases:
        return "尚未解析详情"
    parts = []
    for starbase in empire.starbases[:limit]:
        system = starbase.system_name or (
            f"system {starbase.system_id}" if starbase.system_id is not None else "unknown system"
        )
        modules = f"; modules {', '.join(starbase.modules[:3])}" if starbase.modules else ""
        buildings = f"; buildings {', '.join(starbase.buildings[:2])}" if starbase.buildings else ""
        parts.append(
            f"{system} ({starbase.level or 'unknown'}, power {_format_number(starbase.military_power)}{modules}{buildings})"
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
            f"{megastructure.name or megastructure.megastructure_id} "
            f"({_format_value(megastructure.megastructure_type)}{location})"
        )
    suffix = (
        f" (+{len(empire.megastructures) - limit})"
        if len(empire.megastructures) > limit
        else ""
    )
    return " | ".join(parts) + suffix


def _format_ship_designs(empire: EmpireSummary, limit: int = 6) -> str:
    if not empire.ship_designs:
        if empire.ship_design_ids:
            return f"已发现 {len(empire.ship_design_ids)} 个设计 ID，尚未解析详情"
        return "尚未发现舰船设计"
    parts = []
    for design in empire.ship_designs[:limit]:
        mode = "auto" if design.auto_generated else "manual"
        components = (
            f"; components {', '.join(design.component_templates[:3])}"
            if design.component_templates
            else ""
        )
        parts.append(
            f"{design.name or design.design_id} "
            f"({_format_value(design.ship_size)}, {mode}{components})"
        )
    suffix = f" (+{len(empire.ship_designs) - limit})" if len(empire.ship_designs) > limit else ""
    return " | ".join(parts) + suffix


def _format_technologies(empire: EmpireSummary, limit: int = 10) -> str:
    if not empire.technologies:
        return "尚未解析"
    shown = list(empire.technologies.keys())[:limit]
    suffix = f" (+{len(empire.technologies) - limit})" if len(empire.technologies) > limit else ""
    return f"{len(empire.technologies)} 项: " + ", ".join(shown) + suffix


def _format_tradition_details(empire: EmpireSummary, limit: int = 6) -> str:
    if not empire.traditions:
        return "尚未选择传统"
    grouped: dict[str, list[str]] = {}
    for tradition in empire.traditions:
        tree = _tradition_tree_name(tradition)
        grouped.setdefault(tree, []).append(tradition)
    parts = []
    for tree, traditions in grouped.items():
        shown = ", ".join(traditions[:limit])
        suffix = f" (+{len(traditions) - limit})" if len(traditions) > limit else ""
        parts.append(f"{tree}: {shown}{suffix}")
    return " | ".join(parts)


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
                title="军事实力为零",
                severity="high",
                detail="存档显示当前军事实力和已用舰队容量都是 0。",
                recommendation="尽快确认是否拆掉了舰队或存档字段未覆盖生物舰船；如果游戏内确实无舰队，应优先恢复基础防卫舰队，避免被邻国、掠夺者或危机事件抓空窗。",
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


def _build_planet_findings(empire: EmpireSummary) -> list[Finding]:
    findings: list[Finding] = []
    for planet in empire.planets:
        label = planet.name or str(planet.planet_id)
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
