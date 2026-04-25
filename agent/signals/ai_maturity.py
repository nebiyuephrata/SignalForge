from __future__ import annotations

from statistics import mean

from agent.core.models import AIMaturityAssessment, WeightedJustification


WEIGHTS = {
    "ai_adjacent_open_roles": 3,
    "named_ai_ml_leadership": 3,
    "github_org_activity": 2,
    "executive_commentary": 2,
    "modern_data_ml_stack": 1,
    "strategic_communications": 1,
}

MAX_POINTS = sum(WEIGHTS.values())


def build_ai_maturity_assessment(
    company: dict[str, object] | None,
    *,
    role_titles: list[str] | None = None,
) -> AIMaturityAssessment:
    if not company:
        justifications = _empty_justifications()
        return AIMaturityAssessment(
            score=0,
            confidence=0.35,
            weighted_points=0,
            max_points=MAX_POINTS,
            justifications=justifications,
            explanation="No Crunchbase company record was available, so the system defaults to AI maturity score 0.",
        )

    ai_roles_open = int(company.get("ai_roles_open", 0) or 0)
    leadership_changes = company.get("leadership_changes", [])
    practices = [str(item) for item in company.get("ai_practices", []) if str(item).strip()]
    normalized_roles = " ".join(role_titles or []).lower()

    has_ai_leadership = any(
        isinstance(change, dict)
        and any(keyword in str(change.get("role", "")).lower() for keyword in ("ai", "ml", "data"))
        for change in leadership_changes
    )
    github_activity_detected = False
    executive_commentary_detected = bool(practices)
    stack_detected = any(keyword in normalized_roles for keyword in ("ml", "machine learning", "data", "platform"))
    strategic_messaging_detected = any(
        keyword in " ".join(practices).lower()
        for keyword in ("governance", "copilot", "automation", "evaluation", "monitoring", "ai")
    )

    justifications = [
        WeightedJustification(
            signal="ai_adjacent_open_roles",
            status=(
                f"{ai_roles_open} AI-adjacent roles are open."
                if ai_roles_open
                else "No AI-adjacent roles are open in the structured record."
            ),
            weight="high",
            confidence="high" if ai_roles_open >= 2 else "medium" if ai_roles_open == 1 else "low",
            source_url=f"https://{company.get('domain', 'example.com')}/careers",
        ),
        WeightedJustification(
            signal="named_ai_ml_leadership",
            status=(
                "A named AI/data leadership signal is present."
                if has_ai_leadership
                else "No named AI/ML leadership appointment is present."
            ),
            weight="high",
            confidence="high" if has_ai_leadership else "medium",
            source_url=f"https://{company.get('domain', 'example.com')}/team",
        ),
        WeightedJustification(
            signal="github_org_activity",
            status=(
                "No GitHub organization telemetry is available in the current offline dataset."
            ),
            weight="medium",
            confidence="low",
            source_url=None,
        ),
        WeightedJustification(
            signal="executive_commentary",
            status=(
                "Public strategic AI commentary is inferred from named AI practices in the fixture."
                if executive_commentary_detected
                else "No executive commentary signal was captured."
            ),
            weight="medium",
            confidence="medium" if executive_commentary_detected else "low",
            source_url=f"https://{company.get('domain', 'example.com')}",
        ),
        WeightedJustification(
            signal="modern_data_ml_stack",
            status=(
                "Job titles imply a modern data or ML-adjacent stack."
                if stack_detected
                else "No modern data or ML stack signal was inferred from public job titles."
            ),
            weight="low",
            confidence="medium" if stack_detected else "low",
            source_url=f"https://{company.get('domain', 'example.com')}/careers",
        ),
        WeightedJustification(
            signal="strategic_communications",
            status=(
                "Public practices indicate strategic AI or automation messaging."
                if strategic_messaging_detected
                else "No strategic AI messaging signal was observed."
            ),
            weight="low",
            confidence="medium" if strategic_messaging_detected else "low",
            source_url=f"https://{company.get('domain', 'example.com')}",
        ),
    ]

    weighted_points = 0
    if ai_roles_open >= 2:
        weighted_points += WEIGHTS["ai_adjacent_open_roles"]
    elif ai_roles_open == 1:
        weighted_points += 2
    if has_ai_leadership:
        weighted_points += WEIGHTS["named_ai_ml_leadership"]
    if github_activity_detected:
        weighted_points += WEIGHTS["github_org_activity"]
    if executive_commentary_detected:
        weighted_points += 1 if not practices else WEIGHTS["executive_commentary"]
    if stack_detected:
        weighted_points += WEIGHTS["modern_data_ml_stack"]
    if strategic_messaging_detected:
        weighted_points += WEIGHTS["strategic_communications"]

    score = _map_points_to_score(weighted_points)
    confidence = round(
        mean(
            [
                0.9 if ai_roles_open >= 2 else 0.7 if ai_roles_open == 1 else 0.6,
                0.9 if has_ai_leadership else 0.55,
                0.3 if not github_activity_detected else 0.75,
                0.7 if executive_commentary_detected else 0.4,
                0.65 if stack_detected else 0.4,
                0.65 if strategic_messaging_detected else 0.4,
            ]
        ),
        2,
    )

    if weighted_points == 0:
        explanation = "The company is publicly silent on the weighted AI signals in the current dataset, so SignalForge assigns AI maturity score 0."
    else:
        explanation = (
            f"AI maturity score {score} is based on {weighted_points}/{MAX_POINTS} weighted points across high-, medium-, and low-weight public signals."
        )

    return AIMaturityAssessment(
        score=score,
        confidence=confidence,
        weighted_points=weighted_points,
        max_points=MAX_POINTS,
        justifications=justifications,
        explanation=explanation,
    )


def score_ai_maturity(signals: list[dict[str, object]]) -> int:
    if not signals:
        return 0
    value = signals[0].get("value", 0)
    return int(value) if isinstance(value, int) else 0


def _map_points_to_score(weighted_points: int) -> int:
    if weighted_points >= 8:
        return 3
    if weighted_points >= 5:
        return 2
    if weighted_points >= 2:
        return 1
    return 0


def _empty_justifications() -> list[WeightedJustification]:
    return [
        WeightedJustification(
            signal=signal_name,
            status="No data available because the prospect company record is missing.",
            weight="high" if WEIGHTS[signal_name] == 3 else "medium" if WEIGHTS[signal_name] == 2 else "low",
            confidence="low",
        )
        for signal_name in WEIGHTS
    ]

