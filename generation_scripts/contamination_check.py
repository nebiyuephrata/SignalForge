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


def corpus_ngram_counts(tasks: list[dict[str, Any]], n: int) -> Counter[tuple[str, ...]]:
    counts: Counter[tuple[str, ...]] = Counter()
    for task in tasks:
        counts.update(ngrams(tokenize(task_text(task)), n))
    return counts


def cosine_similarity(left: Counter[str], right: Counter[str]) -> float:
    keys = set(left) | set(right)
    numerator = sum(left[key] * right[key] for key in keys)
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)


def cheap_embedding_vector(text: str, width: int = 256) -> list[float]:
    """Cheap local embedding surrogate using token and trigram hashing.

    This is intentionally lightweight and reproducible in-repo. When a stronger
    embedding model is available, this function is the one intended to swap.
    """
    vector = [0.0] * width
    normalized = text.lower()
    tokens = tokenize(normalized)
    for token in tokens:
        vector[hash(f"tok::{token}") % width] += 1.0
    compact = "".join(char if char.isalnum() else " " for char in normalized)
    for idx in range(max(len(compact) - 2, 0)):
        trigram = compact[idx : idx + 3]
        vector[hash(f"tri::{trigram}") % width] += 0.25
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]


def dense_cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        raise ValueError("Embedding vectors must be the same width.")
    numerator = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
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
    reference_tasks: list[dict[str, Any]],
    held_out_tasks: list[dict[str, Any]],
    ngram_threshold: int,
    cosine_threshold: float,
    split_name: str,
    boilerplate_ngram_cutoff: int = 3,
    embedding_width: int = 256,
) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    violations = 0
    global_ngrams = corpus_ngram_counts(reference_tasks + held_out_tasks, ngram_threshold)
    for held_out in held_out_tasks:
        held_text = task_text(held_out)
        held_tokens = tokenize(held_text)
        held_counter = Counter(held_tokens)
        held_embedding = cheap_embedding_vector(held_text, width=embedding_width)
        max_overlap = 0
        max_sparse_cosine = 0.0
        max_embedding_cosine = 0.0
        nearest_task_id = None
        for reference in reference_tasks:
            reference_text = task_text(reference)
            reference_tokens = tokenize(reference_text)
            raw_overlap = ngrams(held_tokens, ngram_threshold) & ngrams(reference_tokens, ngram_threshold)
            filtered_overlap = {
                gram
                for gram in raw_overlap
                if global_ngrams[gram] <= boilerplate_ngram_cutoff
            }
            overlap = ngram_threshold if filtered_overlap else 0
            sparse_cosine = cosine_similarity(held_counter, Counter(reference_tokens))
            embedding_cosine = dense_cosine_similarity(
                held_embedding,
                cheap_embedding_vector(reference_text, width=embedding_width),
            )
            if overlap > max_overlap or sparse_cosine > max_sparse_cosine or embedding_cosine > max_embedding_cosine:
                max_overlap = max(max_overlap, overlap)
                max_sparse_cosine = max(max_sparse_cosine, sparse_cosine)
                max_embedding_cosine = max(max_embedding_cosine, embedding_cosine)
                nearest_task_id = reference["task_id"]
        violated = max_overlap >= ngram_threshold or max_embedding_cosine >= cosine_threshold
        if violated:
            violations += 1
        if held_out.get("source_mode") in {"programmatic", "hand-authored"}:
            time_shift_check = "not_required_synthetic_or_repo_authored_task"
        else:
            time_shift_check = "repo_artifact_window_requires_manual_review"
        findings.append(
            {
                "held_out_task_id": held_out["task_id"],
                f"nearest_{split_name}_task_id": nearest_task_id,
                "longest_shared_ngram": max_overlap,
                "lexical_cosine_similarity": round(max_sparse_cosine, 4),
                "embedding_cosine_similarity": round(max_embedding_cosine, 4),
                "time_shift_check": time_shift_check,
                "violated": violated,
            }
        )
    return {
        "comparison_scope": f"held_out_vs_{split_name}",
        "ngram_overlap_threshold": ngram_threshold,
        "boilerplate_ngram_cutoff": boilerplate_ngram_cutoff,
        "embedding_similarity_threshold": cosine_threshold,
        "embedding_width": embedding_width,
        "embedding_model": "cheap_local_hashing_embedding_v1",
        "violations": violations,
        "findings": findings,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run contamination checks across Tenacious-Bench partitions.")
    parser.add_argument("--ngram-threshold", type=int, default=8)
    parser.add_argument("--cosine-threshold", type=float, default=0.85)
    parser.add_argument("--boilerplate-ngram-cutoff", type=int, default=3)
    parser.add_argument("--embedding-width", type=int, default=256)
    args = parser.parse_args()

    train_tasks = load_tasks("train")
    dev_tasks = load_tasks("dev")
    held_out_tasks = load_tasks("held_out")
    report = {
        "held_out_vs_train": compare_splits(
            train_tasks,
            held_out_tasks,
            args.ngram_threshold,
            args.cosine_threshold,
            "train",
            boilerplate_ngram_cutoff=args.boilerplate_ngram_cutoff,
            embedding_width=args.embedding_width,
        ),
        "held_out_vs_dev": compare_splits(
            dev_tasks,
            held_out_tasks,
            args.ngram_threshold,
            args.cosine_threshold,
            "dev",
            boilerplate_ngram_cutoff=args.boilerplate_ngram_cutoff,
            embedding_width=args.embedding_width,
        ),
    }
    out_path = REPO_ROOT / "contamination_check.json"
    out_path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
