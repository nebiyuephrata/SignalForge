from __future__ import annotations

from training.preference_data_utils import build_preference_rows
from training.export_unsloth_datasets import split_non_heldout_tasks


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


def test_build_preference_rows_creates_multiple_structured_negatives() -> None:
    rows = build_preference_rows(
        [
            {
                "task_id": "tb-qual-001",
                "dimension": "weak_confidence_qualification",
                "task_type": "qualification_decision",
                "source_mode": "programmatic",
                "input": {
                    "company_name": "Northstar Lending",
                    "signal_confidence": 0.52,
                    "prior_thread": "Prospect asked for more detail before booking.",
                },
                "ground_truth": {
                    "qualification_status": "partial",
                    "intent_level": "medium",
                    "next_action": "ask_follow_up_question",
                },
                "candidate_output": {
                    "qualification_status": "partial",
                    "intent_level": "medium",
                    "next_action": "ask_follow_up_question",
                },
                "metadata": {"week10_evidence_refs": [], "probe_refs": []},
            }
        ],
        split="train",
        normalize_dimensions=True,
        render_plain_strings=True,
    )

    assert len(rows) == 3
    assert {row["rejection_strategy"] for row in rows} == {
        "qualification_aggressive",
        "qualification_conservative",
        "qualification_mixed_signal",
    }
    assert len({row["rejected"] for row in rows}) == 3
    assert any("share_booking_link" in row["rejected"] for row in rows)


def test_split_non_heldout_tasks_keeps_task_groups_disjoint() -> None:
    tasks = [
        {
            "task_id": "train-email-1",
            "task_type": "email_grounding",
            "dimension": "signal_over_claiming",
            "benchmark_source_split": "train",
        },
        {
            "task_id": "dev-email-1",
            "task_type": "email_grounding",
            "dimension": "signal_over_claiming",
            "benchmark_source_split": "dev",
        },
        {
            "task_id": "dev-email-2",
            "task_type": "email_grounding",
            "dimension": "signal_over_claiming",
            "benchmark_source_split": "dev",
        },
        {
            "task_id": "dev-qual-1",
            "task_type": "qualification_decision",
            "dimension": "weak_confidence_qualification",
            "benchmark_source_split": "dev",
        },
        {
            "task_id": "dev-qual-2",
            "task_type": "qualification_decision",
            "dimension": "weak_confidence_qualification",
            "benchmark_source_split": "dev",
        },
    ]

    export_train, export_dev = split_non_heldout_tasks(tasks)

    train_ids = {task["task_id"] for task in export_train}
    dev_ids = {task["task_id"] for task in export_dev}
    assert train_ids.isdisjoint(dev_ids)
    assert train_ids | dev_ids == {task["task_id"] for task in tasks}
    assert {task["task_type"] for task in export_train} == {
        "email_grounding",
        "qualification_decision",
    }
    assert {task["task_type"] for task in export_dev} == {
        "email_grounding",
        "qualification_decision",
    }
