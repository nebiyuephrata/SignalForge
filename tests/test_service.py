from pathlib import Path

from backend.services.prospect_run_service import ProspectRunService
from eval.probe_analysis import load_probe_library, select_target_failure_mode, summarize_by_category
from eval.run_adversarial import run as run_adversarial_suite


def test_service_run_default_writes_latest_artifacts(tmp_path) -> None:
    service = ProspectRunService()
    service.repo_root = tmp_path

    result = service.run()

    assert result["company"] == "Northstar Lending"
    assert result["qualification"]["qualification_status"] == "qualified"
    assert (tmp_path / "outputs" / "hiring_signal_brief.json").exists()
    assert (tmp_path / "outputs" / "northstar_lending_full_run.json").exists()
    assert (tmp_path / "outputs" / "channel_plan.json").exists()
    assert (tmp_path / "logs" / "prospect_runs.jsonl").exists()


def test_service_run_named_scenario_writes_scenario_artifacts(tmp_path) -> None:
    service = ProspectRunService()
    service.repo_root = tmp_path

    result = service.run(scenario_name="weak_confidence")

    assert result["scenario_name"] == "weak_confidence"
    assert result["booking"]["should_book"] is False
    assert (tmp_path / "outputs" / "weak_confidence_full_run.json").exists()
    assert result["confidence_assessment"]["level"] in {"low", "medium"}


def test_service_run_batch_returns_compact_summary(tmp_path, monkeypatch) -> None:
    service = ProspectRunService()
    service.repo_root = tmp_path

    fake_summary = {
        "total_cases": 2,
        "passed_cases": 1,
        "results": [
            {
                "scenario_name": "case_one",
                "company_name": "Alpha Co",
                "evaluation": {
                    "passed": True,
                    "observed": {"signal_confidence": 0.7},
                },
                "result": {
                    "qualification": {"qualification_status": "qualified"},
                    "booking": {"should_book": True},
                },
            },
            {
                "scenario_name": "case_two",
                "company_name": "Beta Co",
                "evaluation": {
                    "passed": False,
                    "observed": {"signal_confidence": 0.3},
                },
                "result": {
                    "qualification": {"qualification_status": "partial"},
                    "booking": {"should_book": False},
                },
            },
        ],
    }

    monkeypatch.setattr(
        "backend.services.prospect_run_service.run_adversarial_suite",
        lambda: fake_summary,
    )

    summary = service.run_batch()

    assert summary["total_cases"] == 2
    assert summary["passed_cases"] == 1
    assert summary["failed_cases"] == 1
    assert summary["scenarios"][0]["scenario_name"] == "case_one"
    assert (tmp_path / "outputs" / "adversarial_batch_summary.json").exists()


def test_probe_analysis_tracks_target_failure_mode() -> None:
    probes = load_probe_library()
    assert len(probes) >= 30

    summaries = summarize_by_category(probes)
    weak_confidence = next(summary for summary in summaries if summary["category"] == "weak confidence handling")
    assert weak_confidence["probe_count"] >= 4

    target = select_target_failure_mode(probes)
    assert target["target_category"]["category"] == "weak confidence handling"
    assert len(target["alternatives"]) == 2


def test_adversarial_suite_currently_passes_all_cases() -> None:
    summary = run_adversarial_suite()

    assert summary["total_cases"] >= 3
    assert summary["passed_cases"] == summary["total_cases"]
