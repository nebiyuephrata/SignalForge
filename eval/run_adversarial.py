from __future__ import annotations

from pathlib import Path

from agent.core.orchestrator import SignalForgeOrchestrator
from agent.utils.trace_logger import append_jsonl_log, write_json
from eval.adversarial_cases import ADVERSARIAL_CASES


def evaluate_case(result: dict[str, object], expectations: dict[str, object]) -> dict[str, object]:
    hiring_summary = str(result["hiring_signal_brief"]["summary"])
    email_body = str(result["email"]["body"])
    company_name = str(result["company"])
    qualification_status = str(result["qualification"]["qualification_status"])
    should_book = bool(result["booking"]["should_book"])

    checks = {
        "summary_contains": str(expectations["summary_contains"]) in hiring_summary,
        "qualification_status": qualification_status == expectations["qualification_status"],
        "booking_should_book": should_book == expectations["booking_should_book"],
    }
    if "email_contains" in expectations:
        checks["email_contains"] = str(expectations["email_contains"]) in email_body
    if expectations.get("email_question_based"):
        checks["email_question_based"] = "?" in email_body
    if expectations.get("email_must_include_company"):
        checks["email_must_include_company"] = company_name in email_body or company_name in str(result["email"]["subject"])

    return {
        "passed": all(checks.values()),
        "checks": checks,
        "observed": {
            "hiring_summary": hiring_summary,
            "email_body": email_body,
            "qualification_status": qualification_status,
            "booking_should_book": should_book,
            "signal_confidence": result["hiring_signal_brief"]["overall_confidence"],
            "trace_id": result["trace_id"],
        },
    }


def run() -> dict[str, object]:
    repo_root = Path(__file__).resolve().parents[1]
    orchestrator = SignalForgeOrchestrator()
    case_results: list[dict[str, object]] = []

    for case in ADVERSARIAL_CASES:
        result = orchestrator.run_scenario(
            company_name=case["company_name"],
            reply_text=case["reply_text"],
            scenario_name=case["name"],
        )
        evaluation = evaluate_case(result, case["expectations"])
        case_result = {
            "scenario_name": case["name"],
            "company_name": case["company_name"],
            "evaluation": evaluation,
            "result": result,
        }
        case_results.append(case_result)
        append_jsonl_log(str(repo_root / "eval" / "logs" / "trace_log.jsonl"), case_result)

    summary = {
        "total_cases": len(case_results),
        "passed_cases": sum(1 for case in case_results if case["evaluation"]["passed"]),
        "results": case_results,
    }
    write_json(str(repo_root / "outputs" / "adversarial_results.json"), summary)
    write_json(str(repo_root / "eval" / "logs" / "score_log.json"), summary)
    return summary


def compact_summary(summary: dict[str, object]) -> dict[str, object]:
    results = summary["results"]
    scenarios = [
        {
            "scenario_name": case["scenario_name"],
            "company_name": case["company_name"],
            "passed": case["evaluation"]["passed"],
            "qualification_status": case["result"]["qualification"]["qualification_status"],
            "booking_should_book": case["result"]["booking"]["should_book"],
            "signal_confidence": case["evaluation"]["observed"]["signal_confidence"],
        }
        for case in results
    ]
    return {
        "total_cases": summary["total_cases"],
        "passed_cases": summary["passed_cases"],
        "failed_cases": summary["total_cases"] - summary["passed_cases"],
        "scenarios": scenarios,
    }


if __name__ == "__main__":
    summary = run()
    print(f"Passed {summary['passed_cases']} / {summary['total_cases']} adversarial cases.")
