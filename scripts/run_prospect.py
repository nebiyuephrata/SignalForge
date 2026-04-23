from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.services.prospect_run_service import ProspectRunService


def main() -> None:
    result = ProspectRunService().run()
    print("Generated:")
    print("- outputs/hiring_signal_brief.json")
    print("- outputs/competitor_gap_brief.json")
    print("- outputs/email.json")
    print("- outputs/draft_email.json")
    print("- outputs/full_prospect_run.json")
    print(f"- outputs/{result.get('scenario_name', result['company']).lower().replace(' ', '_')}_full_run.json")
    print(f"Qualification: {result['qualification']['qualification_status']}")
    print(f"Booking URL: {result['booking']['booking_url']}")


if __name__ == "__main__":
    main()
