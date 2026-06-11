from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass

from .analyzer import render_markdown
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


def build_advice_prompt(report: AdvisorReport, focus: str | None = None) -> AdvicePrompt:
    is_en = report.language is ReportLanguage.EN
    system = _english_system_prompt(report) if is_en else _chinese_system_prompt(report)
    user = _english_user_prompt(report, focus) if is_en else _chinese_user_prompt(report, focus)
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
你是一个谨慎、实战导向的 Stellaris（群星）游戏顾问。

你的任务是根据工具提供的存档摘要，判断玩家当前局势，并给出下一步建议。
你必须遵守以下规则：
- 只使用“存档摘要”中明确给出的事实；不要编造未解析到的数据。
- {visibility}
- 区分“事实”“推断”“建议”。如果缺少外交、边境、敌军或地图信息，必须说明建议置信度有限。
- 建议要可执行，按优先级排列，并尽量说明为什么。
- 对具体机制建议要考虑游戏版本；如果版本信息不足或知识可能过期，必须提示需要版本化 wiki/RAG 验证。
- 不要把完整 gamestate、隐藏 AI 帝国情报、未发现星系或剧透信息写入回答。
"""


def _english_system_prompt(report: AdvisorReport) -> str:
    visibility = _visibility_instruction(report.visibility_mode, zh=False)
    return f"""
You are a careful, practical Stellaris strategy advisor.

Your task is to read the save summary supplied by the tool, assess the player's situation, and recommend next actions.
Rules:
- Use only facts explicitly present in the save summary; do not invent unparsed data.
- {visibility}
- Separate facts, inferences, and recommendations. If diplomacy, borders, enemy fleets, or map data are missing, say that confidence is limited.
- Make advice actionable, prioritized, and explain why.
- Treat mechanic-specific advice as version-sensitive; if version knowledge may be stale, say that version-tagged wiki/RAG validation is needed.
- Do not include full gamestate content, hidden AI intelligence, undiscovered systems, or spoilers.
"""


def _chinese_user_prompt(report: AdvisorReport, focus: str | None) -> str:
    rendered_report = render_markdown(report)
    focus_line = focus or "请给出当前局势评估、主要风险、经济/科研/传统/舰队优先级，以及接下来 10 年的行动计划。"
    return f"""
下面是 Stellaris Advisor 从玩家存档中解析出的摘要。

玩家关注点：
{focus_line}

请用中文输出，格式为：
1. 当前局势一句话判断
2. 已知事实
3. 关键风险和机会
4. 下一步优先级
5. 未来 10 年行动计划
6. 需要进一步读取或检索验证的信息

存档摘要：
{rendered_report}
"""


def _english_user_prompt(report: AdvisorReport, focus: str | None) -> str:
    rendered_report = render_markdown(report)
    focus_line = focus or "Assess the current situation, major risks, economy/research/tradition/fleet priorities, and a 10-year action plan."
    return f"""
Below is a save summary parsed by Stellaris Advisor.

Player focus:
{focus_line}

Reply in English using this structure:
1. One-sentence situation judgment
2. Known facts
3. Key risks and opportunities
4. Next priorities
5. 10-year action plan
6. Information that needs more parsing or retrieval validation

Save summary:
{rendered_report}
"""


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
