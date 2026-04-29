from __future__ import annotations

import json
from collections import defaultdict
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
    sector: str
    location: str
    stage: str
    buying_center: str


COMPANY_PROFILES = [
    CompanyProfile("Northstar Lending", 0.72, "fintech lender", "Austin, TX", "Series B", "VP Engineering"),
    CompanyProfile("Quiet Current Bank", 0.42, "regulated bank", "Nashville, TN", "Series A", "Head of Platform"),
    CompanyProfile("Harborline Ledger", 0.57, "payments ledger platform", "Seattle, WA", "Seed", "New CTO"),
    CompanyProfile("Beacon Ridge Payments", 0.81, "payments processor", "Chicago, IL", "Series C", "Director of AI Operations"),
    CompanyProfile("Elm Street Treasury", 0.68, "treasury ops SaaS", "New York, NY", "Series B", "VP Risk Engineering"),
    CompanyProfile("Delta Pine Credit", 0.76, "credit infra company", "Atlanta, GA", "Growth", "CTO"),
    CompanyProfile("Apex Harbor Finance", 0.79, "enterprise finance platform", "London, UK", "Growth", "Head of Platform"),
    CompanyProfile("Cinder Vault Capital", 0.51, "capital markets tooling", "Berlin, DE", "Series A", "VP Engineering"),
    CompanyProfile("Marula Core Systems", 0.61, "East Africa core banking vendor", "Nairobi, KE", "Series B", "COO"),
    CompanyProfile("Sable River Underwriting", 0.55, "insurtech workflow platform", "Dublin, IE", "Series A", "VP Engineering"),
    CompanyProfile("Juniper Atlas Bank", 0.47, "regional bank", "Johannesburg, ZA", "Private", "Head of Transformation"),
    CompanyProfile("Kitebridge Data Rail", 0.74, "data infra vendor", "Toronto, CA", "Series C", "Chief Architect"),
]

PROGRAMMATIC_VARIANTS_PER_PROBE = 5
HAND_AUTHORED_VARIANTS = 24


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
    unique_by_scenario: dict[str, dict[str, Any]] = {}
    for row in traces:
        scenario_name = row.get("scenario_name")
        if scenario_name and scenario_name not in unique_by_scenario:
            unique_by_scenario[scenario_name] = row

    tasks: list[dict[str, Any]] = []
    for index, (scenario_name, row) in enumerate(sorted(unique_by_scenario.items()), start=1):
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
        trace_ref = row.get("result", {}).get("trace_id") or f"trace-log:{scenario_name}"
        family_id = f"trace-{scenario_name}"
        company_token = company.lower().split()[0]

        tasks.append(
            _family_task(
                task_id=f"tb-trace-email-{index:03d}",
                family_id=family_id,
                source_mode="trace-derived",
                dimension=scenario_name,
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
                task_id=f"tb-trace-qual-{index:03d}",
                family_id=family_id,
                source_mode="trace-derived",
                dimension=f"{scenario_name}_qualification",
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
                task_id=f"tb-trace-channel-{index:03d}",
                family_id=family_id,
                source_mode="trace-derived",
                dimension=f"{scenario_name}_channel_plan",
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
    family_id = f"probe-{probe['id']}"
    dimension = category.replace(" ", "_").replace("(", "").replace(")", "").replace("/", "_")
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
        "hiring_signal_brief_excerpt": f"{setup} Location context: {company.location}. Segment context: {company.sector}.",
        "competitor_gap_brief_excerpt": expected_failure,
        "prior_thread": "" if variant_index % 2 else f"{company.buying_center} is reviewing the team plan this quarter.",
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
    family_id = f"probe-{probe['id']}"
    dimension = category.replace(" ", "_").replace("(", "").replace(")", "").replace("/", "_")
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
            "hiring_signal_brief_excerpt": f"{setup} Segment: {company.sector}. Stage: {company.stage}.",
            "competitor_gap_brief_excerpt": expected_failure,
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
                dimension=template["dimension"],
                difficulty="hard",
                task_type="email_grounding",
                input_payload={
                    "company_name": company.name,
                    "signal_confidence": company.confidence,
                    "hiring_signal_brief_excerpt": prior_thread,
                    "competitor_gap_brief_excerpt": f"{company.name} should receive a direct, bounded answer grounded in the local brief.",
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
    for row in payload.get("tasks", []):
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
                task_id=row["task_id"],
                family_id=row["family_id"],
                source_mode="multi-llm-synthesis",
                dimension=row["dimension"],
                difficulty=row["difficulty"],
                task_type=task_type,
                input_payload={
                    **row["input"],
                    "bench_context": row["input"].get("bench_context") or seed_context["style_guide_excerpt"][:300],
                },
                candidate_output=candidate_output,
                ground_truth=ground_truth,
                scoring_rubric=rubric,
                metadata={
                    "week10_evidence_refs": row.get("metadata", {}).get("week10_evidence_refs", []),
                    "probe_refs": row.get("metadata", {}).get("probe_refs", []),
                    "authoring_mode_detail": "multi-llm-synthesis",
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

    def split_score(split: str, family_size: int) -> tuple[float, float, int]:
        target = max(target_split_counts[split], 1)
        projected = current_counts[split] + family_size
        overflow = max(0, projected - target)
        fill_ratio = current_counts[split] / target
        return (overflow, fill_ratio, current_counts[split])

    held_out_source_modes = {"trace-derived", "hand-authored", "multi-llm-synthesis"}
    for family_id, family_tasks in sorted(
        families.items(),
        key=lambda item: (
            0 if item[1][0]["source_mode"] in held_out_source_modes else 1,
            -len(item[1]),
            item[0],
        ),
    ):
        source_mode = family_tasks[0]["source_mode"]
        family_size = len(family_tasks)
        if source_mode in held_out_source_modes and current_counts["held_out"] + family_size <= target_split_counts["held_out"]:
            split = "held_out"
        elif source_mode == "programmatic":
            split = min(("train", "dev"), key=lambda name: split_score(name, family_size))
        elif current_counts["train"] + family_size <= target_split_counts["train"]:
            split = "train"
        else:
            split = min(("dev", "train"), key=lambda name: split_score(name, family_size))
        for task in family_tasks:
            task["split"] = split
            assigned[split].append(task)
        current_counts[split] += len(family_tasks)

    for split, rows in assigned.items():
        rows.sort(key=lambda item: item["task_id"])
    return assigned


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
