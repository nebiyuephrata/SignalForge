from __future__ import annotations

from statistics import mean

from agent.briefs.brief_schema import EvidenceSignal


def bounded(value: float) -> float:
    return max(0.0, min(1.0, value))


def average_confidence(signals: list[EvidenceSignal]) -> float:
    if not signals:
        return 0.0
    return bounded(mean(signal.confidence for signal in signals))


def confidence_phrase(confidence: float) -> str:
    if confidence >= 0.75:
        return "assertive"
    if confidence >= 0.4:
        return "hedged"
    return "question"
