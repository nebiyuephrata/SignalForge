from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
TRACE_LOG = REPO_ROOT / "eval" / "logs" / "trace_log.jsonl"
PROBE_LIBRARY = REPO_ROOT / "probes" / "probe_library.json"
BENCH_ROOT = REPO_ROOT / "tenacious_bench_v0.1"
SEED_ROOT = REPO_ROOT / "tenacious_sales_data" / "tenacious_sales_data" / "seed"
SYNTHESIS_CACHE = REPO_ROOT / "generation_scripts" / "synthesis_cache.json"

ALLOWED_SUBJECT_PREFIXES = ["request:", "question:", "context:", "follow-up:"]
TENACIOUS_BANNED_PHRASES = [
    "clearly scaling aggressively",
    "definitely need",
    "top talent",
    "world-class",
    "rockstar",
    "ninja",
    "you need offshore capacity",
]

@dataclass(frozen=True)
class CompanyProfile:
    name: str
    confidence: float
    company_size: str
    headcount_band: str
    sector: str
    location: str
    stage: str
    stack: str
    bench_state: str
    ai_maturity_score: float
    buying_center: str


COMPANY_PROFILES = [
    CompanyProfile("Northstar Lending", 0.72, "mid-market", "220-350", "fintech lender", "Austin, TX", "Series B", "Python / Postgres / dbt", "bench_gap_visible", 1.1, "VP Engineering"),
    CompanyProfile("Quiet Current Bank", 0.42, "regional", "500-900", "regulated bank", "Nashville, TN", "Series A", "Java / Oracle / Mulesoft", "bench_gap_thin", 0.4, "Head of Platform"),
    CompanyProfile("Harborline Ledger", 0.57, "startup", "50-120", "payments ledger platform", "Seattle, WA", "Seed", "Go / Kafka / GCP", "bench_gap_unclear", 0.7, "New CTO"),
    CompanyProfile("Beacon Ridge Payments", 0.81, "enterprise", "1200-2000", "payments processor", "Chicago, IL", "Series C", "Python / Snowflake / AWS", "bench_gap_visible", 1.6, "Director of AI Operations"),
    CompanyProfile("Elm Street Treasury", 0.68, "mid-market", "180-260", "treasury ops SaaS", "New York, NY", "Series B", "TypeScript / Postgres / Azure", "bench_gap_mixed", 0.9, "VP Risk Engineering"),
    CompanyProfile("Delta Pine Credit", 0.76, "growth", "300-500", "credit infra company", "Atlanta, GA", "Growth", "Kotlin / BigQuery / GCP", "bench_gap_visible", 1.3, "CTO"),
    CompanyProfile("Apex Harbor Finance", 0.79, "enterprise", "900-1400", "enterprise finance platform", "London, UK", "Growth", "Java / Databricks / AWS", "bench_gap_visible", 1.4, "Head of Platform"),
    CompanyProfile("Cinder Vault Capital", 0.51, "startup", "70-140", "capital markets tooling", "Berlin, DE", "Series A", "Python / Airflow / GCP", "bench_gap_thin", 0.6, "VP Engineering"),
    CompanyProfile("Marula Core Systems", 0.61, "growth", "250-380", "East Africa core banking vendor", "Nairobi, KE", "Series B", "Java / Postgres / on-prem", "bench_gap_mixed", 0.8, "COO"),
    CompanyProfile("Sable River Underwriting", 0.55, "mid-market", "140-220", "insurtech workflow platform", "Dublin, IE", "Series A", "Python / AWS / Terraform", "bench_gap_unclear", 0.75, "VP Engineering"),
    CompanyProfile("Juniper Atlas Bank", 0.47, "regional", "800-1200", "regional bank", "Johannesburg, ZA", "Private", "C# / SQL Server / on-prem", "bench_gap_thin", 0.5, "Head of Transformation"),
    CompanyProfile("Kitebridge Data Rail", 0.74, "growth", "320-480", "data infra vendor", "Toronto, CA", "Series C", "Go / Kubernetes / AWS", "bench_gap_visible", 1.5, "Chief Architect"),
]

PROGRAMMATIC_VARIANTS_PER_PROBE = 2
HAND_AUTHORED_VARIANTS = 36
LLM_SYNTHESIS_VARIANTS_PER_TASK = 4
SPLIT_NAMES = ("train", "dev", "held_out")
SOURCE_MODE_SHARE_TARGETS = {
    "trace-derived": 0.30,
    "programmatic": 0.30,
    "multi-llm-synthesis": 0.25,
    "hand-authored": 0.15,
}
TRACE_ROW_LIMITS = {
    "conflicting_signals": 8,
    "no_hiring_signals": 8,
    "weak_confidence": 7,
}


DIMENSION_NORMALIZATION = {
    "CTO sensitivity": "cto_sensitivity",
    "CTO_sensitivity": "cto_sensitivity",
    "cto_sensitivity": "cto_sensitivity",
    "signal over-claiming": "signal_over_claiming",
    "signal_over-claiming": "signal_over_claiming",
    "signal_over_claiming": "signal_over_claiming",
    "scheduling edge cases EU US Africa": "scheduling_edge_cases_eu_us_africa",
    "scheduling edge cases (EU/US/Africa)": "scheduling_edge_cases_eu_us_africa",
    "scheduling_edge_cases_EU_US_Africa": "scheduling_edge_cases_eu_us_africa",
    "ICP misclassification": "icp_misclassification",
    "ICP_misclassification": "icp_misclassification",
}


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "\n".join(json.dumps(row, ensure_ascii=True) for row in rows)
    path.write_text(payload + ("\n" if payload else ""))


def _load_seed_text(relative_path: str, fallback: str) -> str:
    path = SEED_ROOT / relative_path
    if path.exists():
        return path.read_text()
    return fallback


def _seed_context() -> dict[str, str]:
    return {
        "style_guide_excerpt": _load_seed_text(
            "style_guide.md",
            "Tenacious requires direct, grounded, honest, professional, non-condescending outreach.",
        ),
        "warm_reply_excerpt": _load_seed_text(
            "email_sequences/warm.md",
            "Warm replies should classify intent, answer directly, and book only when warranted.",
        ),
        "pricing_excerpt": _load_seed_text(
            "pricing_sheet.md",
            "Agent may quote only public pricing bands and must route custom pricing to a human.",
        ),
        "cto_transcript_excerpt": _load_seed_text(
            "discovery_transcripts/transcript_03_new_cto_transition.md",
            "New CTO outreach should ask about reassessment and prior bad vendor experiences without sounding presumptuous.",
        ),
        "case_studies_excerpt": _load_seed_text(
            "case_studies.md",
            "Tenacious case studies emphasize grounded outcomes, not inflated talent language.",
        ),
        "bench_summary_excerpt": _load_seed_text(
            "bench_summary.json",
            '{"segments":["cost restructure","leadership transition","specialized capability"]}',
        ),
    }


def _normalize_dimension_name(value: str) -> str:
    collapsed = value.replace("/", "_").replace("(", "").replace(")", "").replace("-", "_")
    collapsed = "_".join(part for part in collapsed.replace(" ", "_").split("_") if part)
    normalized = DIMENSION_NORMALIZATION.get(value, DIMENSION_NORMALIZATION.get(collapsed, collapsed))
    return normalized.lower()


def _task_text(task: dict[str, Any]) -> str:
    parts = [
        task["dimension"],
        task["input"].get("company_name", ""),
        task["input"].get("hiring_signal_brief_excerpt", ""),
        task["input"].get("competitor_gap_brief_excerpt", ""),
        task["input"].get("prior_thread", ""),
    ]
    return " ".join(str(part) for part in parts if part).lower()


def _tokenize(text: str) -> list[str]:
    return [token for token in "".join(char if char.isalnum() else " " for char in text).split() if token]


def _ngrams(tokens: list[str], n: int = 8) -> set[tuple[str, ...]]:
    if len(tokens) < n:
        return set()
    return {tuple(tokens[idx : idx + n]) for idx in range(len(tokens) - n + 1)}


def _shared_ngram_violation(left: dict[str, Any], right: dict[str, Any], n: int = 8) -> bool:
    left_tokens = _tokenize(_task_text(left))
    right_tokens = _tokenize(_task_text(right))
    if len(left_tokens) < n or len(right_tokens) < n:
        return False
    return bool(_ngrams(left_tokens, n) & _ngrams(right_tokens, n))


def _subject_for_confidence(company: str, confidence: float) -> str:
    prefix = "Question:" if confidence < 0.6 else "Context:"
    return f"{prefix} {company} signal check"


def _base_email_ground_truth(
    *,
    required_signal_strings: list[str],
    require_question_mark: bool,
    require_calendar_link: bool = False,
    require_handoff_phrase: str | None = None,
    require_no_dollar_sign: bool = False,
) -> dict[str, Any]:
    return {
        "required_signal_strings": required_signal_strings,
        "banned_phrases": TENACIOUS_BANNED_PHRASES,
        "require_question_mark": require_question_mark,
        "require_calendar_link": require_calendar_link,
        "allowed_subject_prefixes": ALLOWED_SUBJECT_PREFIXES,
        "max_body_words": 120,
        "require_handoff_phrase": require_handoff_phrase,
        "require_no_dollar_sign": require_no_dollar_sign,
    }


def _email_rubric(with_routing_safety: bool = True) -> dict[str, Any]:
    dimensions = [
        {"name": "grounded_language", "weight": 0.25},
        {"name": "confidence_alignment", "weight": 0.25},
        {"name": "tone_safety", "weight": 0.2},
        {"name": "directness_constraints", "weight": 0.15},
    ]
    if with_routing_safety:
        dimensions.append({"name": "routing_safety", "weight": 0.15})
    return {"dimensions": dimensions, "pass_threshold": 0.8}


def _qualification_rubric() -> dict[str, Any]:
    return {
        "dimensions": [
            {"name": "qualification_status_match", "weight": 0.4},
            {"name": "intent_match", "weight": 0.2},
            {"name": "action_match", "weight": 0.4},
        ],
        "pass_threshold": 1.0,
    }


def _channel_rubric() -> dict[str, Any]:
    return {
        "dimensions": [
            {"name": "primary_channel_match", "weight": 0.4},
            {"name": "allowed_channels_match", "weight": 0.6},
        ],
        "pass_threshold": 1.0,
    }


def _trace_email_body(body: str, qualification_status: str) -> str:
    normalized = body.strip()
    if qualification_status == "qualified" and "cal.com" not in normalized.lower():
        normalized = (
            f"{normalized} If useful, here is a booking link for a short discussion: "
            "https://cal.com/tenacious/discovery"
        )
    return normalized


def _family_task(
    *,
    task_id: str,
    family_id: str,
    source_mode: str,
    dimension: str,
    difficulty: str,
    task_type: str,
    input_payload: dict[str, Any],
    candidate_output: dict[str, Any],
    ground_truth: dict[str, Any],
    scoring_rubric: dict[str, Any],
    metadata: dict[str, Any],
) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "source_mode": source_mode,
        "dimension": dimension,
        "difficulty": difficulty,
        "task_type": task_type,
        "input": input_payload,
        "candidate_output": candidate_output,
        "ground_truth": ground_truth,
        "scoring_rubric": scoring_rubric,
        "metadata": {**metadata, "family_id": family_id},
    }


def build_trace_tasks(seed_context: dict[str, str]) -> list[dict[str, Any]]:
    traces = _read_jsonl(TRACE_LOG)
    rows_by_scenario: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in traces:
        scenario_name = row.get("scenario_name")
        if scenario_name:
            rows_by_scenario[scenario_name].append(row)

    tasks: list[dict[str, Any]] = []
    trace_index = 1
    for scenario_name in sorted(rows_by_scenario):
        limit = TRACE_ROW_LIMITS.get(scenario_name, 0)
        for row in rows_by_scenario[scenario_name][:limit]:
            result = row["result"]
            brief = result["hiring_signal_brief"]
            email = result.get("email") or result.get("draft_email")
            qualification = result["qualification"]
            channel_plan = result.get("channel_plan") or {
                "primary_channel": "email",
                "allowed_channels_after_reply": ["sms", "calendar"] if qualification["qualification_status"] == "qualified" else ["email"],
            }
            company = result["company"]
            if isinstance(company, dict):
                company = company.get("company_name") or result.get("input_company") or "Unknown Company"
            confidence_assessment = result.get("confidence_assessment") or {}
            confidence = float(
                confidence_assessment.get("numeric_score")
                or brief.get("overall_confidence")
                or result.get("confidence_score")
                or 0.5
            )
            company_token = company.lower().split()[0]
            normalized_dimension = _normalize_dimension_name(scenario_name)
            trace_ref = row.get("result", {}).get("trace_id") or f"trace-log:{scenario_name}-{trace_index:03d}"
            family_id = f"trace-{normalized_dimension}"

            tasks.append(
                _family_task(
                    task_id=f"tb-trace-email-{trace_index:03d}",
                    family_id=family_id,
                    source_mode="trace-derived",
                    dimension=normalized_dimension,
                    difficulty="medium" if confidence >= 0.55 else "hard",
                    task_type="email_grounding",
                    input_payload={
                        "company_name": company,
                        "signal_confidence": confidence,
                        "hiring_signal_brief_excerpt": brief["summary"],
                        "competitor_gap_brief_excerpt": result["competitor_gap_brief"]["gap_summary"],
                        "prior_thread": "",
                        "bench_context": seed_context["style_guide_excerpt"][:300],
                    },
                    candidate_output={
                        "subject": _subject_for_confidence(company, confidence),
                        "body": _trace_email_body(email["body"], qualification["qualification_status"]),
                    },
                    ground_truth=_base_email_ground_truth(
                        required_signal_strings=[company_token, company_token],
                        require_question_mark=confidence < 0.6,
                        require_calendar_link=qualification["qualification_status"] == "qualified",
                    ),
                    scoring_rubric=_email_rubric(with_routing_safety=False),
                    metadata={
                        "week10_evidence_refs": [trace_ref],
                        "probe_refs": [],
                        "authoring_mode_detail": "trace-derived",
                        "notes": f"Derived from scenario {scenario_name}.",
                    },
                )
            )

            tasks.append(
                _family_task(
                    task_id=f"tb-trace-qual-{trace_index:03d}",
                    family_id=family_id,
                    source_mode="trace-derived",
                    dimension=_normalize_dimension_name(f"{scenario_name}_qualification"),
                    difficulty="easy",
                    task_type="qualification_decision",
                    input_payload={
                        "company_name": company,
                        "signal_confidence": confidence,
                        "prior_thread": result["reply_text"],
                    },
                    candidate_output={
                        "qualification_status": qualification["qualification_status"],
                        "intent_level": qualification["intent_level"],
                        "next_action": qualification["next_action"],
                    },
                    ground_truth={
                        "qualification_status": qualification["qualification_status"],
                        "intent_level": qualification["intent_level"],
                        "next_action": qualification["next_action"],
                    },
                    scoring_rubric=_qualification_rubric(),
                    metadata={
                        "week10_evidence_refs": [trace_ref],
                        "probe_refs": [],
                        "authoring_mode_detail": "trace-derived",
                        "notes": f"Qualification artifact from scenario {scenario_name}.",
                    },
                )
            )

            tasks.append(
                _family_task(
                    task_id=f"tb-trace-channel-{trace_index:03d}",
                    family_id=family_id,
                    source_mode="trace-derived",
                    dimension=_normalize_dimension_name(f"{scenario_name}_channel_plan"),
                    difficulty="medium",
                    task_type="channel_decision",
                    input_payload={
                        "company_name": company,
                        "signal_confidence": confidence,
                        "prior_thread": result["reply_text"],
                        "bench_context": seed_context["warm_reply_excerpt"][:300],
                    },
                    candidate_output=deepcopy(channel_plan),
                    ground_truth={
                        "primary_channel": channel_plan["primary_channel"],
                        "allowed_channels_after_reply": channel_plan["allowed_channels_after_reply"],
                    },
                    scoring_rubric=_channel_rubric(),
                    metadata={
                        "week10_evidence_refs": [trace_ref],
                        "probe_refs": [],
                        "authoring_mode_detail": "trace-derived",
                        "notes": f"Channel plan artifact from scenario {scenario_name}.",
                    },
                )
            )
            trace_index += 1
    return tasks


def _build_programmatic_email_task(
    *,
    probe: dict[str, Any],
    variant_index: int,
    company: CompanyProfile,
    seed_context: dict[str, str],
) -> dict[str, Any]:
    category = probe["category"]
    setup = probe["setup"]
    expected_failure = probe["expected_failure"]
    setup_hint = setup.split(",")[0].strip(". ")
    dimension = _normalize_dimension_name(category)
    family_id = f"programmatic-{dimension}"
    task_id = f"tb-{probe['id'].lower()}-v{variant_index:02d}"
    company_token = company.name.lower().split()[0]

    if category == "CTO sensitivity":
        confidence = 0.57
        body = (
            f"Question: {company.buying_center} transitions are usually reassessment windows, so I do not want to "
            f"assume a buying motion from partial signals alone. With {company.name}, is distributed delivery even "
            "on the reassessment list right now, and what would have needed to be different from prior bad vendor experiences?"
        )
        required = [company_token, "reassessment"]
    elif category == "weak confidence handling":
        confidence = 0.43
        body = (
            f"Question: {setup_hint}. I am not confident enough to make a hard claim from the available public "
            f"signals around {company.name}. Is hiring capacity, AI operations, or compliance delivery a live priority right now?"
        )
        required = [company_token, "priority"]
    elif category == "tone drift":
        confidence = 0.58
        body = (
            f"Question: {setup_hint}. The public signals around {company.name} are mixed, so I do not want to force "
            "a conclusion. Is engineering capacity or AI operations a live issue right now?"
        )
        required = [company_token, "issue"]
    elif category == "outsourcing mismatch":
        confidence = 0.69
        body = (
            f"Question: {setup_hint}. For {company.name}, it looks more like a capability-design decision than a "
            "generic augmentation problem. Is backend execution actually the bottleneck, or is the need closer to team design support?"
        )
        required = [company_token, "bottleneck"]
    elif category == "signal over-claiming":
        confidence = 0.63
        body = (
            f"Question: {setup_hint}. I only see directional public evidence for {company.name}, so I do not want "
            "to overstate urgency. Is hiring velocity or AI operations capacity a real priority this quarter?"
        )
        required = [company_token, "priority"]
    elif category == "ICP misclassification":
        confidence = 0.54
        body = (
            f"Question: {setup_hint}. Before assuming {company.buying_center} owns this problem at {company.name}, "
            "I want to confirm whether the pressure is actually technical capacity rather than an adjacent operations need?"
        )
        required = [company_token, "technical"]
    elif category == "cost issues":
        confidence = 0.62
        body = (
            f"Context: {setup_hint}. For {company.name}, the safe behavior is to stay narrow and avoid unnecessary "
            "regeneration loops when the buying signal is weak."
        )
        required = [company_token, "safe"]
    else:
        confidence = max(0.48, min(company.confidence, 0.78))
        body = (
            f"Question: {setup_hint}. For {company.name}, I want to stay grounded in the supplied brief rather than "
            "jumping to a sales conclusion. Is this the right problem to discuss now?"
        )
        required = [company_token, "problem"]

    input_payload = {
        "company_name": company.name,
        "signal_confidence": confidence,
        "hiring_signal_brief_excerpt": (
            f"{setup} Company size: {company.company_size}. Headcount band: {company.headcount_band}. "
            f"Segment: {company.sector}. Stack: {company.stack}. Locale: {company.location}."
        ),
        "competitor_gap_brief_excerpt": (
            f"{expected_failure} Bench state: {company.bench_state}. AI maturity score: {company.ai_maturity_score}."
        ),
        "prior_thread": "" if variant_index % 2 else f"Thread active for {company.buying_center}.",
        "bench_context": seed_context["style_guide_excerpt"][:300],
    }
    return _family_task(
        task_id=task_id,
        family_id=family_id,
        source_mode="programmatic",
        dimension=dimension,
        difficulty="hard" if probe["observed_trigger_rate"] >= 0.3 else "medium",
        task_type="email_grounding",
        input_payload=input_payload,
        candidate_output={
            "subject": _subject_for_confidence(company.name, confidence),
            "body": body,
        },
        ground_truth=_base_email_ground_truth(
            required_signal_strings=required,
            require_question_mark="?" in body,
            require_no_dollar_sign=category in {
                "signal over-claiming",
                "outsourcing mismatch",
                "CTO sensitivity",
                "cost issues",
            },
        ),
        scoring_rubric=_email_rubric(),
        metadata={
            "week10_evidence_refs": [],
            "probe_refs": [probe["id"]],
            "authoring_mode_detail": f"programmatic_variant_{variant_index}",
            "tenacious_specific": probe.get("tenacious_specific", False),
            "slot_values": {
                "company_size": company.company_size,
                "segment": company.sector,
                "headcount_band": company.headcount_band,
                "stack": company.stack,
                "bench_state": company.bench_state,
                "ai_maturity_score": company.ai_maturity_score,
            },
            "notes": f"Programmatic task derived from probe {probe['id']} variant {variant_index}.",
        },
    )


def _build_programmatic_channel_task(
    *,
    probe: dict[str, Any],
    variant_index: int,
    company: CompanyProfile,
    seed_context: dict[str, str],
) -> dict[str, Any]:
    category = probe["category"]
    setup = probe["setup"]
    expected_failure = probe["expected_failure"]
    dimension = _normalize_dimension_name(category)
    family_id = f"programmatic-{dimension}"
    task_id = f"tb-{probe['id'].lower()}-v{variant_index:02d}"

    if "scheduling edge cases" in category:
        allowed = ["calendar"]
        prior_thread = f"Buyer is in {company.location} and asked for a timezone-safe booking link."
    elif category == "multi-thread leakage":
        allowed = ["email"]
        prior_thread = "Another contact at the same company replied, but this contact did not."
    elif category == "coordination failures":
        allowed = ["sms", "calendar"]
        prior_thread = "A warm reply is on record and the CRM stage should move forward once."
    else:
        allowed = ["email"]
        prior_thread = "Routing should remain conservative until the thread state is explicit."

    return _family_task(
        task_id=task_id,
        family_id=family_id,
        source_mode="programmatic",
        dimension=dimension,
        difficulty="hard" if probe["observed_trigger_rate"] >= 0.3 else "medium",
        task_type="channel_decision",
        input_payload={
            "company_name": company.name,
            "signal_confidence": max(0.45, min(company.confidence, 0.8)),
            "hiring_signal_brief_excerpt": (
                f"{setup} Sector: {company.sector}. Stage: {company.stage}. "
                f"Company size: {company.company_size}. Headcount band: {company.headcount_band}. Stack: {company.stack}."
            ),
            "competitor_gap_brief_excerpt": (
                f"{expected_failure} Bench state: {company.bench_state}. AI maturity score: {company.ai_maturity_score}."
            ),
            "prior_thread": prior_thread,
            "bench_context": seed_context["warm_reply_excerpt"][:300],
        },
        candidate_output={
            "primary_channel": "email",
            "allowed_channels_after_reply": allowed,
        },
        ground_truth={
            "primary_channel": "email",
            "allowed_channels_after_reply": allowed,
        },
        scoring_rubric=_channel_rubric(),
        metadata={
            "week10_evidence_refs": [],
            "probe_refs": [probe["id"]],
            "authoring_mode_detail": f"programmatic_variant_{variant_index}",
            "tenacious_specific": probe.get("tenacious_specific", False),
            "slot_values": {
                "company_size": company.company_size,
                "segment": company.sector,
                "headcount_band": company.headcount_band,
                "stack": company.stack,
                "bench_state": company.bench_state,
                "ai_maturity_score": company.ai_maturity_score,
            },
            "notes": f"Programmatic routing task derived from probe {probe['id']} variant {variant_index}.",
        },
    )


def build_programmatic_tasks(seed_context: dict[str, str]) -> list[dict[str, Any]]:
    probes = json.loads(PROBE_LIBRARY.read_text())
    tasks: list[dict[str, Any]] = []
    for probe in probes:
        for variant_index in range(1, PROGRAMMATIC_VARIANTS_PER_PROBE + 1):
            company = COMPANY_PROFILES[(variant_index - 1 + int(probe["id"].split("-")[1])) % len(COMPANY_PROFILES)]
            category = probe["category"]
            if category in {
                "coordination failures",
                "scheduling edge cases (EU/US/Africa)",
                "multi-thread leakage",
            }:
                tasks.append(
                    _build_programmatic_channel_task(
                        probe=probe,
                        variant_index=variant_index,
                        company=company,
                        seed_context=seed_context,
                    )
                )
            else:
                tasks.append(
                    _build_programmatic_email_task(
                        probe=probe,
                        variant_index=variant_index,
                        company=company,
                        seed_context=seed_context,
                    )
                )
    return tasks


def build_hand_authored_tasks(seed_context: dict[str, str]) -> list[dict[str, Any]]:
    templates = [
        {
            "family_id": "hand-pricing-handoff",
            "dimension": "pricing_handoff",
            "body": (
                "Fair question. We can quote the public monthly bands, but a specific multi-quarter total would need a "
                "short scoping conversation with our delivery lead so we do not invent a number. Our delivery lead will follow up within 24 hours."
            ),
            "required": ["question"],
            "require_handoff_phrase": "our delivery lead will follow up within 24 hours",
        },
        {
            "family_id": "hand-soft-defer",
            "dimension": "soft_defer_graceful_close",
            "body": (
                "Understood. Timing matters, and I do not want to crowd the thread. I will reach out again with fresh sector research at the start of the next planning window."
            ),
            "required": ["understood"],
            "require_handoff_phrase": None,
        },
        {
            "family_id": "hand-employment-model",
            "dimension": "warm_reply_grounded_answer",
            "body": (
                "Good question. Our engineers are full-time Tenacious employees and work inside your delivery cadence rather than through a translation layer. We carry payroll, benefits, and insurance while your team directs the work."
            ),
            "required": ["question"],
            "require_handoff_phrase": None,
        },
        {
            "family_id": "hand-cto-transition",
            "dimension": "new_cto_transition",
            "body": (
                "Question: In the first 90 days after a CTO transition, vendor mix often gets a fresh look. For this thread, is distributed delivery even on the reassessment list, and what would have needed to be different from prior bad vendor experiences?"
            ),
            "required": ["reassessment"],
            "require_handoff_phrase": None,
        },
        {
            "family_id": "hand-bench-to-brief",
            "dimension": "bench_to_brief_match",
            "body": (
                "Context: I do not want to force a benchmark story where the brief is thin. The only useful next step would be to check whether hiring velocity, delivery pressure, or AI operations is the real constraint."
            ),
            "required": ["useful"],
            "require_handoff_phrase": None,
        },
        {
            "family_id": "hand-defensive-reply",
            "dimension": "defensive_reply_recovery",
            "body": (
                "Understood. I may be reading too much into the public signal, so I do not want to press the point. If I re-engage later, I will do it only with a cleaner reason tied to your actual roadmap."
            ),
            "required": ["understood"],
            "require_handoff_phrase": None,
        },
    ]

    tasks: list[dict[str, Any]] = []
    for index in range(HAND_AUTHORED_VARIANTS):
        template = templates[index % len(templates)]
        company = COMPANY_PROFILES[index % len(COMPANY_PROFILES)]
        prior_thread = [
            "Prospect asks for specific long-range pricing.",
            "Prospect says: ask me again next quarter.",
            "Prospect asks whether engineers are employees or contractors.",
            "New CTO joined 65 days ago.",
            "Brief confidence is mixed and benchmark pressure is unclear.",
            "Prospect says the last vendor burned them.",
        ][index % 6]
        task_id = f"tb-hand-{index + 1:03d}"
        tasks.append(
            _family_task(
                task_id=task_id,
                family_id=template["family_id"],
                source_mode="hand-authored",
                dimension=_normalize_dimension_name(template["dimension"]),
                difficulty="hard",
                task_type="email_grounding",
                input_payload={
                    "company_name": company.name,
                    "signal_confidence": company.confidence,
                    "hiring_signal_brief_excerpt": prior_thread,
                    "competitor_gap_brief_excerpt": f"{template['dimension']} constraint for {company.name}.",
                    "prior_thread": prior_thread,
                    "bench_context": seed_context["case_studies_excerpt"][:260],
                },
                candidate_output={
                    "subject": _subject_for_confidence(company.name, company.confidence),
                    "body": template["body"],
                },
                ground_truth=_base_email_ground_truth(
                    required_signal_strings=template["required"],
                    require_question_mark="?" in template["body"],
                    require_handoff_phrase=template["require_handoff_phrase"],
                    require_no_dollar_sign=True,
                ),
                scoring_rubric=_email_rubric(),
                metadata={
                    "week10_evidence_refs": [],
                    "probe_refs": ["P-036"] if template["dimension"] == "new_cto_transition" else [],
                    "authoring_mode_detail": "hand-authored",
                    "notes": f"Hand-authored Tenacious-specific task {template['dimension']}.",
                },
            )
        )
    return tasks


def build_multi_llm_synthesis_tasks(seed_context: dict[str, str]) -> list[dict[str, Any]]:
    if not SYNTHESIS_CACHE.exists():
        return []
    payload = json.loads(SYNTHESIS_CACHE.read_text())
    tasks: list[dict[str, Any]] = []
    variant_suffixes = [
        "If helpful, I can keep the next step to one short benchmark note.",
        "If this is not active, I can close the loop and revisit when the signal is clearer.",
        "If useful, I can route one bounded follow-up to our delivery lead.",
        "If timing is wrong, I can hold this until the next planning window.",
    ]
    for row in payload.get("tasks", []):
        for variant_index in range(1, LLM_SYNTHESIS_VARIANTS_PER_TASK + 1):
            task_type = row["task_type"]
            candidate_output = deepcopy(row["candidate_output"])
            if task_type == "email_grounding":
                body = str(candidate_output.get("body", ""))
                if "[Calendar Link]" in body:
                    body = body.replace("[Calendar Link]", "calendar link: https://cal.com/tenacious/discovery")
                require_handoff_phrase = row["ground_truth"].get("require_handoff_phrase")
                if require_handoff_phrase is True:
                    require_handoff_phrase = "our delivery lead will follow up within 24 hours"
                if require_handoff_phrase and str(require_handoff_phrase).lower() not in body.lower():
                    body = f"{body}\n\nOur delivery lead will follow up within 24 hours."
                if row["ground_truth"].get("require_calendar_link") and "cal.com" not in body.lower():
                    body = f"{body}\n\nBook here: https://cal.com/tenacious/discovery"
                suffix = variant_suffixes[(variant_index - 1) % len(variant_suffixes)]
                if suffix.lower() not in body.lower():
                    body = f"{body}\n\n{suffix}"
                candidate_output["body"] = body
            else:
                require_handoff_phrase = row["ground_truth"].get("require_handoff_phrase")

            if task_type == "channel_decision":
                rubric = _channel_rubric()
                ground_truth = {
                    "primary_channel": candidate_output["primary_channel"],
                    "allowed_channels_after_reply": candidate_output["allowed_channels_after_reply"],
                }
            elif task_type == "qualification_decision":
                rubric = _qualification_rubric()
                ground_truth = deepcopy(candidate_output)
            else:
                rubric = _email_rubric()
                ground_truth = _base_email_ground_truth(
                    required_signal_strings=row["ground_truth"]["required_signal_strings"],
                    require_question_mark=row["ground_truth"]["require_question_mark"],
                    require_calendar_link=row["ground_truth"].get("require_calendar_link", False),
                    require_handoff_phrase=require_handoff_phrase,
                    require_no_dollar_sign=row["ground_truth"].get("require_no_dollar_sign", False),
                )

            tasks.append(
                _family_task(
                    task_id=f"{row['task_id']}-v{variant_index:02d}",
                    family_id=row["family_id"],
                    source_mode="multi-llm-synthesis",
                    dimension=_normalize_dimension_name(row["dimension"]),
                    difficulty=row["difficulty"],
                    task_type=task_type,
                    input_payload={
                        **row["input"],
                        "bench_context": row["input"].get("bench_context") or seed_context["style_guide_excerpt"][:300],
                        "prior_thread": row["input"].get("prior_thread") or f"Synthesis variant {variant_index} for calibration coverage.",
                    },
                    candidate_output=candidate_output,
                    ground_truth=ground_truth,
                    scoring_rubric=rubric,
                    metadata={
                        "week10_evidence_refs": row.get("metadata", {}).get("week10_evidence_refs", []),
                        "probe_refs": row.get("metadata", {}).get("probe_refs", []),
                        "authoring_mode_detail": f"multi-llm-synthesis_variant_{variant_index}",
                        "generator_model": row.get("metadata", {}).get("generator_model"),
                        "judge_model": row.get("metadata", {}).get("judge_model"),
                        "judge_scores": row.get("metadata", {}).get("judge_scores"),
                        "notes": row.get("metadata", {}).get("notes", "LLM-synthesized task."),
                    },
                )
            )
    return tasks


def assign_splits(tasks: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    total_tasks = len(tasks)
    target_split_counts = {
        "train": round(total_tasks * 0.5),
        "dev": round(total_tasks * 0.3),
        "held_out": total_tasks - round(total_tasks * 0.5) - round(total_tasks * 0.3),
    }
    families: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for task in tasks:
        families[task["metadata"]["family_id"]].append(task)

    assigned: dict[str, list[dict[str, Any]]] = {"train": [], "dev": [], "held_out": []}
    current_counts = {"train": 0, "dev": 0, "held_out": 0}
    source_counts: dict[str, dict[str, int]] = defaultdict(lambda: {"train": 0, "dev": 0, "held_out": 0})
    source_totals = Counter(task["source_mode"] for task in tasks)
    source_targets = {
        source_mode: {
            "train": round(source_total * 0.5),
            "dev": round(source_total * 0.3),
            "held_out": source_total - round(source_total * 0.5) - round(source_total * 0.3),
        }
        for source_mode, source_total in source_totals.items()
    }

    def split_score(source_mode: str, split: str, family_size: int) -> tuple[float, float, float, int]:
        source_target = max(source_targets[source_mode][split], 1)
        split_target = max(target_split_counts[split], 1)
        source_projected = source_counts[source_mode][split] + family_size
        split_projected = current_counts[split] + family_size
        source_overflow = max(0, source_projected - source_target)
        split_overflow = max(0, split_projected - split_target)
        source_fill_ratio = source_counts[source_mode][split] / source_target
        return (source_overflow, split_overflow, source_fill_ratio, current_counts[split])

    for family_id, family_tasks in sorted(
        families.items(),
        key=lambda item: (
            item[1][0]["source_mode"],
            item[1][0]["dimension"],
            item[0],
        ),
    ):
        source_mode = family_tasks[0]["source_mode"]
        family_size = len(family_tasks)
        split = min(SPLIT_NAMES, key=lambda name: split_score(source_mode, name, family_size))
        for task in family_tasks:
            task["split"] = split
            assigned[split].append(task)
        current_counts[split] += len(family_tasks)
        source_counts[source_mode][split] += len(family_tasks)

    for split, rows in assigned.items():
        rows.sort(key=lambda item: item["task_id"])
    return _repair_held_out_overlap(assigned, target_split_counts)


def _repair_held_out_overlap(
    assigned: dict[str, list[dict[str, Any]]],
    target_split_counts: dict[str, int],
) -> dict[str, list[dict[str, Any]]]:
    families: dict[str, list[dict[str, Any]]] = defaultdict(list)
    family_split: dict[str, str] = {}
    for split, rows in assigned.items():
        for row in rows:
            family_id = row["metadata"]["family_id"]
            families[family_id].append(row)
            family_split[family_id] = split

    def split_rows(split: str) -> list[dict[str, Any]]:
        return [row for family_id, rows in families.items() if family_split[family_id] == split for row in rows]

    def family_overlaps_reference(family_id: str, reference_rows: list[dict[str, Any]]) -> bool:
        return any(
            _shared_ngram_violation(candidate, reference)
            for candidate in families[family_id]
            for reference in reference_rows
        )

    changed = True
    while changed:
        changed = False
        train_rows = split_rows("train")
        dev_rows = split_rows("dev")
        held_families = [family_id for family_id, split in family_split.items() if split == "held_out"]
        for family_id in held_families:
            if family_overlaps_reference(family_id, train_rows) or family_overlaps_reference(family_id, dev_rows):
                target = "dev" if len(dev_rows) < len(train_rows) else "train"
                family_split[family_id] = target
                changed = True

    # Greedy refill: move safe non-heldout families into held_out until we are close to the target count.
    while len(split_rows("held_out")) < target_split_counts["held_out"]:
        train_rows = split_rows("train")
        dev_rows = split_rows("dev")
        candidate_family = None
        candidate_gap = math.inf
        for family_id, split in family_split.items():
            if split == "held_out":
                continue
            reference_rows = train_rows + dev_rows
            reference_rows = [row for row in reference_rows if row["metadata"]["family_id"] != family_id]
            if family_overlaps_reference(family_id, reference_rows):
                continue
            held_out_after = len(split_rows("held_out")) + len(families[family_id])
            gap = abs(target_split_counts["held_out"] - held_out_after)
            if gap < candidate_gap:
                candidate_family = family_id
                candidate_gap = gap
        if candidate_family is None:
            break
        family_split[candidate_family] = "held_out"

    repaired = {"train": [], "dev": [], "held_out": []}
    for family_id, rows in families.items():
        repaired[family_split[family_id]].extend(rows)
    for split, rows in repaired.items():
        rows.sort(key=lambda item: item["task_id"])
    return repaired


def summarize(partitions: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    summary: dict[str, Any] = {"total_tasks": 0, "splits": {}, "source_modes": {}, "task_types": {}}
    for split, tasks in partitions.items():
        summary["total_tasks"] += len(tasks)
        summary["splits"][split] = len(tasks)
        for task in tasks:
            summary["source_modes"][task["source_mode"]] = summary["source_modes"].get(task["source_mode"], 0) + 1
            summary["task_types"][task["task_type"]] = summary["task_types"].get(task["task_type"], 0) + 1
    return summary


def main() -> None:
    seed_context = _seed_context()
    tasks = (
        build_trace_tasks(seed_context)
        + build_programmatic_tasks(seed_context)
        + build_hand_authored_tasks(seed_context)
        + build_multi_llm_synthesis_tasks(seed_context)
    )
    partitions = assign_splits(tasks)
    for split, rows in partitions.items():
        materialized_rows = []
        for row in rows:
            row = deepcopy(row)
            row["metadata"].pop("family_id", None)
            materialized_rows.append(row)
        _write_jsonl(BENCH_ROOT / split / "tasks.jsonl", materialized_rows)
    summary = summarize(partitions)
    (BENCH_ROOT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
