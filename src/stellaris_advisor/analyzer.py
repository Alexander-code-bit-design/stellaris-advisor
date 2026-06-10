from __future__ import annotations

from .models import AdvisorReport, Finding, SaveGame


def build_report(save: SaveGame) -> AdvisorReport:
    meta = save.metadata
    summary = [
        f"存档名称: {meta.name or '未知'}",
        f"游戏版本: {meta.version or '未知'}",
        f"当前日期: {meta.date or '未知'}",
        f"玩家国家 ID: {meta.player_country if meta.player_country is not None else '未知'}",
        f"铁人模式: {_format_bool(meta.ironman)}",
    ]

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

    return AdvisorReport(summary=summary, findings=findings, next_steps=next_steps)


def render_markdown(report: AdvisorReport) -> str:
    lines = ["# Stellaris Advisor Report", "", "## 局势摘要"]
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

