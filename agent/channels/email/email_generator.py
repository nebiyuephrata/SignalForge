from __future__ import annotations


def generate_grounded_email(
    company: dict[str, object],
    hiring_signal_brief: dict[str, object],
    competitor_gap_brief: dict[str, object],
) -> dict[str, object]:
    overall_confidence = float(hiring_signal_brief["overall_confidence"])
    signals = hiring_signal_brief.get("signals", [])
    if not isinstance(signals, list) or len(signals) < 2:
        body = (
            f"I'm not confident enough to make a hard claim about {company['company_name']} from the available data. "
            "Is hiring capacity, compliance workload, or AI operations a live priority right now?"
        )
        return {
            "channel": "email",
            "subject": f"{company['company_name']}: quick signal check",
            "body": body,
            "word_count": len(body.split()),
            "grounding": {
                "signal_confidence": overall_confidence,
                "why_now": hiring_signal_brief.get("summary", "Signals are incomplete."),
            },
        }

    funding = signals[0]["value"]
    velocity = signals[1]["value"]
    if overall_confidence < 0.5:
        body = (
            f"I'm not confident enough to make a hard claim about {company['company_name']} from the local data alone. "
            "Is hiring capacity, compliance workload, or AI operations a live priority right now?"
        )
    else:
        opener = (
            f"It looks like {company['company_name']} has moved from "
            f"{velocity['open_roles_60_days_ago']} to {velocity['open_roles_current']} open roles in the last 60 days"
            if overall_confidence < 0.75
            else f"{company['company_name']} moved from {velocity['open_roles_60_days_ago']} to {velocity['open_roles_current']} open roles in 60 days"
        )

        body = (
            f"{opener}, following a {funding['round']} on {funding['date']}. "
            f"In a small peer set, similar fintech teams average AI maturity {competitor_gap_brief['peer_average_ai_maturity']}, "
            f"while {company['company_name']} currently scores {competitor_gap_brief['target_ai_maturity']}. "
            "If hiring capacity or AI operations is a live priority, I can share the benchmark and see whether a short discussion is useful."
        )

    return {
        "channel": "email",
        "subject": f"{company['company_name']}: hiring signal and peer benchmark",
        "body": body,
        "word_count": len(body.split()),
        "grounding": {
            "signal_confidence": overall_confidence,
            "why_now": hiring_signal_brief["summary"],
        },
    }
