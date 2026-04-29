from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
BENCH_ROOT = REPO_ROOT / "tenacious_bench_v0.1"


def load_tasks(split: str) -> list[dict[str, Any]]:
    path = BENCH_ROOT / split / "tasks.jsonl"
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def task_text(task: dict[str, Any]) -> str:
    parts = [
        task["dimension"],
        task["input"].get("company_name", ""),
        task["input"].get("hiring_signal_brief_excerpt", ""),
        task["input"].get("competitor_gap_brief_excerpt", ""),
        task["input"].get("prior_thread", ""),
    ]
    return " ".join(str(part) for part in parts if part).lower()


def tokenize(text: str) -> list[str]:
    return [token for token in "".join(char if char.isalnum() else " " for char in text).split() if token]


def ngrams(tokens: list[str], n: int = 8) -> set[tuple[str, ...]]:
    if len(tokens) < n:
        return set()
    return {tuple(tokens[idx : idx + n]) for idx in range(len(tokens) - n + 1)}


def cosine_similarity(left: Counter[str], right: Counter[str]) -> float:
    keys = set(left) | set(right)
    numerator = sum(left[key] * right[key] for key in keys)
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)


def longest_shared_ngram(tokens_a: list[str], tokens_b: list[str], minimum: int) -> int:
    if len(tokens_a) < minimum or len(tokens_b) < minimum:
        return 0
    if ngrams(tokens_a, minimum) & ngrams(tokens_b, minimum):
        return minimum
    return 0


def compare_splits(
    train_tasks: list[dict[str, Any]],
    held_out_tasks: list[dict[str, Any]],
    ngram_threshold: int,
    cosine_threshold: float,
) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    violations = 0
    for held_out in held_out_tasks:
        held_text = task_text(held_out)
        held_tokens = tokenize(held_text)
        held_counter = Counter(held_tokens)
        max_overlap = 0
        max_cosine = 0.0
        nearest_task_id = None
        for train in train_tasks:
            train_text = task_text(train)
            train_tokens = tokenize(train_text)
            overlap = longest_shared_ngram(held_tokens, train_tokens, ngram_threshold)
            cosine = cosine_similarity(held_counter, Counter(train_tokens))
            if overlap > max_overlap or cosine > max_cosine:
                max_overlap = max(max_overlap, overlap)
                max_cosine = max(max_cosine, cosine)
                nearest_task_id = train["task_id"]
        violated = max_overlap >= ngram_threshold or max_cosine >= cosine_threshold
        if violated:
            violations += 1
        if held_out.get("source_mode") in {"programmatic", "hand-authored"}:
            time_shift_check = "not_required_synthetic_or_repo_authored_task"
        else:
            time_shift_check = "repo_artifact_window_requires_manual_review"
        findings.append(
            {
                "held_out_task_id": held_out["task_id"],
                "nearest_train_task_id": nearest_task_id,
                "longest_shared_ngram": max_overlap,
                "cosine_similarity": round(max_cosine, 4),
                "time_shift_check": time_shift_check,
                "violated": violated,
            }
        )
    return {
        "ngram_overlap_threshold": ngram_threshold,
        "embedding_similarity_threshold": cosine_threshold,
        "violations": violations,
        "findings": findings,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run contamination checks across Tenacious-Bench partitions.")
    parser.add_argument("--ngram-threshold", type=int, default=8)
    parser.add_argument("--cosine-threshold", type=float, default=0.85)
    args = parser.parse_args()

    train_tasks = load_tasks("train")
    held_out_tasks = load_tasks("held_out")
    report = compare_splits(train_tasks, held_out_tasks, args.ngram_threshold, args.cosine_threshold)
    report["comparison_scope"] = "held_out_vs_train"
    out_path = REPO_ROOT / "contamination_check.json"
    out_path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
