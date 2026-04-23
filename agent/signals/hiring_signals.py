from __future__ import annotations

from datetime import date, datetime
from statistics import mean

from agent.signals.ai_maturity import build_ai_maturity_assessment
from agent.tools.crunchbase_tool import CrunchbaseTool
from agent.tools.layoffs_tool import LayoffsTool, REFERENCE_DATE


def _days_since(iso_date: str, as_of_date: date) -> int:
    event_date = datetime.strptime(iso_date, "%Y-%m-%d").date()
    return (as_of_date - event_date).days


def build_hiring_signal_brief(
    company_name: str,
    crunchbase_tool: CrunchbaseTool,
    layoffs_tool: LayoffsTool | None = None,
    as_of_date: date = REFERENCE_DATE,
) -> dict[str, object]:
    company = crunchbase_tool.get_company_by_name(company_name)
    if company is None:
        raise ValueError(f"Company not found in local dataset: {company_name}")

    layoffs_tool = layoffs_tool or LayoffsTool()
    recent_layoffs = layoffs_tool.get_recent_layoffs(company_name, as_of_date=as_of_date)
    ai_maturity = build_ai_maturity_assessment(company)

    funding_days = _days_since(str(company["funding_date"]), as_of_date)
    funding_signal = {
        "signal": "funding_event",
        "value": {
            "round": company["last_funding_round"],
            "date": company["funding_date"],
            "days_since_event": funding_days,
        },
        "confidence": 0.95 if funding_days <= 180 else 0.3,
        "evidence": [f"{company['last_funding_round']} on {company['funding_date']}"],
    }

    open_roles_current = int(company["open_roles_current"])
    open_roles_60_days_ago = int(company["open_roles_60_days_ago"])
    velocity_delta = open_roles_current - open_roles_60_days_ago
    velocity_ratio = round(open_roles_current / max(open_roles_60_days_ago, 1), 2)
    job_velocity_signal = {
        "signal": "job_post_velocity",
        "value": {
            "open_roles_current": open_roles_current,
            "open_roles_60_days_ago": open_roles_60_days_ago,
            "delta": velocity_delta,
            "ratio": velocity_ratio,
        },
        "confidence": 0.85 if velocity_delta >= 3 else 0.6 if velocity_delta > 0 else 0.35 if velocity_delta < 0 else 0.4,
        "evidence": [f"{open_roles_60_days_ago} roles -> {open_roles_current} roles in 60 days"],
    }

    layoffs_signal = {
        "signal": "layoffs",
        "value": recent_layoffs
        or [{"reported_at": None, "employees_impacted": 0, "note": "No layoffs in the last 180 days"}],
        "confidence": 0.8 if recent_layoffs else 0.55,
        "evidence": (
            [f"{row['employees_impacted']} employees impacted on {row['reported_at']}" for row in recent_layoffs]
            if recent_layoffs
            else ["No layoffs found in local layoffs dataset for the last 180 days"]
        ),
    }

    leadership_signal = {
        "signal": "leadership_change",
        "value": {"detected": False, "status": "stub"},
        "confidence": 0.2,
        "evidence": ["Leadership change detection is stubbed in the local-first version."],
    }

    signals = [funding_signal, job_velocity_signal, layoffs_signal, leadership_signal]
    overall_confidence = round(mean(signal["confidence"] for signal in signals + [ai_maturity]), 2)

    if recent_layoffs and velocity_delta > 0:
        summary = (
            f"{company_name} shows mixed but timely hiring intent: headcount demand rose from "
            f"{open_roles_60_days_ago} to {open_roles_current} open roles in 60 days after a "
            f"{company['last_funding_round']} on {company['funding_date']}, while a smaller layoff "
            f"was also recorded in the last 180 days."
        )
    elif velocity_delta >= 3:
        summary = (
            f"{company_name} appears to be hiring more actively: open roles moved from "
            f"{open_roles_60_days_ago} to {open_roles_current} in 60 days following "
            f"{company['last_funding_round']} on {company['funding_date']}."
        )
    elif velocity_delta > 0:
        summary = (
            f"{company_name} shows only a small increase in open roles in the local dataset, so the "
            "signal should be treated as directional rather than conclusive."
        )
    else:
        summary = (
            f"{company_name} has limited near-term hiring momentum in the local dataset, so messaging "
            "should stay exploratory."
        )

    return {
        "company_name": company_name,
        "as_of_date": as_of_date.isoformat(),
        "summary": summary,
        "signals": signals,
        "ai_maturity_score": ai_maturity,
        "overall_confidence": overall_confidence,
    }
