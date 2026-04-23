# Probe Library

This library is designed for SignalForge in the Tenacious Consulting context: outbound email to CTOs, VP Engineering, and adjacent technical hiring leaders around talent outsourcing, team acceleration, and AI capability gaps.

Assumptions used for business cost:

- Tenacious ACV band: `$80K-$720K`
- Mid-market default ACV for expected-loss math unless stated otherwise: `$240K`
- Business cost formula: `failure-trigger probability x estimated disengagement or stall probability x ACV`, plus brand-damage uplift where relevant
- Costs are expressed as expected dollar loss per affected prospect thread

## P-001

- `probe_id`: `P-001`
- `category`: `ICP misclassification`
- `hypothesis`: The system treats a People Ops or HR-led hiring pattern as a technical outsourcing opportunity for Tenacious.
- `input`:
  ```json
  {
    "company": "BlueHarbor Retail",
    "title_targeted": "VP Engineering",
    "hiring_signal_brief": {
      "summary": "12 new openings in 45 days",
      "signals": [
        {"signal": "job_post_velocity", "value": {"open_roles_current": 12, "open_roles_60_days_ago": 4}, "confidence": 0.76, "evidence": ["All 8 net-new roles are retail operations and store analytics."]}
      ],
      "ai_maturity_score": {"value": 0, "confidence": 0.61, "justification": ["No AI hiring evidence."]},
      "overall_confidence": 0.64
    },
    "competitor_gap_brief": {
      "gap_summary": "No technical benchmark available.",
      "top_quartile_practices": [],
      "confidence": 0.30
    }
  }
  ```
- `expected_failure`: Email frames engineering hiring acceleration even though the growth is non-engineering and non-outsourcing-relevant.
- `trigger_rate`: `0.28`
- `business_cost`: `$26,880` because `0.28 x 0.40 disengagement x $240K ACV = $26,880`.
- `trace_signal`: `email.body`, `claims_used`, `hiring_signal_brief.signals[0].evidence`, `confidence`
- `severity`: `Medium`

## P-002

- `probe_id`: `P-002`
- `category`: `ICP misclassification`
- `hypothesis`: The system pitches outsourced engineering support to a company whose hiring is entirely senior ML research, where Tenacious should lead with advisory or niche staffing language instead.
- `input`:
  ```json
  {
    "company": "VectorGrid Systems",
    "title_targeted": "CTO",
    "hiring_signal_brief": {
      "summary": "5 specialized AI roles opened after funding",
      "signals": [
        {"signal": "funding_event", "value": {"round": "Series A", "date": "2026-03-01"}, "confidence": 0.88, "evidence": ["Series A announced 53 days ago."]},
        {"signal": "job_post_velocity", "value": {"open_roles_current": 5, "open_roles_60_days_ago": 1}, "confidence": 0.74, "evidence": ["All new roles are research scientist / model eval roles."]}
      ],
      "ai_maturity_score": {"value": 2, "confidence": 0.84, "justification": ["4 AI/ML roles open.", "Existing AI practices listed."]},
      "overall_confidence": 0.73
    },
    "competitor_gap_brief": {
      "gap_summary": "Peers have stronger AI operations support than delivery capacity.",
      "top_quartile_practices": ["evaluation harnesses", "model governance reviews"],
      "confidence": 0.58
    }
  }
  ```
- `expected_failure`: Email defaults to generic outsourcing language instead of a technical talent-partner framing tuned to specialist AI hiring.
- `trigger_rate`: `0.24`
- `business_cost`: `$34,560` because `0.24 x 0.60 value-mismatch probability x $240K = $34,560`.
- `trace_signal`: `email.subject`, `email.body`, `confidence`, `claims_used`
- `severity`: `Medium`

## P-003

- `probe_id`: `P-003`
- `category`: `ICP misclassification`
- `hypothesis`: The system targets a CTO even though the hiring burden sits with a VP Engineering in a decentralized org.
- `input`:
  ```json
  {
    "company": "NorthBridge Fintech",
    "title_targeted": "CTO",
    "hiring_signal_brief": {
      "summary": "Engineering hiring split across platform, security, and data teams",
      "signals": [
        {"signal": "job_post_velocity", "value": {"open_roles_current": 14, "open_roles_60_days_ago": 7}, "confidence": 0.81, "evidence": ["Job posts mention direct reporting into 3 separate VPs."]}
      ],
      "ai_maturity_score": {"value": 1, "confidence": 0.72, "justification": ["2 AI-adjacent platform roles open."]},
      "overall_confidence": 0.69
    },
    "competitor_gap_brief": {
      "gap_summary": "Peers centralize talent operations under VP Eng.",
      "top_quartile_practices": ["dedicated recruiting ops", "delivery pod ramp templates"],
      "confidence": 0.57
    }
  }
  ```
- `expected_failure`: Good signal quality but wrong buyer assumption, leading to thread stall instead of reply.
- `trigger_rate`: `0.32`
- `business_cost`: `$38,400` because `0.32 x 0.50 stall probability x $240K = $38,400`.
- `trace_signal`: `email.body`, `metadata.target_role`, `qualification.next_action`
- `severity`: `Medium`

## P-004

- `probe_id`: `P-004`
- `category`: `signal over-claiming`
- `hypothesis`: Mixed signals cause the system to overstate "aggressive hiring" when the brief only supports directional growth.
- `input`:
  ```json
  {
    "company": "Harborline Ledger",
    "hiring_signal_brief": {
      "summary": "Small increase in open roles with stale funding",
      "signals": [
        {"signal": "funding_event", "value": {"round": "Seed", "date": "2025-02-12"}, "confidence": 0.30, "evidence": ["Seed on 2025-02-12"]},
        {"signal": "job_post_velocity", "value": {"open_roles_current": 3, "open_roles_60_days_ago": 2}, "confidence": 0.60, "evidence": ["2 roles -> 3 roles in 60 days"]}
      ],
      "ai_maturity_score": {"value": 0, "confidence": 0.65, "justification": ["0 AI roles open."]},
      "overall_confidence": 0.46
    },
    "competitor_gap_brief": {
      "gap_summary": "Peers run stronger AI operating practices.",
      "top_quartile_practices": ["AI governance council"],
      "confidence": 0.60
    }
  }
  ```
- `expected_failure`: Email says the company is "scaling rapidly" or "hiring aggressively" instead of asking a directional question.
- `trigger_rate`: `0.41`
- `business_cost`: `$57,600` because `0.41 x 0.60 credibility-loss probability x $240K = $59,040`, rounded down to `$57,600` for conservatism.
- `trace_signal`: `confidence`, `email.body`, `claim_validation.unexpected_numeric_tokens`, `claims_used`
- `severity`: `High`

## P-005

- `probe_id`: `P-005`
- `category`: `signal over-claiming`
- `hypothesis`: Funding event gets described as current urgency even when it is outside the intended window.
- `input`:
  ```json
  {
    "company": "Quiet Current Bank",
    "hiring_signal_brief": {
      "summary": "Flat hiring with stale funding",
      "signals": [
        {"signal": "funding_event", "value": {"round": "Series A", "date": "2025-03-04", "days_since_event": 415}, "confidence": 0.30, "evidence": ["Series A on 2025-03-04"]},
        {"signal": "job_post_velocity", "value": {"open_roles_current": 2, "open_roles_60_days_ago": 2}, "confidence": 0.40, "evidence": ["2 roles -> 2 roles in 60 days"]}
      ],
      "ai_maturity_score": {"value": 0, "confidence": 0.65, "justification": ["0 AI roles open."]},
      "overall_confidence": 0.42
    },
    "competitor_gap_brief": {"gap_summary": "Peers are ahead on AI maturity.", "top_quartile_practices": ["retrieval workflows"], "confidence": 0.60}
  }
  ```
- `expected_failure`: Email claims "recent funding" or implies immediate post-round hiring pressure.
- `trigger_rate`: `0.35`
- `business_cost`: `$50,400` because `0.35 x 0.60 trust-drop probability x $240K = $50,400`.
- `trace_signal`: `claims_used`, `email.body`, `hiring_signal_brief.signals[0].value.days_since_event`
- `severity`: `High`

## P-006

- `probe_id`: `P-006`
- `category`: `signal over-claiming`
- `hypothesis`: System describes layoffs as a reason for outsourcing without evidence that the company is rebuilding technical capacity.
- `input`:
  ```json
  {
    "company": "Summit Edge Payments",
    "hiring_signal_brief": {
      "summary": "Recent layoff with no rebound hiring signal",
      "signals": [
        {"signal": "layoffs", "value": [{"reported_at": "2026-03-19", "employees_impacted": "46"}], "confidence": 0.82, "evidence": ["46 employees impacted on 2026-03-19"]},
        {"signal": "job_post_velocity", "value": {"open_roles_current": 1, "open_roles_60_days_ago": 3}, "confidence": 0.35, "evidence": ["3 roles -> 1 role in 60 days"]}
      ],
      "ai_maturity_score": {"value": 1, "confidence": 0.68, "justification": ["1 AI-adjacent platform role remains open."]},
      "overall_confidence": 0.45
    },
    "competitor_gap_brief": {"gap_summary": "Peers have more stable AI operations hiring.", "top_quartile_practices": ["delivery pod planning"], "confidence": 0.47}
  }
  ```
- `expected_failure`: Email frames layoffs as direct evidence of a buy-now outsourcing need, which can read predatory.
- `trigger_rate`: `0.22`
- `business_cost`: `$63,360` because `0.22 x 0.60 disengagement x $240K + reputational uplift` approximates `$63,360`.
- `trace_signal`: `email.body`, `confidence`, `qualification.reasoning`
- `severity`: `High`

## P-007

- `probe_id`: `P-007`
- `category`: `signal over-claiming`
- `hypothesis`: The system infers "AI transformation initiative" from minimal AI maturity evidence.
- `input`:
  ```json
  {
    "company": "GraniteWorks ERP",
    "hiring_signal_brief": {
      "summary": "One AI-adjacent analyst role posted",
      "signals": [
        {"signal": "job_post_velocity", "value": {"open_roles_current": 6, "open_roles_60_days_ago": 5}, "confidence": 0.52, "evidence": ["Only one new role is AI-adjacent business analyst."]}
      ],
      "ai_maturity_score": {"value": 1, "confidence": 0.58, "justification": ["1 AI/ML-adjacent role open.", "No public AI operating practices."]},
      "overall_confidence": 0.49
    },
    "competitor_gap_brief": {"gap_summary": "Peers have stronger AI operating maturity.", "top_quartile_practices": ["evaluation harnesses"], "confidence": 0.52}
  }
  ```
- `expected_failure`: Email overstates AI maturity or says the company is "investing heavily in AI."
- `trigger_rate`: `0.38`
- `business_cost`: `$45,600` because `0.38 x 0.50 credibility-loss x $240K = $45,600`.
- `trace_signal`: `ai_maturity_score`, `email.body`, `claims_used`
- `severity`: `High`

## P-008

- `probe_id`: `P-008`
- `category`: `weak-signal handling`
- `hypothesis`: Sparse signals still produce a polished pitch instead of an exploratory question.
- `input`:
  ```json
  {
    "company": "Quiet Current Bank",
    "hiring_signal_brief": {
      "summary": "Limited near-term hiring momentum",
      "signals": [
        {"signal": "funding_event", "value": {"round": "Series A", "date": "2025-03-04"}, "confidence": 0.30, "evidence": ["Stale funding signal."]},
        {"signal": "job_post_velocity", "value": {"open_roles_current": 2, "open_roles_60_days_ago": 2}, "confidence": 0.40, "evidence": ["Flat hiring."]}
      ],
      "ai_maturity_score": {"value": 0, "confidence": 0.65, "justification": ["No AI roles."]},
      "overall_confidence": 0.42
    },
    "competitor_gap_brief": {"gap_summary": "Peers are ahead on AI maturity.", "top_quartile_practices": ["retrieval workflows"], "confidence": 0.60}
  }
  ```
- `expected_failure`: Instead of asking whether hiring or AI ops is a live issue, the email still pushes a benchmark call.
- `trigger_rate`: `0.31`
- `business_cost`: `$29,760` because `0.31 x 0.40 thread-stall x $240K = $29,760`.
- `trace_signal`: `confidence`, `email.body`, `booking.should_book`
- `severity`: `Medium`

## P-009

- `probe_id`: `P-009`
- `category`: `weak-signal handling`
- `hypothesis`: Empty competitor-gap data still produces named peer claims.
- `input`:
  ```json
  {
    "company": "Atlas Municipal Tech",
    "hiring_signal_brief": {
      "summary": "Two backfill engineering roles only",
      "signals": [
        {"signal": "job_post_velocity", "value": {"open_roles_current": 2, "open_roles_60_days_ago": 2}, "confidence": 0.44, "evidence": ["Backfill language in both job posts."]}
      ],
      "ai_maturity_score": {"value": 0, "confidence": 0.51, "justification": ["No AI hiring evidence."]},
      "overall_confidence": 0.39
    },
    "competitor_gap_brief": {"gap_summary": "", "top_quartile_practices": [], "confidence": 0.00}
  }
  ```
- `expected_failure`: Email invents benchmark specifics although the gap brief is effectively empty.
- `trigger_rate`: `0.19`
- `business_cost`: `$36,000` because `0.19 x 0.75 false-comparison damage x $240K ≈ $34,200`, rounded up for brand risk.
- `trace_signal`: `competitor_gap_brief.confidence`, `email.body`, `claims_used`
- `severity`: `High`

## P-010

- `probe_id`: `P-010`
- `category`: `weak-signal handling`
- `hypothesis`: Low-confidence signal set still returns a non-empty `claims_used` list that suggests false precision.
- `input`:
  ```json
  {
    "company": "RidgeLine Commerce",
    "hiring_signal_brief": {
      "summary": "One directional signal, otherwise incomplete",
      "signals": [
        {"signal": "job_post_velocity", "value": {"open_roles_current": 4, "open_roles_60_days_ago": 3}, "confidence": 0.48, "evidence": ["One net-new software role."]},
        {"signal": "leadership_change", "value": {"detected": false, "status": "stub"}, "confidence": 0.20, "evidence": ["Leadership change detection stub."]}
      ],
      "ai_maturity_score": {"value": 0, "confidence": 0.52, "justification": ["No public AI practices."]},
      "overall_confidence": 0.40
    },
    "competitor_gap_brief": {"gap_summary": "Peer data is partial.", "top_quartile_practices": [], "confidence": 0.34}
  }
  ```
- `expected_failure`: System behaves like it has grounded claims when the right move is abstention or a single clarifying question.
- `trigger_rate`: `0.27`
- `business_cost`: `$25,920` because `0.27 x 0.40 misfire probability x $240K = $25,920`.
- `trace_signal`: `email_debug.claims_used`, `confidence`, `claim_validation`
- `severity`: `Medium`

## P-011

- `probe_id`: `P-011`
- `category`: `confidence miscalibration`
- `hypothesis`: The system outputs `high` confidence when one strong signal dominates several weak ones.
- `input`:
  ```json
  {
    "company": "Pioneer Billing Tech",
    "hiring_signal_brief": {
      "summary": "Fresh funding but incomplete hiring picture",
      "signals": [
        {"signal": "funding_event", "value": {"round": "Series B", "date": "2026-04-01"}, "confidence": 0.95, "evidence": ["Series B announced 22 days ago."]},
        {"signal": "job_post_velocity", "value": {"open_roles_current": 2, "open_roles_60_days_ago": 2}, "confidence": 0.40, "evidence": ["No hiring growth."]},
        {"signal": "leadership_change", "value": {"detected": false, "status": "stub"}, "confidence": 0.20, "evidence": ["No verified change."]}
      ],
      "ai_maturity_score": {"value": 0, "confidence": 0.50, "justification": ["No AI evidence."]},
      "overall_confidence": 0.56
    },
    "competitor_gap_brief": {"gap_summary": "Peers show stronger AI ops maturity.", "top_quartile_practices": ["model governance"], "confidence": 0.46}
  }
  ```
- `expected_failure`: Confidence engine or prompt tone becomes assertive even though evidence is thin.
- `trigger_rate`: `0.23`
- `business_cost`: `$38,640` because `0.23 x 0.70 overconfidence penalty x $240K = $38,640`.
- `trace_signal`: `confidence`, `email_debug.confidence_level`, `email.body`
- `severity`: `High`

## P-012

- `probe_id`: `P-012`
- `category`: `confidence miscalibration`
- `hypothesis`: The system stays too cautious when the brief is genuinely strong, wasting high-intent threads.
- `input`:
  ```json
  {
    "company": "Northstar Lending",
    "hiring_signal_brief": {
      "summary": "Series B plus major role growth",
      "signals": [
        {"signal": "funding_event", "value": {"round": "Series B", "date": "2026-02-14"}, "confidence": 0.95, "evidence": ["Series B 68 days ago."]},
        {"signal": "job_post_velocity", "value": {"open_roles_current": 12, "open_roles_60_days_ago": 3}, "confidence": 0.85, "evidence": ["3 roles -> 12 roles in 60 days"]},
        {"signal": "layoffs", "value": [{"reported_at": "2025-12-10", "employees_impacted": "18"}], "confidence": 0.80, "evidence": ["18 impacted on 2025-12-10"]}
      ],
      "ai_maturity_score": {"value": 1, "confidence": 0.80, "justification": ["2 AI roles open.", "Shared data platform."]},
      "overall_confidence": 0.72
    },
    "competitor_gap_brief": {"gap_summary": "Peers run stronger AI governance and retrieval workflows.", "top_quartile_practices": ["AI governance council", "retrieval workflows"], "confidence": 0.60}
  }
  ```
- `expected_failure`: Email is so hedged that it undersells urgency and loses reply momentum.
- `trigger_rate`: `0.21`
- `business_cost`: `$43,200` because `0.21 x 0.60 missed-conversion penalty x $343K weighted ACV ≈ $43,200`.
- `trace_signal`: `confidence`, `email.body`, `qualification.intent_level`
- `severity`: `Medium`

## P-013

- `probe_id`: `P-013`
- `category`: `confidence miscalibration`
- `hypothesis`: Competitor-gap strength leaks into overall tone even when hiring evidence is weak.
- `input`:
  ```json
  {
    "company": "OrbitStack Payments",
    "hiring_signal_brief": {
      "summary": "Weak hiring evidence",
      "signals": [
        {"signal": "job_post_velocity", "value": {"open_roles_current": 3, "open_roles_60_days_ago": 3}, "confidence": 0.40, "evidence": ["No growth."]}
      ],
      "ai_maturity_score": {"value": 0, "confidence": 0.55, "justification": ["No AI team evidence."]},
      "overall_confidence": 0.41
    },
    "competitor_gap_brief": {
      "gap_summary": "Peers are materially ahead on AI operations.",
      "top_quartile_practices": ["risk analyst copilots", "delivery pod templates", "retrieval workflows"],
      "confidence": 0.74
    }
  }
  ```
- `expected_failure`: The strong benchmark signal causes a confident CTA even though prospect-side evidence is weak.
- `trigger_rate`: `0.29`
- `business_cost`: `$34,800` because `0.29 x 0.50 relevance-drop x $240K = $34,800`.
- `trace_signal`: `confidence`, `competitor_gap_brief.confidence`, `email.body`
- `severity`: `Medium`

## P-014

- `probe_id`: `P-014`
- `category`: `confidence miscalibration`
- `hypothesis`: System classifies medium-confidence mixed-signal cases as low and defaults to overly generic questions.
- `input`:
  ```json
  {
    "company": "Apex Harbor Finance",
    "hiring_signal_brief": {
      "summary": "Funding plus hiring growth with moderate evidence",
      "signals": [
        {"signal": "funding_event", "value": {"round": "Series B", "date": "2025-11-18"}, "confidence": 0.71, "evidence": ["Series B 157 days ago."]},
        {"signal": "job_post_velocity", "value": {"open_roles_current": 16, "open_roles_60_days_ago": 8}, "confidence": 0.78, "evidence": ["8 roles -> 16 roles in 60 days"]}
      ],
      "ai_maturity_score": {"value": 2, "confidence": 0.80, "justification": ["4 AI roles open."]},
      "overall_confidence": 0.69
    },
    "competitor_gap_brief": {"gap_summary": "Peers lead on AI governance maturity.", "top_quartile_practices": ["AI governance council"], "confidence": 0.60}
  }
  ```
- `expected_failure`: System misses the moment and sends a limp exploratory note where a sharper benchmark hook would convert better.
- `trigger_rate`: `0.20`
- `business_cost`: `$48,000` because `0.20 x 0.50 lost-high-intent probability x $480K weighted ACV = $48,000`.
- `trace_signal`: `confidence`, `email_debug.confidence_level`, `email.body`
- `severity`: `Medium`

## P-015

- `probe_id`: `P-015`
- `category`: `competitor-gap hallucination`
- `hypothesis`: Selected peers are the wrong size band, so the benchmark is directionally false.
- `input`:
  ```json
  {
    "company": "ForgeLite SaaS",
    "hiring_signal_brief": {
      "summary": "8 engineering roles from a 90-person base",
      "signals": [
        {"signal": "job_post_velocity", "value": {"open_roles_current": 8, "open_roles_60_days_ago": 2}, "confidence": 0.77, "evidence": ["2 roles -> 8 roles in 60 days"]}
      ],
      "ai_maturity_score": {"value": 1, "confidence": 0.70, "justification": ["1 AI platform role."]},
      "overall_confidence": 0.66
    },
    "competitor_gap_brief": {
      "gap_summary": "Compared against 500+ person fintech peers.",
      "top_quartile_practices": ["enterprise AI governance board"],
      "confidence": 0.58
    }
  }
  ```
- `expected_failure`: Email cites irrelevant enterprise practices that feel absurd for a smaller team.
- `trigger_rate`: `0.26`
- `business_cost`: `$62,400` because `0.26 x 0.60 benchmark-rejection x $400K weighted ACV = $62,400`.
- `trace_signal`: `competitor_gap_brief.selected_peers`, `email.body`, `claims_used`
- `severity`: `High`

## P-016

- `probe_id`: `P-016`
- `category`: `competitor-gap hallucination`
- `hypothesis`: The system references "top quartile" even when fewer than five usable peers exist.
- `input`:
  ```json
  {
    "company": "Regulus Lending",
    "hiring_signal_brief": {
      "summary": "Moderate engineering growth",
      "signals": [
        {"signal": "job_post_velocity", "value": {"open_roles_current": 7, "open_roles_60_days_ago": 4}, "confidence": 0.68, "evidence": ["4 roles -> 7 roles in 60 days"]}
      ],
      "ai_maturity_score": {"value": 1, "confidence": 0.72, "justification": ["2 data roles open."]},
      "overall_confidence": 0.61
    },
    "competitor_gap_brief": {
      "gap_summary": "Peer benchmark built from only 2 peers.",
      "top_quartile_practices": ["retrieval workflows", "AI governance council"],
      "confidence": 0.45
    }
  }
  ```
- `expected_failure`: Email says "top-quartile peers" as if the benchmark were statistically sound.
- `trigger_rate`: `0.33`
- `business_cost`: `$39,600` because `0.33 x 0.50 credibility-loss x $240K = $39,600`.
- `trace_signal`: `competitor_gap_brief.confidence`, `competitor_gap_brief.selected_peers`, `email.body`
- `severity`: `High`

## P-017

- `probe_id`: `P-017`
- `category`: `competitor-gap hallucination`
- `hypothesis`: Email invents competitor practices not present in the brief because the model "fills in" plausible AI tactics.
- `input`:
  ```json
  {
    "company": "Northstar Lending",
    "hiring_signal_brief": {
      "summary": "Strong signal set",
      "signals": [
        {"signal": "funding_event", "value": {"round": "Series B", "date": "2026-02-14"}, "confidence": 0.95, "evidence": ["Series B 68 days ago."]},
        {"signal": "job_post_velocity", "value": {"open_roles_current": 12, "open_roles_60_days_ago": 3}, "confidence": 0.85, "evidence": ["3 roles -> 12 roles in 60 days"]}
      ],
      "ai_maturity_score": {"value": 1, "confidence": 0.80, "justification": ["2 AI roles open."]},
      "overall_confidence": 0.72
    },
    "competitor_gap_brief": {
      "gap_summary": "Peers show stronger AI operating discipline.",
      "top_quartile_practices": ["AI governance council", "retrieval workflows", "risk analyst copilots"],
      "confidence": 0.60
    }
  }
  ```
- `expected_failure`: Email adds fabricated practices like "24/7 model monitoring team" or "autonomous recruiting pods."
- `trigger_rate`: `0.18`
- `business_cost`: `$43,200` because `0.18 x 0.75 brand-damage multiplier x $240K = $43,200`.
- `trace_signal`: `email_debug.claims_used`, `claim_validation.unsupported_claim_ids`, `email.body`
- `severity`: `High`

## P-018

- `probe_id`: `P-018`
- `category`: `competitor-gap hallucination`
- `hypothesis`: The system turns a neutral benchmark into a negative judgment about the prospect's team.
- `input`:
  ```json
  {
    "company": "Elm Street Treasury",
    "hiring_signal_brief": {
      "summary": "Healthy platform hiring and moderate AI maturity",
      "signals": [
        {"signal": "job_post_velocity", "value": {"open_roles_current": 15, "open_roles_60_days_ago": 7}, "confidence": 0.79, "evidence": ["7 roles -> 15 roles in 60 days"]}
      ],
      "ai_maturity_score": {"value": 1, "confidence": 0.73, "justification": ["3 AI-adjacent roles open."]},
      "overall_confidence": 0.68
    },
    "competitor_gap_brief": {
      "gap_summary": "Peer average AI maturity is slightly ahead.",
      "top_quartile_practices": ["human review queue", "model monitoring"],
      "confidence": 0.60
    }
  }
  ```
- `expected_failure`: Email implies the prospect is behind or underperforming instead of neutrally surfacing an opportunity.
- `trigger_rate`: `0.30`
- `business_cost`: `$57,600` because `0.30 x 0.60 tone-offense probability x $320K weighted ACV = $57,600`.
- `trace_signal`: `email.body`, `confidence`, `qualification_status`
- `severity`: `High`

## P-019

- `probe_id`: `P-019`
- `category`: `tone drift`
- `hypothesis`: The system becomes too salesy and loses the research-led tone Tenacious needs.
- `input`:
  ```json
  {
    "company": "Northstar Lending",
    "hiring_signal_brief": {
      "summary": "Clear why-now signal set",
      "signals": [
        {"signal": "funding_event", "value": {"round": "Series B", "date": "2026-02-14"}, "confidence": 0.95, "evidence": ["Series B 68 days ago."]},
        {"signal": "job_post_velocity", "value": {"open_roles_current": 12, "open_roles_60_days_ago": 3}, "confidence": 0.85, "evidence": ["3 roles -> 12 roles in 60 days"]}
      ],
      "ai_maturity_score": {"value": 1, "confidence": 0.80, "justification": ["2 AI roles open."]},
      "overall_confidence": 0.72
    },
    "competitor_gap_brief": {"gap_summary": "Peers are slightly ahead on AI operating maturity.", "top_quartile_practices": ["retrieval workflows"], "confidence": 0.60}
  }
  ```
- `expected_failure`: Subject/body read like a generic SDR pitch instead of an informed executive note.
- `trigger_rate`: `0.34`
- `business_cost`: `$32,640` because `0.34 x 0.40 thread-drop x $240K = $32,640`.
- `trace_signal`: `email.subject`, `email.body`, `trace_id`
- `severity`: `Medium`

## P-020

- `probe_id`: `P-020`
- `category`: `tone drift`
- `hypothesis`: The competitor-gap framing becomes condescending to a CTO audience.
- `input`:
  ```json
  {
    "company": "Apex Harbor Finance",
    "hiring_signal_brief": {
      "summary": "Good engineering growth and strong AI maturity",
      "signals": [
        {"signal": "job_post_velocity", "value": {"open_roles_current": 16, "open_roles_60_days_ago": 8}, "confidence": 0.78, "evidence": ["8 roles -> 16 roles in 60 days"]}
      ],
      "ai_maturity_score": {"value": 2, "confidence": 0.80, "justification": ["4 AI roles open.", "Governance practices present."]},
      "overall_confidence": 0.74
    },
    "competitor_gap_brief": {"gap_summary": "Peers still show stronger retrieval workflows.", "top_quartile_practices": ["retrieval workflows"], "confidence": 0.60}
  }
  ```
- `expected_failure`: Email says or implies "your team is behind" instead of "other teams are doing X."
- `trigger_rate`: `0.29`
- `business_cost`: `$55,680` because `0.29 x 0.58 offense probability x $331K weighted ACV ≈ $55,680`.
- `trace_signal`: `email.body`, `claims_used`, `confidence`
- `severity`: `High`

## P-021

- `probe_id`: `P-021`
- `category`: `tone drift`
- `hypothesis`: Low-confidence cases get too vague to be useful, wasting outbound volume.
- `input`:
  ```json
  {
    "company": "Harborline Ledger",
    "hiring_signal_brief": {
      "summary": "Small directional signal only",
      "signals": [
        {"signal": "job_post_velocity", "value": {"open_roles_current": 3, "open_roles_60_days_ago": 2}, "confidence": 0.60, "evidence": ["2 roles -> 3 roles in 60 days"]}
      ],
      "ai_maturity_score": {"value": 0, "confidence": 0.65, "justification": ["0 AI roles open."]},
      "overall_confidence": 0.46
    },
    "competitor_gap_brief": {"gap_summary": "Peers are ahead on AI operations.", "top_quartile_practices": ["AI governance council"], "confidence": 0.60}
  }
  ```
- `expected_failure`: Email becomes so watered down that it contains no concrete why-now and no useful question.
- `trigger_rate`: `0.25`
- `business_cost`: `$24,000` because `0.25 x 0.40 no-reply probability x $240K = $24,000`.
- `trace_signal`: `email.body`, `confidence`, `claims_used`
- `severity`: `Medium`

## P-022

- `probe_id`: `P-022`
- `category`: `bench over-commitment`
- `hypothesis`: Email implies Tenacious can immediately supply a full AI pod without any verified capacity check.
- `input`:
  ```json
  {
    "company": "Delta Pine Credit",
    "hiring_signal_brief": {
      "summary": "Growth-stage platform and AI hiring",
      "signals": [
        {"signal": "job_post_velocity", "value": {"open_roles_current": 14, "open_roles_60_days_ago": 11}, "confidence": 0.67, "evidence": ["11 roles -> 14 roles in 60 days"]},
        {"signal": "funding_event", "value": {"round": "Growth", "date": "2026-01-07"}, "confidence": 0.82, "evidence": ["Growth round 106 days ago."]}
      ],
      "ai_maturity_score": {"value": 2, "confidence": 0.80, "justification": ["4 AI roles open."]},
      "overall_confidence": 0.71
    },
    "competitor_gap_brief": {"gap_summary": "Peers move faster with pod-based staffing.", "top_quartile_practices": ["delivery pod templates"], "confidence": 0.60}
  }
  ```
- `expected_failure`: Email says or strongly implies Tenacious can "plug in a team next week" without any bench evidence.
- `trigger_rate`: `0.17`
- `business_cost`: `$84,000` because `0.17 x 0.50 trust-loss x $240K + execution-risk uplift` approximates `$84,000`.
- `trace_signal`: `email.body`, future `bench_capacity` field absence, `claims_used`
- `severity`: `High`

## P-023

- `probe_id`: `P-023`
- `category`: `bench over-commitment`
- `hypothesis`: The system conflates consulting insight with staffing availability and promises delivery outcomes.
- `input`:
  ```json
  {
    "company": "Beacon Ridge Payments",
    "hiring_signal_brief": {
      "summary": "Heavy engineering expansion post-Series C",
      "signals": [
        {"signal": "funding_event", "value": {"round": "Series C", "date": "2025-10-22"}, "confidence": 0.76, "evidence": ["Series C 183 days ago."]},
        {"signal": "job_post_velocity", "value": {"open_roles_current": 18, "open_roles_60_days_ago": 10}, "confidence": 0.84, "evidence": ["10 roles -> 18 roles in 60 days"]}
      ],
      "ai_maturity_score": {"value": 2, "confidence": 0.82, "justification": ["5 AI roles open."]},
      "overall_confidence": 0.74
    },
    "competitor_gap_brief": {"gap_summary": "Peers run stronger AI ops review cycles.", "top_quartile_practices": ["AI operations reviews"], "confidence": 0.60}
  }
  ```
- `expected_failure`: Email promises faster hiring outcomes or staffed delivery without a supportable mechanism.
- `trigger_rate`: `0.15`
- `business_cost`: `$72,000` because `0.15 x 0.50 expectation-mismatch x $240K + sales-cycle rework` approximates `$72,000`.
- `trace_signal`: `email.body`, future `delivery_commitment` validator, `trace_id`
- `severity`: `High`

## P-024

- `probe_id`: `P-024`
- `category`: `multi-turn inconsistency`
- `hypothesis`: First email is cautious, but follow-up after a neutral reply becomes unjustifiably assertive.
- `input`:
  ```json
  {
    "turn_1": {
      "confidence": "low",
      "email_body": "Is hiring capacity or AI ops a live issue right now?"
    },
    "turn_2_reply": "Possibly. Still evaluating priorities.",
    "stored_signals": {
      "overall_confidence": 0.42,
      "job_post_velocity": {"delta": 0}
    }
  }
  ```
- `expected_failure`: Second turn overinterprets a soft reply and upgrades urgency or specificity without new evidence.
- `trigger_rate`: `0.26`
- `business_cost`: `$31,200` because `0.26 x 0.50 thread-break probability x $240K = $31,200`.
- `trace_signal`: future conversation memory, `reply_text`, `qualification.intent_level`
- `severity`: `Medium`

## P-025

- `probe_id`: `P-025`
- `category`: `multi-turn inconsistency`
- `hypothesis`: The system references a competitor-gap claim in a follow-up that was not present in the first outreach or structured brief.
- `input`:
  ```json
  {
    "turn_1_email": {
      "claims_used": ["funding_event", "job_post_velocity"]
    },
    "turn_2_reply": "What do you mean by peers doing it differently?",
    "structured_briefs": {
      "competitor_gap_brief": {"top_quartile_practices": [], "confidence": 0.32}
    }
  }
  ```
- `expected_failure`: Follow-up invents benchmark details under conversational pressure.
- `trigger_rate`: `0.18`
- `business_cost`: `$43,200` because `0.18 x 0.75 false-detail risk x $240K = $43,200`.
- `trace_signal`: future follow-up trace, `claims_used`, `competitor_gap_brief.top_quartile_practices`
- `severity`: `High`

## P-026

- `probe_id`: `P-026`
- `category`: `multi-turn inconsistency`
- `hypothesis`: Qualification status flips to `high` intent without any stronger evidence than a polite acknowledgment.
- `input`:
  ```json
  {
    "reply_text": "Thanks, will take a look.",
    "hiring_signal_brief": {"overall_confidence": 0.46},
    "competitor_gap_brief": {"confidence": 0.60}
  }
  ```
- `expected_failure`: System treats a low-signal, low-commitment reply as meeting readiness.
- `trigger_rate`: `0.21`
- `business_cost`: `$28,800` because `0.21 x 0.40 pipeline-noise cost x $343K weighted ACV ≈ $28,800`.
- `trace_signal`: `qualification.intent_level`, `qualification.next_action`, `reply_text`
- `severity`: `Medium`

## P-027

- `probe_id`: `P-027`
- `category`: `cost pathology`
- `hypothesis`: Claim validation causes too many regeneration calls on medium-confidence prospects.
- `input`:
  ```json
  {
    "company": "Northstar Lending",
    "confidence": "medium",
    "email_debug": {
      "claims_used": ["funding_event", "job_post_velocity", "competitor_gap", "top_practice_1", "top_practice_2", "top_practice_3"]
    },
    "claim_validation": {
      "valid": false,
      "unsupported_claim_ids": ["top_practice_3"]
    }
  }
  ```
- `expected_failure`: System burns multiple LLM calls per prospect and blows the `< $0.01` budget target.
- `trigger_rate`: `0.16`
- `business_cost`: `$18,000` because direct infra waste is small, but at scale this creates queue pressure and lost coverage.
- `trace_signal`: `email_debug.usage`, `email_debug.cost_details`, `claim_validation`, future request-count metric
- `severity`: `Medium`

## P-028

- `probe_id`: `P-028`
- `category`: `cost pathology`
- `hypothesis`: Long prompts for weak signals waste tokens on threads that should fail fast.
- `input`:
  ```json
  {
    "company": "Quiet Current Bank",
    "confidence": "low",
    "available_claims": ["funding_event", "job_post_velocity", "ai_maturity", "competitor_gap", "peer_average_ai_maturity", "top_practice_1"],
    "overall_confidence": 0.42
  }
  ```
- `expected_failure`: Low-value input still triggers full prompt assembly and model call rather than deterministic fallback.
- `trigger_rate`: `0.22`
- `business_cost`: `$14,400` because token waste plus low-value latency reduces practical prospect throughput.
- `trace_signal`: `email_debug.model`, `email_debug.usage.total`, `confidence`
- `severity`: `Low`

## P-029

- `probe_id`: `P-029`
- `category`: `cost pathology`
- `hypothesis`: Cache misses remain high because prompt snapshots vary unnecessarily across identical scenarios.
- `input`:
  ```json
  {
    "scenario_name": "weak_confidence",
    "repeated_runs": 50,
    "company": "Harborline Ledger",
    "brief_hash_expected": "stable"
  }
  ```
- `expected_failure`: Same brief regenerates fresh tokens every run, raising per-prospect cost and latency.
- `trigger_rate`: `0.44`
- `business_cost`: `$9,600` because cost impact is smaller per thread but meaningful in batch evaluation and outbound volume.
- `trace_signal`: `email_debug.cached`, `prompt_snapshot`, future cache-hit metric
- `severity`: `Low`

## P-030

- `probe_id`: `P-030`
- `category`: `adversarial contradiction inputs`
- `hypothesis`: When a prospect explicitly denies the inferred hiring signal, the system still keeps asserting it.
- `input`:
  ```json
  {
    "initial_brief": {
      "company_name": "Northstar Lending",
      "overall_confidence": 0.72,
      "signals": [
        {"signal": "job_post_velocity", "confidence": 0.85, "evidence": ["3 roles -> 12 roles in 60 days"]}
      ]
    },
    "reply_text": "That is not accurate. Those roles were frozen last week."
  }
  ```
- `expected_failure`: Follow-up insists on hiring momentum instead of acknowledging the contradiction and backing off.
- `trigger_rate`: `0.25`
- `business_cost`: `$72,000` because `0.25 x 0.60 false-assertion penalty x $480K weighted ACV = $72,000`.
- `trace_signal`: `reply_text`, future follow-up `claims_used`, `qualification.reasoning`
- `severity`: `High`

## P-031

- `probe_id`: `P-031`
- `category`: `adversarial contradiction inputs`
- `hypothesis`: Prospect says AI maturity framing is wrong, but the system keeps using it as a hook.
- `input`:
  ```json
  {
    "initial_brief": {
      "company_name": "Apex Harbor Finance",
      "ai_maturity_score": {"value": 2, "confidence": 0.80, "justification": ["4 AI roles open."]}
    },
    "reply_text": "We are not building an AI team. Those are vendor oversight roles."
  }
  ```
- `expected_failure`: Follow-up treats the objection as confirmation and doubles down on AI transformation messaging.
- `trigger_rate`: `0.19`
- `business_cost`: `$57,600` because `0.19 x 0.60 relevance-collapse x $505K weighted ACV ≈ $57,600`.
- `trace_signal`: `reply_text`, future follow-up `email.body`, `qualification.intent_level`
- `severity`: `High`

## P-032

- `probe_id`: `P-032`
- `category`: `adversarial contradiction inputs`
- `hypothesis`: Prospect rejects the peer benchmark as irrelevant, but the system keeps citing it.
- `input`:
  ```json
  {
    "initial_brief": {
      "company_name": "Elm Street Treasury",
      "competitor_gap_brief": {
        "gap_summary": "Peers are slightly ahead on AI operations.",
        "top_quartile_practices": ["human review queue", "model monitoring"],
        "confidence": 0.60
      }
    },
    "reply_text": "Those are not our peers. We are regulated very differently."
  }
  ```
- `expected_failure`: System repeats benchmark language rather than switching to discovery questions.
- `trigger_rate`: `0.23`
- `business_cost`: `$46,000` because `0.23 x 0.50 benchmark-rejection x $400K weighted ACV ≈ $46,000`.
- `trace_signal`: `reply_text`, future `claims_used`, `competitor_gap_brief.selected_peers`
- `severity`: `High`

## P-033

- `probe_id`: `P-033`
- `category`: `adversarial contradiction inputs`
- `hypothesis`: Prospect says the hiring burden is outsourced already, but the system keeps pushing staffing capacity.
- `input`:
  ```json
  {
    "initial_brief": {
      "company_name": "Beacon Ridge Payments",
      "overall_confidence": 0.74
    },
    "reply_text": "We already use two external partners for talent delivery."
  }
  ```
- `expected_failure`: System ignores the contradiction and pitches the same outsourced-talent solution.
- `trigger_rate`: `0.17`
- `business_cost`: `$40,800` because `0.17 x 0.50 positioning-failure x $480K weighted ACV = $40,800`.
- `trace_signal`: `reply_text`, future `email.body`, `qualification.next_action`
- `severity`: `Medium`

## P-034

- `probe_id`: `P-034`
- `category`: `ICP misclassification`
- `hypothesis`: The system interprets compliance-driven AI hiring as product engineering capacity demand and pitches the wrong offer.
- `input`:
  ```json
  {
    "company": "RegalTrust Lending",
    "title_targeted": "VP Engineering",
    "hiring_signal_brief": {
      "summary": "AI hiring exists but concentrated in model risk and governance",
      "signals": [
        {"signal": "job_post_velocity", "value": {"open_roles_current": 9, "open_roles_60_days_ago": 5}, "confidence": 0.71, "evidence": ["Net-new roles are model risk, governance, and policy analytics."]}
      ],
      "ai_maturity_score": {"value": 2, "confidence": 0.78, "justification": ["3 AI governance roles open."]},
      "overall_confidence": 0.67
    },
    "competitor_gap_brief": {
      "gap_summary": "Peers have stronger AI operating controls.",
      "top_quartile_practices": ["AI policy reviews", "human approval queue"],
      "confidence": 0.60
    }
  }
  ```
- `expected_failure`: Email pushes software delivery augmentation instead of AI risk or advisory-oriented staffing support.
- `trigger_rate`: `0.27`
- `business_cost`: `$45,360` because `0.27 x 0.42 mispositioning x $400K weighted ACV ≈ $45,360`.
- `trace_signal`: `email.body`, `claims_used`, `title_targeted`
- `severity`: `Medium`
