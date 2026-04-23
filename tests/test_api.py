import asyncio
from pathlib import Path

from fastapi import HTTPException

from backend.routes import run_prospect as run_prospect_route
from backend.schemas import RunProspectRequest


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
