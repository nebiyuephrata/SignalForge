from __future__ import annotations

from pydantic import BaseModel, Field


class RunProspectRequest(BaseModel):
    company_name: str | None = Field(default=None)
    reply_text: str | None = Field(default=None)
    scenario_name: str | None = Field(default=None)


class AvailableScenariosResponse(BaseModel):
    scenarios: list[str]


class BatchScenarioResult(BaseModel):
    scenario_name: str
    company_name: str
    passed: bool
    qualification_status: str
    booking_should_book: bool
    signal_confidence: float


class BatchRunResponse(BaseModel):
    total_cases: int
    passed_cases: int
    failed_cases: int
    scenarios: list[BatchScenarioResult]


class ProspectEmail(BaseModel):
    subject: str
    body: str


class ProspectRunResponse(BaseModel):
    as_of_date: str | None = None
    company: str
    company_profile: dict[str, object] | None = None
    hiring_signal_brief: dict[str, object]
    competitor_gap_brief: dict[str, object]
    email: ProspectEmail
    confidence: str
    trace_id: str
    trace_url: str | None = None
    claim_validation: dict[str, object] | None = None
    reply_text: str | None = None
    qualification: dict[str, object]
    booking: dict[str, object]
