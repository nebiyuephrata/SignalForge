from __future__ import annotations


def build_ai_maturity_assessment(company: dict[str, object]) -> dict[str, object]:
    ml_roles = int(company.get("ai_roles_open", 0))
    leadership_changes = company.get("leadership_changes", [])
    has_named_ai_leadership = any(
        isinstance(change, dict)
        and any(keyword in str(change.get("role", "")).lower() for keyword in ("ai", "ml", "data"))
        for change in leadership_changes
    )
    has_ai_practices = bool(company.get("ai_practices"))

    if ml_roles > 3 and has_named_ai_leadership:
        score = 3
    elif ml_roles > 3 or (ml_roles > 0 and has_ai_practices):
        score = 2
    elif ml_roles > 0:
        score = 1
    else:
        score = 0

    confidence = 0.85 if score >= 2 else 0.8 if score == 1 else 0.65
    evidence = [
        f"{ml_roles} AI/ML roles are currently open.",
        f"{company.get('open_roles_current', 0)} total roles are currently open.",
    ]
    if has_ai_practices:
        evidence.append("Observed AI practices: " + ", ".join(str(item) for item in company["ai_practices"]))
    if has_named_ai_leadership:
        evidence.append("A named AI/data-adjacent leadership role appears in recent public leadership changes.")

    justifications = [
        {
            "signal": "ai_adjacent_open_roles",
            "status": f"{ml_roles} AI/ML roles are currently open out of {company.get('open_roles_current', 0)} total roles.",
            "weight": "high",
            "confidence": "high" if ml_roles > 0 else "medium",
            "source_url": f"https://{company.get('domain', 'example.com')}/careers",
        },
        {
            "signal": "named_ai_ml_leadership",
            "status": (
                "Public leadership-change data shows an AI/data-adjacent leadership appointment."
                if has_named_ai_leadership
                else "No named AI/ML leadership role was found in the public leadership-change record."
            ),
            "weight": "high",
            "confidence": "medium",
            "source_url": f"https://{company.get('domain', 'example.com')}/team",
        },
        {
            "signal": "strategic_communications",
            "status": (
                "Public AI practices indicate strategic AI execution themes."
                if has_ai_practices
                else "No public strategic AI practice signal was captured."
            ),
            "weight": "medium",
            "confidence": "medium",
            "source_url": f"https://{company.get('domain', 'example.com')}",
        },
    ]

    return {
        "signal": "ai_maturity_score",
        "value": score,
        "score": score,
        "confidence": confidence,
        "evidence": evidence,
        "justification": evidence,
        "justifications": justifications,
    }


def score_ai_maturity(signals: list[dict[str, object]]) -> int:
    if not signals:
        return 0
    value = signals[0].get("value", 0)
    return int(value) if isinstance(value, int) else 0
