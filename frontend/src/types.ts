export type Confidence = "low" | "medium" | "high";

export interface ScenarioListResponse {
  scenarios: string[];
}

export interface BatchScenarioResult {
  scenario_name: string;
  company_name: string;
  passed: boolean;
  qualification_status: string;
  booking_should_book: boolean;
  signal_confidence: number;
}

export interface BatchRunResponse {
  total_cases: number;
  passed_cases: number;
  failed_cases: number;
  scenarios: BatchScenarioResult[];
}

export interface ProspectRunResponse {
  as_of_date?: string;
  company: string;
  company_profile?: {
    company_name: string;
    domain: string;
    employee_count: number;
    industry: string;
    location: string;
    last_funding_round: string;
    funding_date: string;
    open_roles_current: number;
    open_roles_60_days_ago: number;
    ai_roles_open: number;
    ai_practices: string[];
  };
  hiring_signal_brief: {
    company_name: string;
    as_of_date: string;
    summary: string;
    signals: Array<{
      signal: string;
      value: Record<string, unknown> | Array<Record<string, unknown>>;
      confidence: number;
      evidence: string[];
    }>;
    ai_maturity_score: {
      signal: string;
      value: number;
      confidence: number;
      justification: string[];
    };
    overall_confidence: number;
    source_artifact?: Record<
      string,
      {
        confidence: number;
        evidence?: string[];
        value?: Record<string, unknown>;
      }
    >;
  };
  competitor_gap_brief: {
    company_name: string;
    gap_summary: string;
    top_quartile_practices: string[];
    confidence: number;
    target_ai_maturity: number;
    peer_average_ai_maturity: number;
    selected_peers: Array<{
      company_name: string;
      employee_count: number;
      ai_maturity_score: number;
      ai_practices: string[];
    }>;
  };
  email: {
    subject: string;
    body: string;
  };
  confidence: Confidence;
  trace_id: string;
  trace_url?: string | null;
  claim_validation?: {
    valid: boolean;
    unsupported_claim_ids: string[];
    unexpected_numeric_tokens: string[];
    claims_used: string[];
  };
  reply_text?: string;
  qualification: {
    qualification_status: string;
    intent_level: string;
    signal_confidence: number;
    next_action: string;
    reasoning: string[];
  };
  booking: {
    should_book: boolean;
    booking_url: string;
    booking_reason: string;
  };
}

export interface DemoFlowResponse {
  session_id: string;
  session_started_at: string;
  prospect_identity: {
    company_name: string;
    contact_name: string;
    contact_email: string;
    phone_number: string;
    conversation_id: string;
  };
  qualification: {
    qualification_status: string;
    intent_level: string;
    next_action: string;
    allowed_next_channels_after_reply: string[];
  };
  email_send: {
    channel: string;
    provider: string;
    status: string;
    destination: string;
    external_id?: string | null;
    detail: string;
    subject: string;
    body: string;
    crm_contact_id?: string | null;
  };
  reply_event: {
    channel: string;
    provider: string;
    event_type: string;
    message_text: string;
    allowed_next_channels: string[];
    crm_activity_id?: string | null;
  };
  sms_follow_up: {
    channel: string;
    provider: string;
    status: string;
    destination: string;
    external_id?: string | null;
    detail: string;
    body: string;
    crm_activity_id?: string | null;
  };
  lifecycle: {
    current_stage: string;
    booking_completed: boolean;
    allowed_next_channels: string[];
    activities: Array<{
      channel: string;
      direction: string;
      event_type: string;
      detail: string;
      provider?: string | null;
      external_id?: string | null;
      recorded_at: string;
    }>;
  };
  hubspot_record: {
    contact_id: string;
    properties: Record<string, string | number | null>;
    activities: Array<{
      id: string;
      contact_id: string;
      subject: string;
      body: string;
      channel: string;
      recorded_at: string;
    }>;
  };
  calcom_booking: {
    booking_id: string;
    booking_url: string;
    event_type: string;
    attendee_name: string;
    attendee_email: string;
    confirmed_at: string;
    meeting_start: string;
    booking_note_id?: string | null;
  };
  crm_sync: Record<string, unknown>;
}
