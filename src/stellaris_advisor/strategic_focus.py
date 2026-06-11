from __future__ import annotations

from enum import Enum


class StrategicFocus(Enum):
    BALANCED = "balanced"
    EXPLORE = "explore"
    DEVELOP = "develop"
    CONQUER = "conquer"


def focus_description(focus: StrategicFocus, *, zh: bool) -> str:
    if zh:
        return {
            StrategicFocus.BALANCED: "均衡：同时评估探索、发展与征服，不预设玩家必须走某一条路。",
            StrategicFocus.EXPLORE: "探索：优先评估科研船、异常现象、特殊项目、星图扩张、考古/遗珍和外部情报收益。",
            StrategicFocus.DEVELOP: "发展：优先评估经济、科研、殖民地建设、人口/物种、贸易、稳定内政和长期滚雪球。",
            StrategicFocus.CONQUER: "征服：优先评估宣称、舰队、星港、战争目标、附庸化、边境推进和军事窗口。",
        }[focus]
    return {
        StrategicFocus.BALANCED: "Balanced: evaluate exploration, development, and conquest without assuming the player must follow one path.",
        StrategicFocus.EXPLORE: "Explore: prioritize science ships, anomalies, special projects, map expansion, archaeology/relics, and external intelligence value.",
        StrategicFocus.DEVELOP: "Develop: prioritize economy, research, colonies, pops/species, trade, internal stability, and long-term snowballing.",
        StrategicFocus.CONQUER: "Conquer: prioritize claims, fleets, starbases, war goals, vassalization, border pressure, and military timing windows.",
    }[focus]
