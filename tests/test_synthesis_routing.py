from __future__ import annotations

import pytest

from generation_scripts.synthesize_tasks import CALIBRATION_SAMPLE_SIZE, validate_routing_policy


def test_validate_routing_policy_accepts_distinct_families() -> None:
    validate_routing_policy(
        generator_model="google/gemini-2.5-flash",
        bulk_judge_model="qwen/qwen3-32b",
        eval_tier_model="anthropic/claude-sonnet-4.5",
    )


def test_validate_routing_policy_rejects_generator_judge_family_overlap() -> None:
    with pytest.raises(ValueError, match="bulk judge model families must differ"):
        validate_routing_policy(
            generator_model="google/gemini-2.5-flash",
            bulk_judge_model="google/gemini-2.0-flash-lite",
            eval_tier_model="anthropic/claude-sonnet-4.5",
        )


def test_validate_routing_policy_rejects_eval_tier_family_overlap() -> None:
    with pytest.raises(ValueError, match="Eval-tier calibration model family must differ"):
        validate_routing_policy(
            generator_model="google/gemini-2.5-flash",
            bulk_judge_model="qwen/qwen3-32b",
            eval_tier_model="qwen/qwen-plus",
        )


def test_calibration_sample_size_stays_bounded() -> None:
    assert CALIBRATION_SAMPLE_SIZE == 50
