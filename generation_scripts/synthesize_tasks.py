from __future__ import annotations

"""Multi-LLM synthesis pipeline for Tenacious-Bench.

Routing policy:
- Cheap generation model family: Gemini via OpenRouter (`google/gemini-2.5-flash`) for
  bulk seed expansion across the known Week 10 failure dimensions.
- Cheap judge model family: Qwen via OpenRouter (`qwen/qwen3-32b`) for high-volume
  pointwise filtering on coherence, verifiability, and rubric clarity.
- Optional eval-tier calibration: a frontier-family reviewer is sampled only for a
  small calibration slice so the expensive judge never becomes the bulk filter.

Preference-leakage guard:
- The generator and judge must come from different model families.
- Near-duplicate synthesis paths are resolved pairwise using judge scores rather than
  keeping every fluent variant.

Prompts are committed verbatim under `generation_scripts/prompts/` so the synthesis
process is inspectable and reproducible.
"""

import json
import random
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent.llm.client import OpenRouterClient
from agent.utils.config import get_settings

OUT_PATH = REPO_ROOT / "generation_scripts" / "synthesis_cache.json"
PROMPT_ROOT = REPO_ROOT / "generation_scripts" / "prompts"

RANDOM_SEED = 11
GENERATOR_MODEL = "google/gemini-2.5-flash"
POINTWISE_MIN_SCORE = 4
CALIBRATION_SAMPLE_SIZE = 50
CALIBRATION_SEED_FAMILIES = {"synth-weak-confidence", "synth-cto-sensitivity"}


@dataclass(frozen=True)
class JudgeRoute:
    role: str
    model: str
    max_tokens: int
    temperature: float


BULK_JUDGE_ROUTE = JudgeRoute(
    role="dev_tier_bulk_filter",
    model="qwen/qwen3-32b",
    max_tokens=900,
    temperature=0.3,
)

EVAL_TIER_JUDGE_ROUTE = JudgeRoute(
    role="eval_tier_calibration",
    model="anthropic/claude-sonnet-4.5",
    max_tokens=900,
    temperature=0.0,
)


SEED_FAMILIES = [
    {
        "family_id": "synth-weak-confidence",
        "dimension": "weak_confidence_handling",
        "brief": "Create hard cases where public signal is thin or contradictory and the safe answer must stay question-led.",
    },
    {
        "family_id": "synth-cto-sensitivity",
        "dimension": "cto_sensitivity",
        "brief": "Create CTO-facing peer-gap outreach that stays respectful and uncertainty-aware rather than condescending.",
    },
    {
        "family_id": "synth-outsourcing-mismatch",
        "dimension": "outsourcing_mismatch",
        "brief": "Create cases where the right move is capability partnership language rather than generic augmentation.",
    },
    {
        "family_id": "synth-signal-overclaiming",
        "dimension": "signal_over_claiming",
        "brief": "Create cases where the temptation is to overstate urgency from weak funding or hiring data.",
    },
    {
        "family_id": "synth-pricing-handoff",
        "dimension": "pricing_handoff",
        "brief": "Create reply cases where the agent must not invent non-public pricing and should route to a human.",
    },
    {
        "family_id": "synth-scheduling-calibration",
        "dimension": "scheduling_calibration",
        "brief": "Create booking and follow-up cases where timezone or warm-thread status must change the answer.",
    },
]


def _model_family(model_name: str) -> str:
    return model_name.split("/", 1)[0].lower()


def _as_confidence(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().lower()
    mapping = {"weak": 0.45, "low": 0.45, "medium": 0.65, "moderate": 0.65, "high": 0.82}
    if text in mapping:
        return mapping[text]
    try:
        return float(text)
    except ValueError:
        return 0.6


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "yes", "1"}


def _generator_client() -> OpenRouterClient:
    settings = get_settings().model_copy(
        update={
            "openrouter_model": GENERATOR_MODEL,
            "openrouter_fallback_model": GENERATOR_MODEL,
            "openrouter_max_tokens": 1600,
        }
    )
    return OpenRouterClient(settings=settings)


def _judge_client() -> OpenRouterClient:
    settings = get_settings().model_copy(
        update={
            "openrouter_model": BULK_JUDGE_ROUTE.model,
            "openrouter_fallback_model": BULK_JUDGE_ROUTE.model,
            "openrouter_max_tokens": 1000,
        }
    )
    return OpenRouterClient(settings=settings)


def _eval_tier_client() -> OpenRouterClient:
    settings = get_settings().model_copy(
        update={
            "openrouter_model": EVAL_TIER_JUDGE_ROUTE.model,
            "openrouter_fallback_model": EVAL_TIER_JUDGE_ROUTE.model,
            "openrouter_max_tokens": 1000,
        }
    )
    return OpenRouterClient(settings=settings)


def validate_routing_policy(
    generator_model: str = GENERATOR_MODEL,
    bulk_judge_model: str = BULK_JUDGE_ROUTE.model,
    eval_tier_model: str = EVAL_TIER_JUDGE_ROUTE.model,
) -> None:
    if _model_family(generator_model) == _model_family(bulk_judge_model):
        raise ValueError("Generator and bulk judge model families must differ to avoid preference leakage.")
    if _model_family(eval_tier_model) in {_model_family(generator_model), _model_family(bulk_judge_model)}:
        raise ValueError("Eval-tier calibration model family must differ from both generator and bulk judge families.")


def _prompt_template(name: str) -> str:
    return (PROMPT_ROOT / name).read_text()


def _generation_prompt(seed: dict[str, str]) -> tuple[str, str]:
    system = _prompt_template("generation_system.md")
    user = _prompt_template("generation_user.md").format(
        seed_family=seed["family_id"],
        dimension=seed["dimension"],
        brief=seed["brief"],
    )
    return system, user


def _judge_prompt(seed: dict[str, str], tasks: list[dict[str, Any]]) -> tuple[str, str]:
    system = _prompt_template("judge_system.md")
    user = _prompt_template("judge_user.md").format(
        minimum_score=POINTWISE_MIN_SCORE,
        seed_family=seed["family_id"],
        tasks_json=json.dumps(tasks, ensure_ascii=True),
    )
    return system, user


def _normalize_task(seed: dict[str, str], generated: dict[str, Any], task_index: int, judge_score: dict[str, Any]) -> dict[str, Any]:
    company_name = str(generated.get("company_name", "Northstar Lending"))
    signal_confidence = _as_confidence(generated.get("signal_confidence", 0.6))
    required_strings = [str(item).lower() for item in generated.get("required_signal_strings", []) if str(item).strip()]
    subject_prefix = "Question:" if signal_confidence < 0.6 else "Context:"
    candidate_output = {
        "subject": f"{subject_prefix} {company_name} signal check",
        "body": generated["good_body"],
    }
    ground_truth = {
        "required_signal_strings": required_strings or [company_name.lower().split()[0]],
        "require_question_mark": _as_bool(generated.get("require_question_mark", False)),
        "require_calendar_link": _as_bool(generated.get("require_calendar_link", False)),
        "require_handoff_phrase": generated.get("require_handoff_phrase"),
        "require_no_dollar_sign": _as_bool(generated.get("require_no_dollar_sign", False)),
    }

    return {
        "task_id": f"tb-{seed['family_id']}-{task_index:02d}",
        "family_id": seed["family_id"],
        "dimension": seed["dimension"],
        "difficulty": generated.get("difficulty", "hard"),
        "task_type": "email_grounding",
        "input": {
            "company_name": company_name,
            "signal_confidence": signal_confidence,
            "hiring_signal_brief_excerpt": generated["setup"],
            "competitor_gap_brief_excerpt": generated["gap_excerpt"],
            "prior_thread": generated.get("prior_thread", ""),
        },
        "candidate_output": candidate_output,
        "ground_truth": ground_truth,
        "metadata": {
            "generator_model": GENERATOR_MODEL,
            "judge_model": BULK_JUDGE_ROUTE.model,
            "judge_role": BULK_JUDGE_ROUTE.role,
            "judge_scores": {
                "coherence": judge_score["coherence"],
                "verifiability": judge_score["verifiability"],
                "rubric_clarity": judge_score["rubric_clarity"],
            },
            "notes": generated.get("rationale", ""),
        },
    }


def _score_total(row: dict[str, Any]) -> int:
    return int(row["coherence"]) + int(row["verifiability"]) + int(row["rubric_clarity"])


def _pairwise_keep(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    left_total = _score_total(left["judge_score"])
    right_total = _score_total(right["judge_score"])
    if right_total > left_total:
        return right
    if left_total > right_total:
        return left
    left_body_len = len(str(left["task"].get("good_body", "")))
    right_body_len = len(str(right["task"].get("good_body", "")))
    return left if left_body_len <= right_body_len else right


def _near_duplicate_key(task: dict[str, Any]) -> tuple[str, str]:
    company = str(task.get("company_name", "")).strip().lower()
    setup = " ".join(str(task.get("setup", "")).lower().split()[:12])
    return company, setup


def _deduplicate_pairs(scored_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    kept: dict[tuple[str, str], dict[str, Any]] = {}
    for row in scored_rows:
        key = _near_duplicate_key(row["task"])
        if key not in kept:
            kept[key] = row
            continue
        kept[key] = _pairwise_keep(kept[key], row)
    return list(kept.values())


def _should_include(judge_score: dict[str, Any]) -> bool:
    return (
        bool(judge_score.get("include", False))
        and int(judge_score.get("coherence", 0)) >= POINTWISE_MIN_SCORE
        and int(judge_score.get("verifiability", 0)) >= POINTWISE_MIN_SCORE
        and int(judge_score.get("rubric_clarity", 0)) >= POINTWISE_MIN_SCORE
    )


def _run_eval_tier_calibration(
    eval_judge: OpenRouterClient,
    seed: dict[str, str],
    tasks: list[dict[str, Any]],
    rng: random.Random,
) -> dict[str, Any] | None:
    """Spot-check a bounded slice with an eval-tier judge.

    The calibration sample is intentionally capped at 50 tasks so the expensive
    judge stays a sampled audit path rather than the main authoring filter.
    """
    if not tasks:
        return None
    sample_size = min(CALIBRATION_SAMPLE_SIZE, len(tasks))
    sampled = rng.sample(tasks, sample_size)
    system, user = _judge_prompt(seed, sampled)
    judged = eval_judge.chat_json(
        system_prompt=system,
        user_prompt=user,
        prompt_name="week11_eval_tier_judge_calibration",
        temperature=EVAL_TIER_JUDGE_ROUTE.temperature,
        max_tokens=EVAL_TIER_JUDGE_ROUTE.max_tokens,
        metadata={"seed_family": seed["family_id"], "mode": "eval_calibration"},
    )
    return {
        "role": EVAL_TIER_JUDGE_ROUTE.role,
        "model": judged.model,
        "task_count": sample_size,
        "scores": judged.content["scores"],
        "estimated_cost_usd": judged.cost_details.get("estimated_cost_usd", 0.0),
    }


def main() -> None:
    validate_routing_policy()

    generator = _generator_client()
    judge = _judge_client()
    eval_judge = _eval_tier_client()
    rng = random.Random(RANDOM_SEED)
    all_tasks: list[dict[str, Any]] = []
    cost_log: list[dict[str, Any]] = []
    calibration_log: list[dict[str, Any]] = []
    filter_log: list[dict[str, Any]] = []

    for seed in SEED_FAMILIES:
        system_prompt, user_prompt = _generation_prompt(seed)
        generated = generator.chat_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            prompt_name="week11_generate_bench_tasks",
            temperature=0.4,
            max_tokens=1400,
            metadata={"seed_family": seed["family_id"], "mode": "generation"},
        )
        tasks = generated.content["tasks"]
        judge_system, judge_user = _judge_prompt(seed, tasks)
        judged = judge.chat_json(
            system_prompt=judge_system,
            user_prompt=judge_user,
            prompt_name="week11_judge_bench_tasks",
            temperature=BULK_JUDGE_ROUTE.temperature,
            max_tokens=BULK_JUDGE_ROUTE.max_tokens,
            metadata={"seed_family": seed["family_id"], "mode": BULK_JUDGE_ROUTE.role},
        )
        score_rows = judged.content["scores"]
        scored_rows = []
        for index, task in enumerate(tasks):
            judge_score = next((row for row in score_rows if int(row["index"]) == index), None)
            if not judge_score:
                filter_log.append(
                    {
                        "seed_family": seed["family_id"],
                        "task_index": index,
                        "passed": False,
                        "reason": "missing_judge_score",
                    }
                )
                continue
            passed = _should_include(judge_score)
            reasons = []
            if not bool(judge_score.get("include", False)):
                reasons.append("judge_marked_exclude")
            if int(judge_score.get("coherence", 0)) < POINTWISE_MIN_SCORE:
                reasons.append("coherence_below_threshold")
            if int(judge_score.get("verifiability", 0)) < POINTWISE_MIN_SCORE:
                reasons.append("verifiability_below_threshold")
            if int(judge_score.get("rubric_clarity", 0)) < POINTWISE_MIN_SCORE:
                reasons.append("rubric_clarity_below_threshold")
            filter_log.append(
                {
                    "seed_family": seed["family_id"],
                    "task_index": index,
                    "passed": passed,
                    "reason": "passed" if passed else ",".join(reasons),
                    "scores": {
                        "coherence": judge_score.get("coherence"),
                        "verifiability": judge_score.get("verifiability"),
                        "rubric_clarity": judge_score.get("rubric_clarity"),
                    },
                }
            )
            if not passed:
                continue
            scored_rows.append({"task": task, "judge_score": judge_score})
        deduped = _deduplicate_pairs(scored_rows)
        kept = [
            _normalize_task(seed, row["task"], index + 1, row["judge_score"])
            for index, row in enumerate(deduped)
        ]
        all_tasks.extend(kept)
        if seed["family_id"] in CALIBRATION_SEED_FAMILIES:
            calibration = _run_eval_tier_calibration(eval_judge, seed, tasks, rng)
            if calibration:
                calibration_log.append({"seed_family": seed["family_id"], **calibration})
        cost_log.append(
            {
                "seed_family": seed["family_id"],
                "generation_model": generated.model,
                "judge_model": judged.model,
                "judge_role": BULK_JUDGE_ROUTE.role,
                "generation_cost_usd": generated.cost_details.get("estimated_cost_usd", 0.0),
                "judge_cost_usd": judged.cost_details.get("estimated_cost_usd", 0.0),
                "generated_count": len(tasks),
                "kept_count": len(kept),
            }
        )

    OUT_PATH.write_text(
        json.dumps(
            {
                "random_seed": RANDOM_SEED,
                "tasks": all_tasks,
                "cost_log": cost_log,
                "calibration_log": calibration_log,
                "filter_log": filter_log,
            },
            indent=2,
        )
        + "\n"
    )
    print(
        json.dumps(
            {
                "output_path": str(OUT_PATH),
                "task_count": len(all_tasks),
                "cost_log": cost_log,
                "calibration_log": calibration_log,
                "filter_log_rows": len(filter_log),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
