from __future__ import annotations


def compute_global_confidence(hiring_signal_brief: dict[str, object]) -> str:
    signals = hiring_signal_brief.get("signals", [])
    if not isinstance(signals, list) or not signals:
        return "low"

    confident_signals = [
        signal for signal in signals if isinstance(signal, dict) and float(signal.get("confidence", 0.0)) >= 0.6
    ]
    low_stub_signals = [
        signal
        for signal in signals
        if isinstance(signal, dict)
        and (
            "stub" in str(signal.get("value", "")).lower()
            or "stub" in " ".join(str(item) for item in signal.get("evidence", [])).lower()
        )
    ]
    overall_confidence = float(hiring_signal_brief.get("overall_confidence", 0.0))
    completeness = (len(confident_signals) - len(low_stub_signals)) / max(len(signals), 1)

    if overall_confidence >= 0.75 and completeness >= 0.5 and len(confident_signals) >= 2:
        return "high"
    if overall_confidence >= 0.45 and completeness >= 0.25:
        return "medium"
    return "low"
