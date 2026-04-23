from __future__ import annotations

from datetime import date, datetime
from statistics import mean

from agent.tools.job_scraper import JobScraper
from agent.tools.leadership_tool import LeadershipChangeTool
from agent.signals.ai_maturity import build_ai_maturity_assessment
from agent.signals.segment_classifier import classify_primary_segment
from agent.tenacious.context import load_bench_summary
from agent.tools.crunchbase_tool import CrunchbaseTool
from agent.tools.layoffs_tool import LayoffsTool, REFERENCE_DATE


def _days_since(iso_date: str, as_of_date: date) -> int:
    event_date = datetime.strptime(iso_date, "%Y-%m-%d").date()
    return (as_of_date - event_date).days


def _velocity_label(delta: int, ratio: float) -> str:
    if delta <= 0:
        return "declined" if delta < 0 else "flat"
    if ratio >= 3:
        return "tripled_or_more"
    if ratio >= 2:
        return "doubled"
    return "increased_modestly"


def _infer_required_stacks(role_titles: list[str]) -> tuple[list[str], list[str]]:
    required: list[str] = []
    tech_stack: list[str] = []
    normalized = " ".join(role_titles).lower()
    if any(keyword in normalized for keyword in ("backend", "python", "api", "platform")):
        required.append("python")
        tech_stack.extend(["Python", "FastAPI"])
    if any(keyword in normalized for keyword in ("data", "analytics", "dbt", "warehouse")):
        required.append("data")
        tech_stack.extend(["dbt", "Snowflake"])
    if any(keyword in normalized for keyword in ("machine learning", "ml ", "ai ", "mlops")):
        required.append("ml")
        tech_stack.extend(["ML", "MLOps"])
    if any(keyword in normalized for keyword in ("frontend", "react", "typescript", "product designer")):
        required.append("frontend")
        tech_stack.extend(["React", "TypeScript"])
    if any(keyword in normalized for keyword in ("site reliability", "devops", "infrastructure", "security")):
        required.append("infra")
        tech_stack.extend(["AWS", "Docker"])
    dedup_required = list(dict.fromkeys(required))
    dedup_stack = list(dict.fromkeys(tech_stack))
    return dedup_required, dedup_stack


def _build_data_sources_checked(
    *,
    as_of_date: date,
    job_scrape_source: str,
    leadership_detected: bool,
) -> list[dict[str, str]]:
    fetched_at = f"{as_of_date.isoformat()}T09:00:00Z"
    return [
        {"source": "crunchbase_odm", "status": "success", "fetched_at": fetched_at},
        {"source": "layoffs_fyi", "status": "success", "fetched_at": fetched_at},
        {
            "source": "company_careers_page",
            "status": "success" if job_scrape_source != "missing_career_page" else "no_data",
            "fetched_at": fetched_at,
        },
        {
            "source": "linkedin_public_leadership",
            "status": "success" if leadership_detected else "no_data",
            "fetched_at": fetched_at,
        },
    ]


def _normalize_leadership_role(role: str) -> str:
    normalized = role.strip().lower()
    if "cto" in normalized:
        return "cto"
    if "vp engineering" in normalized or "vp eng" in normalized:
        return "vp_engineering"
    if "cio" in normalized:
        return "cio"
    if "chief data" in normalized:
        return "chief_data_officer"
    if "head of ai" in normalized or "head of ml" in normalized:
        return "head_of_ai"
    return "other" if normalized else "none"


def build_hiring_signal_brief(
    company_name: str,
    crunchbase_tool: CrunchbaseTool,
    layoffs_tool: LayoffsTool | None = None,
    leadership_tool: LeadershipChangeTool | None = None,
    job_scraper: JobScraper | None = None,
    as_of_date: date = REFERENCE_DATE,
) -> dict[str, object]:
    company = crunchbase_tool.get_company_by_name(company_name)
    if company is None:
        raise ValueError(f"Company not found in local dataset: {company_name}")

    layoffs_tool = layoffs_tool or LayoffsTool()
    leadership_tool = leadership_tool or LeadershipChangeTool(crunchbase_tool)
    job_scraper = job_scraper or JobScraper(crunchbase_tool)
    recent_layoffs = layoffs_tool.get_recent_layoffs(company_name, as_of_date=as_of_date)
    recent_leadership_changes = leadership_tool.get_recent_changes(company_name, as_of_date=as_of_date)
    job_post_scrape = job_scraper.scrape_company_jobs(company_name)
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

    scraped_open_roles = int(job_post_scrape.get("open_roles", 0) or 0)
    open_roles_current = scraped_open_roles or int(company["open_roles_current"])
    open_roles_60_days_ago = int(company["open_roles_60_days_ago"])
    velocity_delta = open_roles_current - open_roles_60_days_ago
    velocity_ratio = round(open_roles_current / max(open_roles_60_days_ago, 1), 2)
    role_titles = list(job_post_scrape.get("role_titles", []))
    job_scrape_signal = {
        "signal": "job_post_scrape",
        "value": {
            "open_roles_scraped": open_roles_current,
            "role_titles": role_titles[:10],
            "source": job_post_scrape.get("source", "unknown"),
        },
        "confidence": float(job_post_scrape.get("confidence", 0.3)),
        "evidence": list(job_post_scrape.get("evidence", [])),
    }
    job_velocity_signal = {
        "signal": "job_post_velocity",
        "value": {
            "open_roles_current": open_roles_current,
            "open_roles_60_days_ago": open_roles_60_days_ago,
            "delta": velocity_delta,
            "ratio": velocity_ratio,
        },
        "confidence": 0.85 if velocity_delta >= 3 else 0.6 if velocity_delta > 0 else 0.35 if velocity_delta < 0 else 0.4,
        "evidence": [
            f"{open_roles_60_days_ago} roles -> {open_roles_current} roles in 60 days",
            *job_scrape_signal["evidence"][:1],
        ],
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
        "value": recent_leadership_changes or [{"detected": False, "status": "none_recent"}],
        "confidence": 0.78 if recent_leadership_changes else 0.35,
        "evidence": (
            [
                f"{change['change_type']} {change['role']} ({change['person']}) on {change['date']}"
                for change in recent_leadership_changes
            ]
            if recent_leadership_changes
            else ["No recent leadership changes were found in the synthetic company record."]
        ),
    }

    signals = [funding_signal, job_scrape_signal, job_velocity_signal, layoffs_signal, leadership_signal]
    overall_confidence = round(mean(signal["confidence"] for signal in signals + [ai_maturity]), 2)
    primary_segment_match, segment_confidence = classify_primary_segment(
        company=company,
        funding_days=funding_days,
        recent_layoffs=recent_layoffs,
        recent_leadership_changes=recent_leadership_changes,
        ai_maturity_score=int(ai_maturity["score"]),
        open_roles_current=open_roles_current,
        as_of_date=as_of_date,
    )
    required_stacks, inferred_tech_stack = _infer_required_stacks(role_titles)
    bench_summary = load_bench_summary()
    bench_stacks = bench_summary.get("stacks", {}) if isinstance(bench_summary, dict) else {}
    bench_gaps = [
        stack
        for stack in required_stacks
        if not isinstance(bench_stacks, dict)
        or int(bench_stacks.get(stack, {}).get("available_engineers", 0) or 0) <= 0
    ]
    honesty_flags: list[str] = []
    if job_velocity_signal["confidence"] < 0.65:
        honesty_flags.append("weak_hiring_velocity_signal")
    if ai_maturity["confidence"] < 0.7:
        honesty_flags.append("weak_ai_maturity_signal")
    if recent_layoffs and funding_days <= 180:
        honesty_flags.append("layoff_overrides_funding")
    if segment_confidence < 0.6:
        honesty_flags.append("conflicting_segment_signals")
    if bench_gaps:
        honesty_flags.append("bench_gap_detected")
    if inferred_tech_stack:
        honesty_flags.append("tech_stack_inferred_not_confirmed")

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
        "prospect_domain": str(company["domain"]),
        "prospect_name": company_name,
        "as_of_date": as_of_date.isoformat(),
        "generated_at": f"{as_of_date.isoformat()}T09:00:00Z",
        "summary": summary,
        "signals": signals,
        "ai_maturity_score": ai_maturity,
        "ai_maturity": {
            "score": int(ai_maturity["score"]),
            "confidence": float(ai_maturity["confidence"]),
            "justifications": list(ai_maturity.get("justifications", [])),
        },
        "overall_confidence": overall_confidence,
        "primary_segment_match": primary_segment_match,
        "segment_confidence": segment_confidence,
        "hiring_velocity": {
            "open_roles_today": open_roles_current,
            "open_roles_60_days_ago": open_roles_60_days_ago,
            "velocity_label": _velocity_label(velocity_delta, velocity_ratio),
            "signal_confidence": job_velocity_signal["confidence"],
            "sources": ["company_careers_page"],
        },
        "buying_window_signals": {
            "funding_event": {
                "detected": funding_days <= 365,
                "stage": str(company["last_funding_round"]).strip().lower().replace(" ", "_"),
                "closed_at": str(company["funding_date"]),
                "source_url": f"https://www.crunchbase.com/organization/{str(company['domain']).split('.')[0]}",
            },
            "layoff_event": {
                "detected": bool(recent_layoffs),
                "date": recent_layoffs[0]["reported_at"] if recent_layoffs else None,
                "headcount_reduction": int(recent_layoffs[0]["employees_impacted"]) if recent_layoffs else 0,
                "source_url": "https://layoffs.fyi/",
            },
            "leadership_change": {
                "detected": bool(recent_leadership_changes),
                "role": _normalize_leadership_role(str(recent_leadership_changes[0]["role"])) if recent_leadership_changes else "none",
                "new_leader_name": recent_leadership_changes[0]["person"] if recent_leadership_changes else "",
                "started_at": recent_leadership_changes[0]["date"] if recent_leadership_changes else None,
                "source_url": f"https://{company['domain']}/team",
            },
        },
        "tech_stack": inferred_tech_stack,
        "bench_to_brief_match": {
            "required_stacks": required_stacks,
            "bench_available": not bench_gaps,
            "gaps": bench_gaps,
        },
        "data_sources_checked": _build_data_sources_checked(
            as_of_date=as_of_date,
            job_scrape_source=str(job_post_scrape.get("source", "unknown")),
            leadership_detected=bool(recent_leadership_changes),
        ),
        "honesty_flags": honesty_flags,
        "source_artifact": {
            "crunchbase_company_profile": {
                "confidence": 0.95,
                "evidence": [f"Loaded firmographics for {company_name} from the local Crunchbase fixture."],
            },
            "job_post_scrape": job_scrape_signal,
            "layoffs": layoffs_signal,
            "leadership_change": leadership_signal,
        },
    }
