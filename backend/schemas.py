from __future__ import annotations

from typing import Any

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
    confidence_assessment: dict[str, object] | None = None
    trace_id: str
    trace_url: str | None = None
    claim_validation: dict[str, object] | None = None
    reply_text: str | None = None
    qualification: dict[str, object]
    booking: dict[str, object]
    channel_plan: dict[str, object] | None = None


class ProspectDemoFlowResponse(BaseModel):
    session_id: str
    session_started_at: str
    prospect_identity: dict[str, object]
    qualification: dict[str, object]
    email_send: dict[str, object]
    reply_event: dict[str, object]
    sms_follow_up: dict[str, object]
    lifecycle: dict[str, object]
    hubspot_record: dict[str, object]
    calcom_booking: dict[str, object]
    crm_sync: dict[str, object]


class DraftChannelRequest(BaseModel):
    lead: dict[str, Any]


class SendEmailRequest(BaseModel):
    company_name: str
    contact_email: str
    contact_name: str | None = None
    phone_number: str | None = None
    subject: str | None = None
    body: str | None = None
    reply_text: str | None = None
    sync_to_crm: bool = True


class SendWarmSmsRequest(BaseModel):
    company_name: str
    phone_number: str
    contact_email: str | None = None
    body: str
    prior_email_reply: bool = False


class ProviderSendResponse(BaseModel):
    channel: str
    provider: str
    status: str
    destination: str
    external_id: str | None = None
    detail: str = ""
    error_code: str | None = None
    raw_response: dict[str, Any] = Field(default_factory=dict)
    crm_sync: dict[str, Any] | None = None


class WebhookResponse(BaseModel):
    status: str
    provider: str
    channel: str
    event_type: str
    routed_handlers: int = 0
    detail: str = ""
    event: dict[str, Any] | None = None


class BookingWebhookRequest(BaseModel):
    company_name: str
    contact_email: str
    booking_id: str
    booking_url: str
    meeting_start: str
