from __future__ import annotations


def build_ai_maturity_assessment(company: dict[str, object]) -> dict[str, object]:
    ml_roles = int(company.get("ai_roles_open", 0))
    if ml_roles > 3:
        score = 2
    elif ml_roles > 0:
        score = 1
    else:
        score = 0

    confidence = 0.8 if ml_roles > 0 else 0.65
    justification = [
        f"{ml_roles} AI/ML roles are currently open.",
        f"{company.get('open_roles_current', 0)} total roles are currently open.",
    ]
    if company.get("ai_practices"):
        justification.append(
            "Observed AI practices: " + ", ".join(str(item) for item in company["ai_practices"])
        )

    return {
        "signal": "ai_maturity_score",
        "value": score,
        "confidence": confidence,
        "evidence": justification,
        "justification": justification,
    }


def score_ai_maturity(signals: list[dict[str, object]]) -> int:
    if not signals:
        return 0
    value = signals[0].get("value", 0)
    return int(value) if isinstance(value, int) else 0
