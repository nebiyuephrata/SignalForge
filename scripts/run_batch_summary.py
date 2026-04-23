from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.services.prospect_run_service import ProspectRunService


if __name__ == "__main__":
    summary = ProspectRunService().run_batch()
    print(f"Passed {summary['passed_cases']} / {summary['total_cases']} batch scenarios.")
    for scenario in summary["scenarios"]:
        print(
            f"- {scenario['scenario_name']}: passed={scenario['passed']} "
            f"qualification={scenario['qualification_status']} "
            f"book={scenario['booking_should_book']}"
        )
