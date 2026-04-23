from dataclasses import dataclass


@dataclass
class EvalCase:
    name: str
    expected_behavior: str


def load_eval_cases() -> list[EvalCase]:
    return [
        EvalCase(name="low_confidence_abstention", expected_behavior="ask_question"),
        EvalCase(name="high_confidence_booking", expected_behavior="book_meeting"),
    ]
