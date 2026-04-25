from __future__ import annotations

from statistics import mean

from agent.core.models import AIMaturityAssessment, AIMaturitySignalInput, AIMaturitySignalInputs, WeightedJustification


WEIGHT_POINTS = {
    "high": 3,
    "medium": 2,
    "low": 1,
}

SIGNAL_MAX_POINTS = {
    "ai_adjacent_open_roles": 3,
    "named_ai_ml_leadership": 3,
    "github_org_activity": 2,
    "executive_commentary": 2,
    "modern_data_ml_stack": 1,
    "strategic_communications": 1,
}

MAX_POINTS = sum(SIGNAL_MAX_POINTS.values())


def build_ai_maturity_assessment(
    company: dict[str, object] | None,
    *,
    role_titles: list[str] | None = None,
) -> AIMaturityAssessment:
    inputs = collect_ai_maturity_inputs(company, role_titles=role_titles)
    return score_ai_maturity_inputs(inputs)


def collect_ai_maturity_inputs(
    company: dict[str, object] | None,
    *,
    role_titles: list[str] | None = None,
) -> AIMaturitySignalInputs:
    if not company:
        return _empty_inputs()

    ai_roles_open = int(company.get("ai_roles_open", 0) or 0)
    leadership_changes = company.get("leadership_changes", [])
    practices = [str(item) for item in company.get("ai_practices", []) if str(item).strip()]
    normalized_roles = " ".join(role_titles or []).lower()
    practices_blob = " ".join(practices).lower()

    has_ai_leadership = any(
        isinstance(change, dict)
        and any(keyword in str(change.get("role", "")).lower() for keyword in ("ai", "ml", "data"))
        for change in leadership_changes
    )
    github_activity_detected = bool(company.get("github_org_activity"))
    executive_commentary_detected = bool(practices)
    stack_detected = any(keyword in normalized_roles for keyword in ("ml", "machine learning", "data", "platform", "analytics"))
    strategic_messaging_detected = any(
        keyword in practices_blob
        for keyword in ("governance", "copilot", "automation", "evaluation", "monitoring", "ai")
    )

    domain = str(company.get("domain", "example.com"))
    return AIMaturitySignalInputs(
        ai_adjacent_open_roles=AIMaturitySignalInput(
            signal="ai_adjacent_open_roles",
            weight="high",
            points_awarded=3 if ai_roles_open >= 2 else 2 if ai_roles_open == 1 else 0,
            detected=ai_roles_open > 0,
            raw_value=str(ai_roles_open),
            confidence="high" if ai_roles_open >= 2 else "medium" if ai_roles_open == 1 else "low",
            source_url=f"https://{domain}/careers",
            justification=(
                f"{ai_roles_open} AI-adjacent roles are open."
                if ai_roles_open
                else "No AI-adjacent roles are open in the structured record."
            ),
        ),
        named_ai_ml_leadership=AIMaturitySignalInput(
            signal="named_ai_ml_leadership",
            weight="high",
            points_awarded=3 if has_ai_leadership else 0,
            detected=has_ai_leadership,
            raw_value="present" if has_ai_leadership else "absent",
            confidence="high" if has_ai_leadership else "medium",
            source_url=f"https://{domain}/team",
            justification=(
                "A named AI/data leadership signal is present."
                if has_ai_leadership
                else "No named AI/ML leadership appointment is present."
            ),
        ),
        github_org_activity=AIMaturitySignalInput(
            signal="github_org_activity",
            weight="medium",
            points_awarded=2 if github_activity_detected else 0,
            detected=github_activity_detected,
            raw_value="present" if github_activity_detected else "absent",
            confidence="medium" if github_activity_detected else "low",
            source_url=str(company.get("github_org_url") or "") or None,
            justification=(
                "Public GitHub organization activity is present in the structured company record."
                if github_activity_detected
                else "No GitHub organization telemetry is available in the current offline dataset."
            ),
        ),
        executive_commentary=AIMaturitySignalInput(
            signal="executive_commentary",
            weight="medium",
            points_awarded=2 if executive_commentary_detected else 0,
            detected=executive_commentary_detected,
            raw_value=", ".join(practices[:3]) if practices else "absent",
            confidence="medium" if executive_commentary_detected else "low",
            source_url=f"https://{domain}",
            justification=(
                "Public strategic AI commentary is inferred from named AI practices in the fixture."
                if executive_commentary_detected
                else "No executive commentary signal was captured."
            ),
        ),
        modern_data_ml_stack=AIMaturitySignalInput(
            signal="modern_data_ml_stack",
            weight="low",
            points_awarded=1 if stack_detected else 0,
            detected=stack_detected,
            raw_value="detected" if stack_detected else "not_detected",
            confidence="medium" if stack_detected else "low",
            source_url=f"https://{domain}/careers",
            justification=(
                "Job titles imply a modern data or ML-adjacent stack."
                if stack_detected
                else "No modern data or ML stack signal was inferred from public job titles."
            ),
        ),
        strategic_communications=AIMaturitySignalInput(
            signal="strategic_communications",
            weight="low",
            points_awarded=1 if strategic_messaging_detected else 0,
            detected=strategic_messaging_detected,
            raw_value="detected" if strategic_messaging_detected else "not_detected",
            confidence="medium" if strategic_messaging_detected else "low",
            source_url=f"https://{domain}",
            justification=(
                "Public practices indicate strategic AI or automation messaging."
                if strategic_messaging_detected
                else "No strategic AI messaging signal was observed."
            ),
        ),
    )


def score_ai_maturity_inputs(inputs: AIMaturitySignalInputs) -> AIMaturityAssessment:
    weighted_points = sum(signal.points_awarded for signal in inputs.ordered())
    score = _map_points_to_score(weighted_points)
    justifications = [
        WeightedJustification(
            signal=signal.signal,
            status=signal.justification,
            weight=signal.weight,
            confidence=signal.confidence,
            source_url=signal.source_url,
        )
        for signal in inputs.ordered()
    ]

    if weighted_points == 0:
        explanation = (
            "The company is publicly silent on the weighted AI signals in the current dataset, "
            "so SignalForge assigns AI maturity score 0. Absence of evidence is not proof of absence."
        )
        confidence = 0.35
    else:
        explanation = (
            f"AI maturity score {score} is based on {weighted_points}/{MAX_POINTS} weighted points across "
            "high-, medium-, and low-weight public signals."
        )
        confidence = round(
            mean([_confidence_to_numeric(signal.confidence) for signal in inputs.ordered()]),
            2,
        )

    return AIMaturityAssessment(
        score=max(0, min(3, score)),
        confidence=confidence,
        weighted_points=weighted_points,
        max_points=MAX_POINTS,
        justifications=justifications,
        explanation=explanation,
    )


def score_ai_maturity(signals: AIMaturitySignalInputs | list[dict[str, object]]) -> int:
    if isinstance(signals, AIMaturitySignalInputs):
        return score_ai_maturity_inputs(signals).score
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


def _empty_inputs() -> AIMaturitySignalInputs:
    empty_signal = lambda signal_name, weight: AIMaturitySignalInput(  # noqa: E731
        signal=signal_name,
        weight=weight,
        points_awarded=0,
        detected=False,
        raw_value="missing_company_record",
        confidence="low",
        source_url=None,
        justification="No data available because the prospect company record is missing.",
    )
    return AIMaturitySignalInputs(
        ai_adjacent_open_roles=empty_signal("ai_adjacent_open_roles", "high"),
        named_ai_ml_leadership=empty_signal("named_ai_ml_leadership", "high"),
        github_org_activity=empty_signal("github_org_activity", "medium"),
        executive_commentary=empty_signal("executive_commentary", "medium"),
        modern_data_ml_stack=empty_signal("modern_data_ml_stack", "low"),
        strategic_communications=empty_signal("strategic_communications", "low"),
    )


def _confidence_to_numeric(value: str) -> float:
    mapping = {"high": 0.9, "medium": 0.65, "low": 0.35}
    return mapping.get(value, 0.35)
