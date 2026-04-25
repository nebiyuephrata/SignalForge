import asyncio
from pathlib import Path

from fastapi import HTTPException

from backend.routes import demo as demo_route
from backend.routes import run_prospect as run_prospect_route
from backend.schemas import DemoRunLiveRequest, RunProspectRequest


def test_list_scenarios_returns_known_cases() -> None:
    response = asyncio.run(run_prospect_route.list_run_prospect_scenarios())

    assert response.scenarios == [
        "conflicting_signals",
        "no_hiring_signals",
        "weak_confidence",
    ]


def test_run_prospect_default_returns_expected_company(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(run_prospect_route.service, "repo_root", Path(tmp_path))
    response = asyncio.run(run_prospect_route.run_prospect())

    assert response.company == "Northstar Lending"
    assert response.qualification["qualification_status"] == "qualified"
    assert response.channel_plan["primary_channel"] == "email"
    assert response.email.subject


def test_run_prospect_invalid_scenario_returns_404() -> None:
    try:
        asyncio.run(
            run_prospect_route.run_prospect(
                RunProspectRequest(scenario_name="does_not_exist"),
            )
        )
    except HTTPException as exc:
        assert exc.status_code == 404
        assert "Unknown scenario" in str(exc.detail)
    else:
        raise AssertionError("Expected HTTPException for invalid scenario")


def test_run_prospect_demo_flow_returns_traceable_lifecycle(monkeypatch) -> None:
    monkeypatch.setattr(
        run_prospect_route.demo_flow_service,
        "run",
        lambda **_: {
            "session_id": "demo-1",
            "session_started_at": "2026-04-25T12:00:00Z",
            "prospect_identity": {
                "company_name": "Northstar Lending",
                "contact_email": "northstar.lending@example.com",
                "conversation_id": "northstar-lending|northstar.lending@example.com|+15551234567",
            },
            "qualification": {"qualification_status": "qualified"},
            "email_send": {"status": "queued"},
            "reply_event": {"event_type": "reply"},
            "sms_follow_up": {"status": "queued"},
            "lifecycle": {"current_stage": "BOOKED"},
            "hubspot_record": {"contact_id": "demo-contact-1"},
            "calcom_booking": {"booking_id": "demo-booking-1"},
            "crm_sync": {"email_send": {"contact": {"id": "demo-contact-1"}}},
        },
    )

    response = asyncio.run(run_prospect_route.run_prospect_demo_flow())

    assert response.prospect_identity["company_name"] == "Northstar Lending"
    assert response.lifecycle["current_stage"] == "BOOKED"
    assert response.calcom_booking["booking_id"] == "demo-booking-1"


def test_run_live_demo_endpoint_returns_typed_artifacts(monkeypatch) -> None:
    monkeypatch.setattr(
        demo_route.service,
        "run",
        lambda **_: {
            "company": "Northstar Lending",
            "hiring_signal_brief": {"summary": "Signals grounded."},
            "competitor_gap_brief": {"gap_summary": "Peers are ahead on AI ops hiring."},
            "generated_email": {"subject": "Quick thought for Northstar Lending", "body": "Body"},
            "channel_plan": {"primary_channel": "email", "allowed_channels_after_reply": ["sms", "whatsapp", "calendar"]},
            "confidence_score": 0.82,
            "confidence_level": "high",
            "trace_id": "trace-1",
            "trace_url": "https://example.com/traces/trace-1",
        },
    )

    response = asyncio.run(
        demo_route.run_live_demo(DemoRunLiveRequest(company_name="Northstar Lending"))
    )

    assert response.company == "Northstar Lending"
    assert response.generated_email.subject
    assert response.channel_plan["primary_channel"] == "email"


def test_run_live_demo_endpoint_falls_back_on_exception(monkeypatch) -> None:
    monkeypatch.setattr(
        demo_route.service.orchestrator,
        "run_single_prospect",
        lambda **_: (_ for _ in ()).throw(RuntimeError("upstream failed")),
    )

    response = asyncio.run(
        demo_route.run_live_demo(DemoRunLiveRequest(company_name="Northstar Lending"))
    )

    assert response.company == "Northstar Lending"
    assert response.generated_email.subject
    assert response.confidence_score == 0.0
    assert response.channel_plan["primary_channel"] == "email"


def test_batch_endpoint_returns_compact_summary(monkeypatch) -> None:
    monkeypatch.setattr(
        run_prospect_route.service,
        "run_batch",
        lambda: {
            "total_cases": 1,
            "passed_cases": 1,
            "failed_cases": 0,
            "scenarios": [
                {
                    "scenario_name": "demo_case",
                    "company_name": "Demo Co",
                    "passed": True,
                    "qualification_status": "qualified",
                    "booking_should_book": True,
                    "signal_confidence": 0.8,
                }
            ],
        },
    )
    response = asyncio.run(run_prospect_route.run_prospect_batch())

    assert response.passed_cases == 1
    assert response.scenarios[0].scenario_name == "demo_case"
