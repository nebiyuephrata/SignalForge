ADVERSARIAL_CASES = [
    {
        "name": "conflicting_signals",
        "company_name": "Northstar Lending",
        "reply_text": (
            "Yes, that's directionally right. We're adding AI operations capacity this quarter "
            "and would be open to a 20-minute call next week."
        ),
        "expectations": {
            "summary_contains": "mixed but timely hiring intent",
            "email_must_include_company": True,
            "qualification_status": "qualified",
            "booking_should_book": True,
        },
    },
    {
        "name": "no_hiring_signals",
        "company_name": "Quiet Current Bank",
        "reply_text": "Not a priority right now. You may be reading too much into it.",
        "expectations": {
            "summary_contains": "limited near-term hiring momentum",
            "email_question_based": True,
            "qualification_status": "partial",
            "booking_should_book": False,
        },
    },
    {
        "name": "weak_confidence",
        "company_name": "Harborline Ledger",
        "reply_text": "Maybe. We're still figuring out whether there's anything urgent here.",
        "expectations": {
            "summary_contains": "small increase in open roles",
            "email_question_based": True,
            "qualification_status": "partial",
            "booking_should_book": False,
        },
    },
]


def get_adversarial_case(name: str) -> dict[str, object] | None:
    normalized = name.strip().lower()
    for case in ADVERSARIAL_CASES:
        if str(case["name"]).strip().lower() == normalized:
            return case
    return None


def list_adversarial_case_names() -> list[str]:
    return [str(case["name"]) for case in ADVERSARIAL_CASES]
