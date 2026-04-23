from typing import Any, Literal

from pydantic import BaseModel, Field


class EvidenceSignal(BaseModel):
    signal: str
    value: Any
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)


class LeadRecord(BaseModel):
    company_name: str
    domain: str | None = None
    employee_count: int | None = None
    industry: str | None = None
    location: str | None = None


class BriefSection(BaseModel):
    summary: str
    signals: list[EvidenceSignal] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)


class LeadBrief(BaseModel):
    lead: LeadRecord
    hiring: BriefSection
    compliance: BriefSection
    ai_maturity: BriefSection
    competitor_gap: BriefSection


class CRMFields(BaseModel):
    icp_segment: str
    signal_confidence: float = Field(ge=0.0, le=1.0)
    ai_maturity: int = Field(ge=0, le=3)
    intent_level: Literal["low", "medium", "high"]
    qualification_status: str
    next_action: str


class OutboundMessage(BaseModel):
    channel: Literal["email", "sms", "voice"]
    body: str
    crm_fields: CRMFields
