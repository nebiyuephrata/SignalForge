from __future__ import annotations

from datetime import date, datetime
from statistics import mean

from agent.core.models import (
    AIMaturityAssessment,
    BenchToBriefMatch,
    BuyingWindowSignals,
    EvidenceSignal,
    FundingEvent,
    HiringSignalBrief,
    HiringVelocity,
    LayoffEvent,
    LeadershipChangeEvent,
    SourceAttribution,
)
from agent.signals.ai_maturity import build_ai_maturity_assessment
from agent.signals.segment_classifier import classify_primary_segment
from agent.tenacious.context import load_bench_summary
from agent.tools.crunchbase_tool import CrunchbaseTool
from agent.tools.job_scraper import JobScraper
from agent.tools.layoffs_tool import LayoffsTool, REFERENCE_DATE
from agent.tools.leadership_tool import LeadershipChangeTool


def build_hiring_signal_brief(
    company_name: str,
    crunchbase_tool: CrunchbaseTool,
    layoffs_tool: LayoffsTool | None = None,
    leadership_tool: LeadershipChangeTool | None = None,
    job_scraper: JobScraper | None = None,
    as_of_date: date = REFERENCE_DATE,
) -> dict[str, object]:
    company = crunchbase_tool.lookup_company_record(company_name)
    layoffs_tool = layoffs_tool or LayoffsTool()
    leadership_tool = leadership_tool or LeadershipChangeTool(crunchbase_tool)
    job_scraper = job_scraper or JobScraper(crunchbase_tool)

    if company is None:
        brief = _build_missing_company_brief(company_name=company_name, as_of_date=as_of_date)
        payload = brief.model_dump()
        payload["ai_maturity_score"] = {
            "value": payload["ai_maturity"]["score"],
            "confidence": payload["ai_maturity"]["confidence"],
            "justification": [item["status"] for item in payload["ai_maturity"]["justifications"]],
        }
        return payload

    recent_layoffs = layoffs_tool.get_recent_layoffs(company_name, as_of_date=as_of_date)
    recent_leadership_changes = leadership_tool.get_recent_changes(company_name, as_of_date=as_of_date)
    job_post_scrape = job_scraper.scrape_company_jobs(company_name)
    ai_maturity = build_ai_maturity_assessment(company, role_titles=list(job_post_scrape.get("role_titles", [])))
    recent_funding_event = crunchbase_tool.lookup_recent_funding_event(
        company_name,
        lookback_days=180,
        as_of_date=as_of_date,
    )

    funding_days = _days_since(str(company["funding_date"]), as_of_date)
    open_roles_current = int(job_post_scrape.get("open_roles", 0) or company.get("open_roles_current", 0) or 0)
    open_roles_60_days_ago = int(company.get("open_roles_60_days_ago", 0) or 0)
    velocity_delta = open_roles_current - open_roles_60_days_ago
    velocity_ratio = round(open_roles_current / max(open_roles_60_days_ago, 1), 2) if open_roles_current else 0.0
    role_titles = list(job_post_scrape.get("role_titles", []))
    required_stacks, inferred_stack = _infer_required_stacks(role_titles)
    bench_to_brief = _build_bench_to_brief_match(required_stacks)

    funding_signal = EvidenceSignal(
        signal="funding_event",
        value={
            "round": company["last_funding_round"],
            "date": company["funding_date"],
            "days_since_event": funding_days,
            "source_url": f"https://www.crunchbase.com/organization/{str(company_name).lower().replace(' ', '-')}",
            "within_180_day_window": bool(recent_funding_event),
        },
        confidence=0.95 if funding_days <= 180 else 0.3,
        evidence=[
            f"{company['last_funding_round']} on {company['funding_date']} ({funding_days} days ago).",
            (
                "Funding event falls within the 180-day buying-window filter."
                if recent_funding_event
                else "Funding event is older than the 180-day buying-window filter."
            ),
        ],
        sources=["crunchbase_odm"],
    )
    job_scrape_signal = EvidenceSignal(
        signal="job_post_scrape",
        value={
            "open_roles_scraped": open_roles_current,
            "role_titles": role_titles[:10],
            "source": list(job_post_scrape.get("sources", [])),
        },
        confidence=float(job_post_scrape.get("confidence", 0.0)),
        evidence=list(job_post_scrape.get("evidence", [])),
        sources=list(job_post_scrape.get("sources", [])),
    )
    job_velocity_signal = EvidenceSignal(
        signal="job_post_velocity",
        value={
            "open_roles_current": open_roles_current,
            "open_roles_60_days_ago": open_roles_60_days_ago,
            "delta": velocity_delta,
            "ratio": velocity_ratio,
        },
        confidence=_velocity_confidence(velocity_delta),
        evidence=[f"{open_roles_60_days_ago} roles -> {open_roles_current} roles over the last 60 days."],
        sources=list(job_post_scrape.get("sources", [])),
    )
    layoffs_signal = EvidenceSignal(
        signal="layoffs",
        value=recent_layoffs or [{"reported_at": None, "employees_impacted": 0, "note": "No recent layoffs found."}],
        confidence=0.82 if recent_layoffs else 0.58,
        evidence=(
            [f"{row['employees_impacted']} employees impacted on {row['reported_at']}." for row in recent_layoffs]
            if recent_layoffs
            else ["No layoffs.fyi event was recorded in the last 180 days."]
        ),
        sources=["layoffs_fyi"],
    )
    leadership_signal = EvidenceSignal(
        signal="leadership_change",
        value=recent_leadership_changes or [{"detected": False, "status": "none_recent"}],
        confidence=0.8 if recent_leadership_changes else 0.45,
        evidence=(
            [
                f"{change['change_type']} {change['role']} ({change['person']}) on {change['date']}."
                for change in recent_leadership_changes
            ]
            if recent_leadership_changes
            else ["No leadership change was found in the last 180 days."]
        ),
        sources=["linkedin_public", "company_team_page"],
    )

    primary_segment_match, segment_confidence = classify_primary_segment(
        company=company,
        funding_days=funding_days,
        recent_layoffs=recent_layoffs,
        recent_leadership_changes=recent_leadership_changes,
        ai_maturity_score=ai_maturity.score,
        open_roles_current=open_roles_current,
        as_of_date=as_of_date,
    )
    if segment_confidence < 0.6:
        primary_segment_match = "abstain"

    uncertainty_flags = _uncertainty_flags(
        ai_maturity=ai_maturity,
        bench_to_brief=bench_to_brief,
        funding_days=funding_days,
        recent_layoffs=recent_layoffs,
        segment_confidence=segment_confidence,
        velocity_signal=job_velocity_signal,
        company=company,
    )
    overall_confidence = round(
        mean(
            [
                funding_signal.confidence,
                job_scrape_signal.confidence,
                job_velocity_signal.confidence,
                layoffs_signal.confidence,
                leadership_signal.confidence,
                ai_maturity.confidence,
            ]
        ),
        2,
    )

    brief = HiringSignalBrief(
        company_name=company_name,
        prospect_domain=str(company["domain"]),
        prospect_name=company_name,
        as_of_date=as_of_date.isoformat(),
        summary=_summary(
            company_name=company_name,
            funding_round=str(company["last_funding_round"]),
            funding_date=str(company["funding_date"]),
            recent_layoffs=recent_layoffs,
            open_roles_current=open_roles_current,
            open_roles_60_days_ago=open_roles_60_days_ago,
            velocity_delta=velocity_delta,
        ),
        primary_segment_match=primary_segment_match,
        segment_confidence=round(segment_confidence, 2),
        ai_maturity=ai_maturity,
        hiring_velocity=HiringVelocity(
            open_roles_today=open_roles_current,
            open_roles_60_days_ago=open_roles_60_days_ago,
            delta=velocity_delta,
            velocity_label=_velocity_label(delta=velocity_delta, ratio=velocity_ratio, open_roles_current=open_roles_current),
            signal_confidence=job_velocity_signal.confidence,
            sources=list(job_post_scrape.get("sources", [])),
            role_titles=role_titles[:10],
        ),
        buying_window_signals=BuyingWindowSignals(
            funding_event=FundingEvent(
                detected=bool(company.get("last_funding_round")),
                stage=_normalize_funding_stage(str(company.get("last_funding_round", ""))),
                closed_at=str(company["funding_date"]),
                days_since_event=funding_days,
                source_url=funding_signal.value["source_url"],
                confidence=funding_signal.confidence,
            ),
            layoff_event=LayoffEvent(
                detected=bool(recent_layoffs),
                date=recent_layoffs[0]["reported_at"] if recent_layoffs else None,
                headcount_reduction=int(recent_layoffs[0]["employees_impacted"]) if recent_layoffs else 0,
                source_url="https://layoffs.fyi/",
                confidence=layoffs_signal.confidence,
            ),
            leadership_change=LeadershipChangeEvent(
                detected=bool(recent_leadership_changes),
                role=_normalize_leadership_role(recent_leadership_changes[0]["role"]) if recent_leadership_changes else "none",
                new_leader_name=recent_leadership_changes[0]["person"] if recent_leadership_changes else None,
                started_at=recent_leadership_changes[0]["date"] if recent_leadership_changes else None,
                source_url=recent_leadership_changes[0].get("source_url") if recent_leadership_changes else None,
                confidence=leadership_signal.confidence,
            ),
        ),
        tech_stack=inferred_stack,
        bench_to_brief_match=bench_to_brief,
        data_sources_checked=_data_sources_checked(
            company=company,
            job_post_scrape=job_post_scrape,
            leadership_detected=bool(recent_leadership_changes),
        ),
        signals=[funding_signal, job_scrape_signal, job_velocity_signal, layoffs_signal, leadership_signal],
        overall_confidence=overall_confidence,
        uncertainty_flags=uncertainty_flags,
        source_artifact={
            "funding_event": funding_signal.model_dump(),
            "job_post_scrape": job_scrape_signal.model_dump(),
            "job_post_velocity": job_velocity_signal.model_dump(),
            "layoffs": layoffs_signal.model_dump(),
            "leadership_change": leadership_signal.model_dump(),
            "ai_maturity": ai_maturity.model_dump(),
        },
    )
    payload = brief.model_dump()
    payload["ai_maturity_score"] = {
        "value": payload["ai_maturity"]["score"],
        "confidence": payload["ai_maturity"]["confidence"],
        "justification": [item["status"] for item in payload["ai_maturity"]["justifications"]],
    }
    return payload


def _build_missing_company_brief(company_name: str, as_of_date: date) -> HiringSignalBrief:
    ai_maturity = build_ai_maturity_assessment(None)
    return HiringSignalBrief(
        company_name=company_name,
        prospect_domain="unknown",
        prospect_name=company_name,
        as_of_date=as_of_date.isoformat(),
        summary="No Crunchbase record was found, so SignalForge cannot make a grounded hiring claim for this prospect yet.",
        primary_segment_match="abstain",
        segment_confidence=0.0,
        ai_maturity=ai_maturity,
        hiring_velocity=HiringVelocity(
            open_roles_today=0,
            open_roles_60_days_ago=0,
            delta=0,
            velocity_label="insufficient_signal",
            signal_confidence=0.0,
            sources=[],
            role_titles=[],
        ),
        buying_window_signals=BuyingWindowSignals(
            funding_event=FundingEvent(detected=False, stage="none", confidence=0.0),
            layoff_event=LayoffEvent(detected=False, confidence=0.0),
            leadership_change=LeadershipChangeEvent(detected=False, role="none", confidence=0.0),
        ),
        tech_stack=[],
        bench_to_brief_match=BenchToBriefMatch(required_stacks=[], bench_available=False, gaps=[]),
        data_sources_checked=[
            SourceAttribution(
                source="crunchbase_odm",
                status="no_data",
                confidence=0.0,
                detail="No Crunchbase company record was found.",
                fallback_todo="Add the prospect to the deterministic fixture or connect the real Crunchbase export.",
            )
        ],
        signals=[],
        overall_confidence=0.0,
        uncertainty_flags=["missing_crunchbase_record"],
        source_artifact={},
    )


def _days_since(iso_date: str, as_of_date: date) -> int:
    event_date = datetime.strptime(iso_date, "%Y-%m-%d").date()
    return (as_of_date - event_date).days


def _normalize_funding_stage(stage: str) -> str:
    normalized = stage.strip().lower()
    mapping = {
        "seed": "seed",
        "series a": "series_a",
        "series b": "series_b",
        "series c": "series_c",
        "series d": "series_d_plus",
        "growth": "series_d_plus",
        "debt": "debt",
    }
    return mapping.get(normalized, "other" if normalized else "none")


def _velocity_label(*, delta: int, ratio: float, open_roles_current: int) -> str:
    if open_roles_current == 0:
        return "insufficient_signal"
    if delta <= 0:
        return "declined" if delta < 0 else "flat"
    if ratio >= 3:
        return "tripled_or_more"
    if ratio >= 2:
        return "doubled"
    return "increased_modestly"


def _velocity_confidence(delta: int) -> float:
    if delta >= 6:
        return 0.88
    if delta >= 3:
        return 0.8
    if delta > 0:
        return 0.62
    if delta == 0:
        return 0.45
    return 0.35


def _infer_required_stacks(role_titles: list[str]) -> tuple[list[str], list[str]]:
    required: list[str] = []
    tech_stack: list[str] = []
    normalized = " ".join(role_titles).lower()
    if any(keyword in normalized for keyword in ("backend", "python", "api", "platform")):
        required.append("python")
        tech_stack.extend(["Python", "FastAPI"])
    if any(keyword in normalized for keyword in ("data", "analytics", "warehouse")):
        required.append("data")
        tech_stack.extend(["dbt", "Snowflake"])
    if any(keyword in normalized for keyword in ("machine learning", "ml ", "mlops", "ai")):
        required.append("ml")
        tech_stack.extend(["ML", "MLOps"])
    if any(keyword in normalized for keyword in ("frontend", "react", "typescript")):
        required.append("frontend")
        tech_stack.extend(["React", "TypeScript"])
    if any(keyword in normalized for keyword in ("site reliability", "devops", "infrastructure", "security")):
        required.append("infra")
        tech_stack.extend(["AWS", "Docker"])
    return list(dict.fromkeys(required)), list(dict.fromkeys(tech_stack))


def _build_bench_to_brief_match(required_stacks: list[str]) -> BenchToBriefMatch:
    bench_summary = load_bench_summary()
    stacks = bench_summary.get("stacks", {}) if isinstance(bench_summary, dict) else {}
    gaps = [
        stack
        for stack in required_stacks
        if not isinstance(stacks, dict) or int(stacks.get(stack, {}).get("available_engineers", 0) or 0) <= 0
    ]
    return BenchToBriefMatch(
        required_stacks=required_stacks,
        bench_available=bool(required_stacks) and not gaps,
        gaps=gaps,
    )


def _data_sources_checked(
    *,
    company: dict[str, object],
    job_post_scrape: dict[str, object],
    leadership_detected: bool,
) -> list[SourceAttribution]:
    source_artifact = job_post_scrape.get("source_artifact", {})
    company_page_source = SourceAttribution.model_validate(
        source_artifact.get(
            "company_careers_page",
            {
                "source": "company_careers_page",
                "status": "no_data",
                "confidence": 0.0,
                "detail": "No careers page result was captured.",
            },
        )
    )
    return [
        SourceAttribution(
            source="crunchbase_odm",
            status="success",
            source_url=f"https://www.crunchbase.com/organization/{str(company['company_name']).lower().replace(' ', '-')}",
            confidence=0.95,
            detail="Loaded deterministic company record and funding metadata.",
        ),
        company_page_source,
        *[
            SourceAttribution.model_validate(value)
            for key, value in source_artifact.items()
            if key in {"builtin", "wellfound", "linkedin_public"}
        ],
        SourceAttribution(
            source="layoffs_fyi",
            status="success",
            source_url="https://layoffs.fyi/",
            confidence=0.82,
            detail="Parsed layoffs.fyi CSV fixture.",
        ),
        SourceAttribution(
            source="leadership_change_detection",
            status="success" if leadership_detected else "no_data",
            source_url=f"https://{company['domain']}/team",
            confidence=0.8 if leadership_detected else 0.45,
            detail="Leadership changes were read from public company fixture data.",
        ),
    ]


def _uncertainty_flags(
    *,
    ai_maturity: AIMaturityAssessment,
    bench_to_brief: BenchToBriefMatch,
    funding_days: int,
    recent_layoffs: list[dict[str, str]],
    segment_confidence: float,
    velocity_signal: EvidenceSignal,
    company: dict[str, object],
) -> list[str]:
    flags: list[str] = []
    if funding_days > 180:
        flags.append("stale_funding_signal")
    if velocity_signal.confidence < 0.65:
        flags.append("weak_hiring_velocity_signal")
    if ai_maturity.confidence < 0.7:
        flags.append("weak_ai_maturity_signal")
    if recent_layoffs and velocity_signal.value["delta"] > 0:
        flags.append("layoff_overrides_funding")
    if segment_confidence < 0.6:
        flags.append("conflicting_segment_signals")
    if bench_to_brief.gaps:
        flags.append("bench_gap_detected")
    if not company.get("career_page_path"):
        flags.append("missing_public_career_page")
    return flags


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


def _summary(
    *,
    company_name: str,
    funding_round: str,
    funding_date: str,
    recent_layoffs: list[dict[str, str]],
    open_roles_current: int,
    open_roles_60_days_ago: int,
    velocity_delta: int,
) -> str:
    if recent_layoffs and velocity_delta > 0:
        return (
            f"{company_name} shows mixed but timely hiring intent: roles moved from {open_roles_60_days_ago} to "
            f"{open_roles_current} over 60 days after a {funding_round} on {funding_date}, but layoffs were also recorded recently."
        )
    if velocity_delta >= 3:
        return (
            f"{company_name} appears to be hiring more actively: roles moved from {open_roles_60_days_ago} to "
            f"{open_roles_current} over 60 days following a {funding_round} on {funding_date}."
        )
    if velocity_delta > 0:
        return (
            f"{company_name} shows only a small increase in open roles in the deterministic dataset, so the signal is directional rather than conclusive."
        )
    return f"{company_name} has limited near-term hiring momentum in the deterministic dataset, so messaging should remain exploratory."
