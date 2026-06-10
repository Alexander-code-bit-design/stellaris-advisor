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
                f"殖民地数量: {len(empire.owned_planets)}",
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

    if "planet" not in save.gamestate:
        findings.append(
            Finding(
                title="星球数据尚未结构化",
                severity="low",
                detail="MVP 已读取 gamestate，但还没有展开星球块。",
                recommendation="下一步实现 planet block 解析，提取住房、就业、稳定度、区划和建筑队列。",
            )
        )

    next_steps = [
        "实现玩家国家定位：从 player country ID 找到对应 country block。",
        "提取月收入、资源库存、舰队容量、科研产出、传统和飞升槽。",
        "建立按版本标记的 wiki/patch/community 知识库。",
        "让 LLM 只基于结构化摘要和检索证据生成建议。",
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
