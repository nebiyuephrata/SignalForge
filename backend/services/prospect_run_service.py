from __future__ import annotations

from pathlib import Path

from agent.core.orchestrator import SignalForgeOrchestrator
from agent.utils.trace_logger import append_jsonl_log, write_json
from eval.adversarial_cases import get_adversarial_case, list_adversarial_case_names
from eval.run_adversarial import compact_summary, run as run_adversarial_suite


class ProspectRunService:
    def __init__(self) -> None:
        self.orchestrator = SignalForgeOrchestrator()
        self.repo_root = Path(__file__).resolve().parents[2]

    def available_scenarios(self) -> list[str]:
        return list_adversarial_case_names()

    def run_batch(self) -> dict[str, object]:
        summary = run_adversarial_suite()
        compact = compact_summary(summary)
        write_json(str(self.repo_root / "outputs" / "adversarial_batch_summary.json"), compact)
        append_jsonl_log(
            str(self.repo_root / "logs" / "prospect_runs.jsonl"),
            {
                "batch_run": True,
                "total_cases": compact["total_cases"],
                "passed_cases": compact["passed_cases"],
                "failed_cases": compact["failed_cases"],
                "scenarios": compact["scenarios"],
            },
        )
        return compact

    def run(
        self,
        company_name: str | None = None,
        reply_text: str | None = None,
        scenario_name: str | None = None,
        contact_email: str | None = None,
    ) -> dict[str, object]:
        if scenario_name:
            case = get_adversarial_case(scenario_name)
            if case is None:
                raise ValueError(f"Unknown scenario: {scenario_name}")
            result = self.orchestrator.run_scenario(
                company_name=str(case["company_name"]),
                reply_text=str(case["reply_text"]) if reply_text is None else reply_text,
                scenario_name=str(case["name"]),
            )
        else:
            result = self.orchestrator.run_single_prospect(
                company_name=company_name or self.orchestrator.crunchbase_tool.list_companies()[0]["company_name"],
                reply_text=reply_text,
                contact_email=contact_email,
            )

        artifact_slug = self._artifact_slug(result)
        write_json(str(self.repo_root / "outputs" / f"{artifact_slug}_hiring_signal_brief.json"), result["hiring_signal_brief"])
        write_json(
            str(self.repo_root / "outputs" / f"{artifact_slug}_competitor_gap_brief.json"),
            result["competitor_gap_brief"],
        )
        write_json(str(self.repo_root / "outputs" / f"{artifact_slug}_email.json"), result["email"])
        write_json(str(self.repo_root / "outputs" / f"{artifact_slug}_draft_email.json"), result["email"])
        write_json(str(self.repo_root / "outputs" / f"{artifact_slug}_channel_plan.json"), result["channel_plan"])
        write_json(str(self.repo_root / "outputs" / f"{artifact_slug}_full_run.json"), result)

        # Keep the original stable filenames for the latest run.
        write_json(str(self.repo_root / "outputs" / "hiring_signal_brief.json"), result["hiring_signal_brief"])
        write_json(str(self.repo_root / "outputs" / "competitor_gap_brief.json"), result["competitor_gap_brief"])
        write_json(str(self.repo_root / "outputs" / "email.json"), result["email"])
        write_json(str(self.repo_root / "outputs" / "draft_email.json"), result["email"])
        write_json(str(self.repo_root / "outputs" / "channel_plan.json"), result["channel_plan"])
        write_json(str(self.repo_root / "outputs" / "full_prospect_run.json"), result)

        append_jsonl_log(
            str(self.repo_root / "logs" / "prospect_runs.jsonl"),
            {
                "scenario_name": result.get("scenario_name"),
                "input_company": result["company"],
                "confidence": result["confidence"],
                "trace_id": result["trace_id"],
                "signals": {
                    "hiring_signal_brief": result["hiring_signal_brief"],
                    "competitor_gap_brief": result["competitor_gap_brief"],
                },
                "email": result["email"],
                "reply_text": result["reply_text"],
                "qualification": result["qualification"],
                "booking": result["booking"],
                "channel_plan": result["channel_plan"],
            },
        )
        return result

    def _artifact_slug(self, result: dict[str, object]) -> str:
        scenario_name = result.get("scenario_name")
        if scenario_name:
            return str(scenario_name).strip().lower().replace(" ", "_")
        return str(result["company"]).strip().lower().replace(" ", "_")
