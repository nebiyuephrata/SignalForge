from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


class LifecycleStage(str, Enum):
    NEW = "NEW"
    EMAILED = "EMAILED"
    REPLIED = "REPLIED"
    QUALIFIED = "QUALIFIED"
    BOOKED = "BOOKED"
    CLOSED = "CLOSED"


class SourceAttribution(BaseModel):
    source: str
    status: Literal["success", "no_data", "skipped", "fallback", "error"]
    fetched_at: str = Field(default_factory=utc_now_iso)
    source_url: str | None = None
    public_only: bool = True
    respects_robots_txt: bool = True
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    detail: str = ""
    fallback_todo: str | None = None


class WeightedJustification(BaseModel):
    signal: Literal[
        "ai_adjacent_open_roles",
        "named_ai_ml_leadership",
        "github_org_activity",
        "executive_commentary",
        "modern_data_ml_stack",
        "strategic_communications",
    ]
    status: str
    weight: Literal["high", "medium", "low"]
    confidence: Literal["high", "medium", "low"]
    source_url: str | None = None


class AIMaturitySignalInput(BaseModel):
    signal: Literal[
        "ai_adjacent_open_roles",
        "named_ai_ml_leadership",
        "github_org_activity",
        "executive_commentary",
        "modern_data_ml_stack",
        "strategic_communications",
    ]
    weight: Literal["high", "medium", "low"]
    points_awarded: int = Field(ge=0)
    detected: bool
    raw_value: str
    confidence: Literal["high", "medium", "low"]
    source_url: str | None = None
    justification: str


class AIMaturitySignalInputs(BaseModel):
    ai_adjacent_open_roles: AIMaturitySignalInput
    named_ai_ml_leadership: AIMaturitySignalInput
    github_org_activity: AIMaturitySignalInput
    executive_commentary: AIMaturitySignalInput
    modern_data_ml_stack: AIMaturitySignalInput
    strategic_communications: AIMaturitySignalInput

    def ordered(self) -> list[AIMaturitySignalInput]:
        return [
            self.ai_adjacent_open_roles,
            self.named_ai_ml_leadership,
            self.github_org_activity,
            self.executive_commentary,
            self.modern_data_ml_stack,
            self.strategic_communications,
        ]


class AIMaturityAssessment(BaseModel):
    score: int = Field(ge=0, le=3)
    confidence: float = Field(ge=0.0, le=1.0)
    weighted_points: int = Field(ge=0)
    max_points: int = Field(ge=1)
    justifications: list[WeightedJustification] = Field(default_factory=list)
    explanation: str


class HiringVelocity(BaseModel):
    open_roles_today: int = Field(ge=0)
    open_roles_60_days_ago: int = Field(ge=0)
    delta: int
    velocity_label: Literal[
        "tripled_or_more",
        "doubled",
        "increased_modestly",
        "flat",
        "declined",
        "insufficient_signal",
    ]
    signal_confidence: float = Field(ge=0.0, le=1.0)
    sources: list[str] = Field(default_factory=list)
    role_titles: list[str] = Field(default_factory=list)


class FundingEvent(BaseModel):
    detected: bool
    stage: Literal["seed", "series_a", "series_b", "series_c", "series_d_plus", "debt", "other", "none"]
    amount_usd: int | None = None
    closed_at: str | None = None
    days_since_event: int | None = None
    source_url: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)


class LayoffEvent(BaseModel):
    detected: bool
    date: str | None = None
    headcount_reduction: int = Field(ge=0, default=0)
    percentage_cut: float | None = None
    source_url: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)


class LeadershipChangeEvent(BaseModel):
    detected: bool
    role: Literal["cto", "vp_engineering", "cio", "chief_data_officer", "head_of_ai", "other", "none"]
    new_leader_name: str | None = None
    started_at: str | None = None
    source_url: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)


class BuyingWindowSignals(BaseModel):
    funding_event: FundingEvent
    layoff_event: LayoffEvent
    leadership_change: LeadershipChangeEvent


class BenchToBriefMatch(BaseModel):
    required_stacks: list[str] = Field(default_factory=list)
    bench_available: bool = False
    gaps: list[str] = Field(default_factory=list)


class EvidenceSignal(BaseModel):
    signal: str
    value: Any
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)


class HiringSignalBrief(BaseModel):
    company_name: str
    prospect_domain: str
    prospect_name: str
    generated_at: str = Field(default_factory=utc_now_iso)
    as_of_date: str
    summary: str
    primary_segment_match: Literal[
        "segment_1_series_a_b",
        "segment_2_mid_market_restructure",
        "segment_3_leadership_transition",
        "segment_4_specialized_capability",
        "abstain",
    ]
    segment_confidence: float = Field(ge=0.0, le=1.0)
    ai_maturity: AIMaturityAssessment
    hiring_velocity: HiringVelocity
    buying_window_signals: BuyingWindowSignals
    tech_stack: list[str] = Field(default_factory=list)
    bench_to_brief_match: BenchToBriefMatch
    data_sources_checked: list[SourceAttribution] = Field(default_factory=list)
    signals: list[EvidenceSignal] = Field(default_factory=list)
    overall_confidence: float = Field(ge=0.0, le=1.0)
    uncertainty_flags: list[str] = Field(default_factory=list)
    source_artifact: dict[str, Any] = Field(default_factory=dict)


class CompetitorEvidence(BaseModel):
    competitor_name: str
    evidence: str
    source_url: str


class CompetitorEntry(BaseModel):
    name: str
    domain: str
    ai_maturity_score: int = Field(ge=0, le=3)
    ai_maturity_justification: list[str] = Field(default_factory=list)
    headcount_band: Literal["15_to_80", "80_to_200", "200_to_500", "500_to_2000", "2000_plus"]
    top_quartile: bool = False
    sources_checked: list[str] = Field(default_factory=list)
    named_signals: list[str] = Field(default_factory=list)


class GapFinding(BaseModel):
    practice: str
    peer_evidence: list[CompetitorEvidence] = Field(default_factory=list)
    prospect_state: str
    confidence: Literal["high", "medium", "low"]
    segment_relevance: list[str] = Field(default_factory=list)


class DistributionPosition(BaseModel):
    prospect_rank: int = Field(ge=1)
    total_companies: int = Field(ge=1)
    percentile: float = Field(ge=0.0, le=1.0)
    label: Literal["top_quartile", "upper_mid", "lower_mid", "bottom_quartile"]


class CompetitorGapBrief(BaseModel):
    prospect_domain: str
    prospect_sector: str
    prospect_sub_niche: str
    generated_at: str = Field(default_factory=utc_now_iso)
    prospect_ai_maturity_score: int = Field(ge=0, le=3)
    sector_top_quartile_benchmark: float = Field(ge=0.0, le=3.0)
    competitors_analyzed: list[CompetitorEntry] = Field(default_factory=list)
    distribution_position: DistributionPosition
    gap_findings: list[GapFinding] = Field(default_factory=list)
    suggested_pitch_shift: str
    gap_quality_self_check: dict[str, bool]
    confidence: float = Field(ge=0.0, le=1.0)
    sparse_sector: bool = False
    gap_summary: str
    peer_average_ai_maturity: float = Field(ge=0.0, le=3.0)
    target_ai_maturity: int = Field(ge=0, le=3)


class ConfidenceBehavior(BaseModel):
    tone: Literal["exploratory", "directional", "assertive"]
    max_claims: int = Field(ge=1)
    allow_booking_link: bool = False
    allow_sms: bool = False
    require_question_led_copy: bool = False
    require_post_generation_validation: bool = True


class ChannelPlan(BaseModel):
    primary_channel: Literal["email"]
    sms_gate: str
    whatsapp_gate: str
    voice_gate: str
    allowed_channels_after_reply: list[str] = Field(default_factory=list)


class GeneratedEmailArtifact(BaseModel):
    subject: str
    body: str


class WebsiteVisitEvent(BaseModel):
    company_name: str
    page_visited: str
    timestamp: str
    contact_email: str | None = None
    session_id: str | None = None
    source: str = "website"


class WebsiteBehaviorSignal(BaseModel):
    visit_count: int = Field(ge=0)
    recent_pages: list[str] = Field(default_factory=list)
    last_visit_at: str | None = None
    follow_up_recommended: bool = False
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)


class LinkedInSignalArtifact(BaseModel):
    hiring_posts: list[str] = Field(default_factory=list)
    leadership_changes: list[str] = Field(default_factory=list)
    company_activity_signals: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    source_attribution: SourceAttribution


class ConfidenceAssessment(BaseModel):
    numeric_score: float = Field(ge=0.0, le=1.0)
    level: Literal["low", "medium", "high"]
    thresholds: dict[str, float]
    behavior: ConfidenceBehavior
    rationale: list[str] = Field(default_factory=list)
    uncertainty_flags: list[str] = Field(default_factory=list)


class LifecycleActivity(BaseModel):
    channel: Literal["email", "sms", "voice", "calendar", "system", "website", "whatsapp"]
    direction: Literal["outbound", "inbound", "system"]
    event_type: str
    detail: str
    provider: str | None = None
    external_id: str | None = None
    recorded_at: str = Field(default_factory=utc_now_iso)


class LeadLifecycleState(BaseModel):
    lead_key: str
    company_name: str
    contact_email: str | None = None
    phone_number: str | None = None
    stage: LifecycleStage = LifecycleStage.NEW
    qualification_status: str = "unknown"
    intent_level: str = "low"
    next_action: str = "research"
    booking_url: str | None = None
    crm_contact_id: str | None = None
    confidence_score: float = Field(ge=0.0, le=1.0, default=0.0)
    email_reply_received: bool = False
    sms_reply_received: bool = False
    booking_completed: bool = False
    website_visits_count: int = Field(ge=0, default=0)
    last_website_page: str | None = None
    last_website_visit_at: str | None = None
    activities: list[LifecycleActivity] = Field(default_factory=list)
    last_inbound_message: str | None = None
    updated_at: str = Field(default_factory=utc_now_iso)

    @property
    def sms_allowed(self) -> bool:
        return self.email_reply_received and self.confidence_score >= 0.6

    @property
    def whatsapp_allowed(self) -> bool:
        return self.email_reply_received and self.confidence_score >= 0.6

    @property
    def booking_ready(self) -> bool:
        return self.stage in {LifecycleStage.QUALIFIED, LifecycleStage.REPLIED} and self.confidence_score >= 0.6
