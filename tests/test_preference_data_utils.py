from __future__ import annotations

from training.preference_data_utils import build_preference_rows


def sample_email_task() -> dict:
    return {
        "task_id": "tb-test-001",
        "dimension": "signal_over_claiming",
        "task_type": "email_grounding",
        "source_mode": "hand-authored",
        "input": {
            "company_name": "Quiet Current Bank",
            "prior_thread": "",
            "signal_confidence": 0.42,
        },
        "ground_truth": {
            "allowed_subject_prefixes": ["request:", "question:", "context:", "follow-up:"],
            "banned_phrases": ["world-class", "you need offshore capacity"],
            "max_body_words": 120,
            "require_calendar_link": False,
            "require_handoff_phrase": None,
            "require_no_dollar_sign": True,
            "require_question_mark": True,
            "required_signal_strings": ["quiet", "technical"],
        },
        "candidate_output": {
            "subject": "Question: Quiet Current Bank signal check",
            "body": (
                "Question: I only see directional public evidence for Quiet Current Bank. "
                "Before assuming the pressure is technical capacity, I want to confirm whether "
                "this is actually an engineering bottleneck?"
            ),
        },
        "metadata": {
            "week10_evidence_refs": [],
            "probe_refs": [],
        },
    }


def test_build_preference_rows_creates_multiple_unique_email_negatives() -> None:
    rows = build_preference_rows(
        [sample_email_task()],
        split="train",
        normalize_dimensions=True,
        render_plain_strings=True,
    )

    assert len(rows) == 3
    assert {row["rejection_strategy"] for row in rows} == {
        "strong_overclaiming",
        "constraint_break",
        "wordy_overconfident",
    }
    assert all(row["chosen"] != row["rejected"] for row in rows)
    assert all(row["dimension"] == "signal_over_claiming" for row in rows)
    assert len({row["rejected"] for row in rows}) == 3
    assert any("world-class engineers" in row["rejected"] for row in rows)
    assert any("$25k" in row["rejected"] or "$45k" in row["rejected"] for row in rows)
