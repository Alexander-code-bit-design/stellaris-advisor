from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass

from .knowledge import KnowledgeHit, render_knowledge_evidence
from .models import AdvisorReport
from .report_language import ReportLanguage
from .visibility import VisibilityMode


class AdviceError(RuntimeError):
    """Raised when an LLM advice request cannot be completed."""


@dataclass(slots=True)
class AdvicePrompt:
    system: str
    user: str

    def render(self) -> str:
        return (
            "## System\n"
            f"{self.system.strip()}\n\n"
            "## User\n"
            f"{self.user.strip()}\n"
        )


def build_advice_prompt(
    report: AdvisorReport,
    focus: str | None = None,
    knowledge_hits: list[KnowledgeHit] | None = None,
) -> AdvicePrompt:
    is_en = report.language is ReportLanguage.EN
    system = _english_system_prompt(report) if is_en else _chinese_system_prompt(report)
    user = (
        _english_user_prompt(report, focus, knowledge_hits or [])
        if is_en
        else _chinese_user_prompt(report, focus, knowledge_hits or [])
    )
    return AdvicePrompt(system=system, user=user)


def request_openai_compatible_advice(
    prompt: AdvicePrompt,
    *,
    model: str,
    api_key: str,
    base_url: str = "https://api.openai.com/v1",
    timeout_seconds: int = 60,
) -> str:
    if not model:
        raise AdviceError("An advice model is required.")
    if not api_key:
        raise AdviceError("An API key is required.")

    endpoint = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": prompt.system},
            {"role": "user", "content": prompt.user},
        ],
        "temperature": 0.2,
    }
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise AdviceError(f"LLM request failed with HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise AdviceError(f"LLM request failed: {exc.reason}") from exc

    try:
        body = json.loads(raw)
        return body["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise AdviceError(f"LLM response had an unexpected shape: {raw[:500]}") from exc


def api_key_from_env(env_name: str) -> str:
    return os.environ.get(env_name, "")


def _chinese_system_prompt(report: AdvisorReport) -> str:
    visibility = _visibility_instruction(report.visibility_mode, zh=True)
    return f"""
你是一个谨慎、实战导向、熟悉 Stellaris（群星）机制和中文标准译名的游戏顾问。

你的任务是根据工具提供的存档事实摘要，判断玩家当前局势，并给出下一步建议。
你必须遵守以下规则：
- 只使用“存档事实摘要”中明确给出的事实；不要编造未解析到的数据。
- {visibility}
- 区分“事实”“推断”“建议”。如果缺少外交、边境、敌军或地图信息，必须说明建议置信度有限。
- 不要把“军事实力为 0”自动判定为极端危机；必须结合邻国态度、接壤关系、战争风险、野怪位置、星港火力和玩家有意节省维护费的策略来判断。
- 不要把所有 hostile 目标都当成会主动进攻的敌国舰队；必须区分空间生物、静态空间站/采矿站、民用船、真正军用舰队，并考虑移动性和外交降温手段。
- 在建议建造军用舰船之前，必须先判断是否存在可见的外交降温路径，例如改善关系、派遣使节、有利贸易、调整外交姿态或等待首次接触完成。
- 恒星基地容量只统计升级后的恒星基地；普通前哨站不占恒星基地容量。报告会分开给出恒星基地总数和容量占用，只能根据“容量占用/上限”判断是否超限。
- 建议要可执行，按优先级排列，并尽量说明为什么。避免只给“补经济/补舰队/补科研”的泛泛建议。
- 对具体机制建议要考虑游戏版本；如果版本信息不足或知识可能过期，必须提示需要版本化 wiki/RAG 验证。
- 如果提供了“检索到的知识证据”，机制建议必须优先引用这些证据；不要把低置信度社区意见当成机制事实。
- 优先使用群星中文标准译名；不确定译名时保留英文 key 或说“译名待验证”，不要自造译名。例如 ascension_perk eternal_vigilance 的中文标准译名是“戒心永存”，不是“永恒警戒”。
- 回答风格应接近群星帝国顾问/内阁简报：有一点游戏内文本气质，但不要编造剧情、角色或隐藏情报。
- 不要把完整 gamestate、隐藏 AI 帝国情报、未发现星系或剧透信息写入回答。
"""


def _english_system_prompt(report: AdvisorReport) -> str:
    visibility = _visibility_instruction(report.visibility_mode, zh=False)
    return f"""
You are a careful, practical Stellaris strategy advisor with strong knowledge of Stellaris mechanics and terminology.

Your task is to read the factual save summary supplied by the tool, assess the player's situation, and recommend next actions.
Rules:
- Use only facts explicitly present in the factual save summary; do not invent unparsed data.
- {visibility}
- Separate facts, inferences, and recommendations. If diplomacy, borders, enemy fleets, or map data are missing, say that confidence is limited.
- Do not automatically treat 0 fleet power as an extreme crisis. Judge it with diplomacy, border contact, war risk, hostile space fauna, starbase firepower, and the player's deliberate upkeep-saving strategy.
- Do not treat every hostile target as an actively invading empire fleet. Distinguish space fauna, static stations/mining stations, civilian ships, and real military fleets, then consider mobility and diplomatic de-escalation options.
- Before recommending military ship construction, evaluate visible diplomatic de-escalation paths such as improving relations, envoy assignment, favorable trade, diplomatic stance changes, or waiting for first contact completion.
- Starbase capacity counts upgraded starbases, not ordinary outposts. The report separates total owned starbase objects from capacity usage; judge over-capacity only from "capacity used / cap".
- Make advice actionable, prioritized, and explain why. Avoid generic "improve economy/research/fleet" advice.
- Treat mechanic-specific advice as version-sensitive; if version knowledge may be stale, say that version-tagged wiki/RAG validation is needed.
- If retrieved knowledge evidence is provided, use it before relying on general memory; do not treat low-confidence community opinions as mechanical facts.
- Use standard Stellaris terms. If a localized term is uncertain, keep the raw English key or mark it as needing localization validation.
- Write like a Stellaris imperial council briefing: atmospheric but factual; do not invent lore, characters, hidden intelligence, or spoilers.
- Do not include full gamestate content, hidden AI intelligence, undiscovered systems, or spoilers.
"""


def _chinese_user_prompt(
    report: AdvisorReport, focus: str | None, knowledge_hits: list[KnowledgeHit]
) -> str:
    rendered_report = _render_fact_summary(report)
    rendered_knowledge = render_knowledge_evidence(knowledge_hits, language="zh")
    focus_line = focus or "请给出当前局势评估、主要风险、经济/科研/传统/舰队优先级，以及接下来 10 年的行动计划。"
    knowledge_section = (
        f"\n\n{rendered_knowledge}\n"
        if rendered_knowledge
        else "\n\n## 检索到的知识证据\n\n- 未提供；涉及机制强度、版本变化或标准译名时请标注需要版本化 wiki/RAG 验证。\n"
    )
    return f"""
下面是 Stellaris Advisor 从玩家存档中解析出的事实摘要。

玩家关注点：
{focus_line}

请用中文输出，格式为：
1. 帝国顾问简报：一句话判断，用群星风格但保持事实边界
2. 已知事实：只列存档摘要明确支持的信息
3. 不确定情报：列出外交、边境、野怪、地图、敌军、殖民地建筑/岗位等缺口，并说明这些缺口如何影响判断
4. 风险与机会：每条标注“事实支持 / 推断 / 待验证”
5. 下一步优先级：按“立即 / 1-3 年 / 3-10 年”排序
6. 具体操作建议：
   - 法令：是否开启、关闭或保留哪些法令；若存档未提供可选法令，就说明需要读取
   - 传统与飞升：下一棵传统、下一个传统节点、飞升天赋候选；不确定译名时保留 key
   - 星球：每个已知殖民地的建筑、区划、岗位或星球决议建议；如果细节不足，明确说需要 full/detail 或更深解析
   - 舰队与舰船设计：是否建舰、建多少、设计思路、武器/防御/作战电脑取舍；如果敌情未知，不要给过度确定的数量
   - 领袖与内阁：领袖岗位、总督/科学家/指挥官安排、内阁议程建议；缺数据则说明
   - 恒星基地：升级、模块、建筑、船坞、防御平台建议；不得把普通前哨站当成占容量的恒星基地
7. 未来 10 年行动计划：按年份或阶段列具体动作
8. 需要版本化 wiki/RAG 验证的机制与译名

存档事实摘要：
{rendered_report}
{knowledge_section}
"""


def _english_user_prompt(
    report: AdvisorReport, focus: str | None, knowledge_hits: list[KnowledgeHit]
) -> str:
    rendered_report = _render_fact_summary(report)
    rendered_knowledge = render_knowledge_evidence(knowledge_hits, language="en")
    focus_line = focus or "Assess the current situation, major risks, economy/research/tradition/fleet priorities, and a 10-year action plan."
    knowledge_section = (
        f"\n\n{rendered_knowledge}\n"
        if rendered_knowledge
        else "\n\n## Retrieved Knowledge Evidence\n\n- None provided; mark mechanics, version changes, and localization as needing version-tagged wiki/RAG validation when relevant.\n"
    )
    return f"""
Below is a factual save summary parsed by Stellaris Advisor.

Player focus:
{focus_line}

Reply in English using this structure:
1. Imperial council brief: one-sentence judgment, atmospheric but fact-bounded
2. Known facts: only facts directly supported by the save summary
3. Intelligence gaps: diplomacy, borders, hostile fauna, map shape, enemy fleets, colony buildings/jobs, and how those gaps affect confidence
4. Risks and opportunities: tag each item as fact-supported, inference, or needs validation
5. Next priorities: immediate, 1-3 years, and 3-10 years
6. Concrete actions:
   - Edicts: keep, enable, or disable; say when available choices were not parsed
   - Traditions and ascension perks: next tree/node/perk candidates; keep raw keys when uncertain
   - Planets: per-colony buildings, districts, jobs, or decisions; say when deeper parsing is needed
   - Fleets and ship designs: whether to build, how many, and design logic without overconfident numbers when enemy intel is missing
   - Leaders and council: assignments, governors/scientists/commanders, and agenda suggestions when data allows
   - Starbases: upgrades, modules, buildings, shipyards, and defense platforms; never count ordinary outposts against starbase capacity
7. 10-year action plan
8. Version-tagged wiki/RAG checks needed for mechanics and localization

Factual save summary:
{rendered_report}
{knowledge_section}
"""


def _render_fact_summary(report: AdvisorReport) -> str:
    is_en = report.language is ReportLanguage.EN
    lines = [
        "# Stellaris Advisor Fact Summary",
        "",
        f"{'Visibility mode' if is_en else '可见性模式'}: `{report.visibility_mode.value}`",
        "",
        f"## {'Parsed Save Facts' if is_en else '已解析存档事实'}",
    ]
    if report.visibility_mode is VisibilityMode.PLAYER_VISIBLE:
        lines.extend(
            [
                "",
                "> This fact summary is generated from player-visible information only; hidden AI intelligence, undiscovered systems, and spoiler data must not be inferred."
                if is_en
                else "> 本事实摘要仅基于玩家可见信息；不得推断隐藏 AI 情报、未发现星系或剧透信息。",
            ]
        )
    elif report.visibility_mode is VisibilityMode.OMNISCIENT:
        lines.extend(
            [
                "",
                "> Warning: omniscient/spoiler mode may include information not normally visible during play."
                if is_en
                else "> 警告：当前为全知/剧透模式，可能包含正常游玩不可见的信息。",
            ]
        )
    lines.extend(f"- {item}" for item in report.summary)
    return "\n".join(lines).strip() + "\n"


def _visibility_instruction(mode: VisibilityMode, *, zh: bool) -> str:
    if mode is VisibilityMode.PLAYER_VISIBLE:
        return (
            "当前是 player_visible 模式：不得主动泄露玩家正常游玩不可见的信息。"
            if zh
            else "Current mode is player_visible: do not reveal information unavailable to the player in normal play."
        )
    if mode is VisibilityMode.OMNISCIENT:
        return (
            "当前是 omniscient 模式：可以用于调试，但必须明确标注剧透风险。"
            if zh
            else "Current mode is omniscient: this may be used for debugging, but spoiler risk must be clearly labeled."
        )
    return (
        "当前是 debug 模式：输出应帮助开发者验证解析结果，并标注可见性风险。"
        if zh
        else "Current mode is debug: output should help validate parsing and label visibility risks."
    )
