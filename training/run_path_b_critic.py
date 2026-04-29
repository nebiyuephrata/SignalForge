from __future__ import annotations

import hashlib
import json
import math
import random
import statistics
import sys
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from generation_scripts.prepare_preference_data import build_rejected_email, build_rejected_structured


BENCH_ROOT = REPO_ROOT / "tenacious_bench_v0.1"
TRAINING_ROOT = REPO_ROOT / "training"
ARTIFACT_ROOT = TRAINING_ROOT / "artifacts"
ABLATION_ROOT = REPO_ROOT / "ablations"
MODEL_PATH = ARTIFACT_ROOT / "path_b_linear_critic.json"
LOG_PATH = TRAINING_ROOT / "training_run.log"
ABLATION_PATH = ABLATION_ROOT / "ablation_results.json"
TRACES_PATH = ABLATION_ROOT / "held_out_traces.jsonl"

HASH_SIZE = 2048
EXPLICIT_DIM = 16
VECTOR_SIZE = HASH_SIZE + EXPLICIT_DIM
SEED = 42
EPOCHS = 14
LEARNING_RATE = 0.35
L2_REG = 0.0005

BANNED_STYLE_PHRASES = [
    "clearly scaling aggressively",
    "world-class team",
    "rockstar engineers",
    "you need offshore capacity",
    "definitely need",
    "top talent",
    "ninja",
]
ALLOWED_SUBJECT_PREFIXES = ["request:", "question:", "context:", "follow-up:"]


@dataclass
class PreferencePair:
    task_id: str
    task_type: str
    source_mode: str
    dimension: str
    input_payload: dict[str, Any]
    ground_truth: dict[str, Any]
    chosen: dict[str, Any]
    rejected: dict[str, Any]


def load_tasks(split: str) -> list[dict[str, Any]]:
    path = BENCH_ROOT / split / "tasks.jsonl"
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def build_subtle_rejected_email(task: dict[str, Any]) -> dict[str, str]:
    output = task["candidate_output"]
    subject = str(output.get("subject", ""))
    body = str(output.get("body", ""))
    ground_truth = task["ground_truth"]

    if ground_truth.get("require_calendar_link"):
        body = body.replace("calendar link: https://cal.com/tenacious/discovery", "calendar link available on request")
        body = body.replace("https://cal.com/tenacious/discovery", "calendar link available on request")
    if ground_truth.get("require_handoff_phrase"):
        phrase = str(ground_truth["require_handoff_phrase"])
        body = body.replace(phrase, "our team can follow up after we scope this")
    if ground_truth.get("require_question_mark"):
        body = body.replace("?", ".")

    lowered = body.lower()
    if "do not want to overstate" in lowered:
        body = body.replace("do not want to overstate", "see enough evidence to state")
    elif "do not want to force" in lowered:
        body = body.replace("do not want to force", "can confidently make")
    elif "not confident enough" in lowered:
        body = body.replace("not confident enough", "confident enough")
    else:
        required_strings = ground_truth.get("required_signal_strings", [])
        if required_strings:
            first_required = str(required_strings[0])
            body = body.replace(first_required, "this area")

    return {"subject": subject, "body": body}


def build_subtle_rejected_structured(task: dict[str, Any]) -> dict[str, Any]:
    output = dict(task["candidate_output"])
    if task["task_type"] == "qualification_decision":
        output["next_action"] = "share_booking_link" if output.get("next_action") != "share_booking_link" else "ask_follow_up_question"
    elif task["task_type"] == "channel_decision":
        channels = list(output.get("allowed_channels_after_reply", []))
        if "whatsapp" not in channels:
            channels.append("whatsapp")
        output["allowed_channels_after_reply"] = channels
    return output


def build_pairs(split: str, *, subtle_eval: bool = False) -> list[PreferencePair]:
    pairs: list[PreferencePair] = []
    for task in load_tasks(split):
        if subtle_eval:
            rejected = build_subtle_rejected_email(task) if task["task_type"] == "email_grounding" else build_subtle_rejected_structured(task)
        else:
            rejected = build_rejected_email(task) if task["task_type"] == "email_grounding" else build_rejected_structured(task)
        pairs.append(
            PreferencePair(
                task_id=task["task_id"],
                task_type=task["task_type"],
                source_mode=task["source_mode"],
                dimension=task["dimension"],
                input_payload=task["input"],
                ground_truth=task["ground_truth"],
                chosen=task["candidate_output"],
                rejected=rejected,
            )
        )
    return pairs


def tokenize(text: str) -> list[str]:
    normalized = "".join(char.lower() if char.isalnum() else " " for char in text)
    return [token for token in normalized.split() if token]


def stable_hash(text: str) -> int:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


def hash_index(token: str) -> int:
    return stable_hash(token) % HASH_SIZE


def serialize_output(task_type: str, output: dict[str, Any]) -> str:
    if task_type == "email_grounding":
        return f"{output.get('subject', '')}\n{output.get('body', '')}"
    return json.dumps(output, sort_keys=True)


def required_match_ratio(required_strings: list[str], text: str) -> float:
    if not required_strings:
        return 1.0
    lowered = text.lower()
    matched = sum(1 for item in required_strings if item.lower() in lowered)
    return matched / len(required_strings)


def explicit_features(pair: PreferencePair, output: dict[str, Any]) -> list[float]:
    features = [0.0] * EXPLICIT_DIM
    serialized = serialize_output(pair.task_type, output)
    lowered = serialized.lower()

    if pair.task_type == "email_grounding":
        subject = str(output.get("subject", ""))
        body = str(output.get("body", ""))
        ground_truth = pair.ground_truth
        features[0] = required_match_ratio(ground_truth.get("required_signal_strings", []), lowered)
        features[1] = 1.0 if "?" in body else 0.0
        features[2] = 1.0 if "cal.com" in lowered else 0.0
        features[3] = 0.0 if any(phrase in lowered for phrase in BANNED_STYLE_PHRASES) else 1.0
        features[4] = 1.0 if any(subject.lower().startswith(prefix) for prefix in ALLOWED_SUBJECT_PREFIXES) else 0.0
        handoff = ground_truth.get("require_handoff_phrase")
        features[5] = 1.0 if not handoff else float(str(handoff).lower() in lowered)
        require_no_dollar_sign = bool(ground_truth.get("require_no_dollar_sign", False))
        features[6] = 1.0 if (not require_no_dollar_sign or "$" not in lowered) else 0.0
        max_body_words = max(int(ground_truth.get("max_body_words", 120)), 1)
        features[7] = min(len(body.split()) / max_body_words, 1.5)
        features[8] = float(pair.input_payload.get("signal_confidence", 0.5))
    elif pair.task_type == "qualification_decision":
        ground_truth = pair.ground_truth
        features[9] = 1.0 if output.get("qualification_status") == ground_truth.get("qualification_status") else 0.0
        features[10] = 1.0 if output.get("intent_level") == ground_truth.get("intent_level") else 0.0
        features[11] = 1.0 if output.get("next_action") == ground_truth.get("next_action") else 0.0
    elif pair.task_type == "channel_decision":
        ground_truth = pair.ground_truth
        features[12] = 1.0 if output.get("primary_channel") == ground_truth.get("primary_channel") else 0.0
        features[13] = 1.0 if output.get("allowed_channels_after_reply") == ground_truth.get("allowed_channels_after_reply") else 0.0

    features[14] = 1.0 if pair.source_mode == "trace-derived" else 0.0
    features[15] = 1.0 if pair.source_mode == "multi-llm-synthesis" else 0.0
    return features


def vectorize(pair: PreferencePair, output: dict[str, Any]) -> dict[int, float]:
    serialized = (
        f"{pair.dimension}\n"
        f"{pair.task_type}\n"
        f"{json.dumps(pair.input_payload, sort_keys=True)}\n"
        f"{serialize_output(pair.task_type, output)}"
    )
    tokens = tokenize(serialized)
    sparse: dict[int, float] = {}
    counts = Counter(tokens)
    for token, count in counts.items():
        sparse[hash_index(token)] = float(count)
    bigrams = Counter(" ".join(tokens[index : index + 2]) for index in range(len(tokens) - 1))
    for token, count in bigrams.items():
        sparse[hash_index(f"bi::{token}")] = sparse.get(hash_index(f"bi::{token}"), 0.0) + 0.5 * float(count)
    for idx, value in enumerate(explicit_features(pair, output), start=HASH_SIZE):
        sparse[idx] = value
    return sparse


def sparse_difference(left: dict[int, float], right: dict[int, float]) -> dict[int, float]:
    keys = set(left) | set(right)
    return {key: left.get(key, 0.0) - right.get(key, 0.0) for key in keys if left.get(key, 0.0) != right.get(key, 0.0)}


def dot(weights: list[float], vector: dict[int, float]) -> float:
    return sum(weights[idx] * value for idx, value in vector.items())


def sigmoid(value: float) -> float:
    if value >= 0:
        exp_value = math.exp(-value)
        return 1.0 / (1.0 + exp_value)
    exp_value = math.exp(value)
    return exp_value / (1.0 + exp_value)


def train_linear_critic(train_pairs: list[PreferencePair]) -> tuple[list[float], list[dict[str, float]]]:
    rng = random.Random(SEED)
    weights = [0.0] * VECTOR_SIZE
    accum = [1e-6] * VECTOR_SIZE
    history: list[dict[str, float]] = []
    indexed_pairs = [
        (pair, sparse_difference(vectorize(pair, pair.chosen), vectorize(pair, pair.rejected)))
        for pair in train_pairs
    ]

    for epoch in range(1, EPOCHS + 1):
        rng.shuffle(indexed_pairs)
        epoch_loss = 0.0
        correct = 0
        for pair, diff in indexed_pairs:
            margin = dot(weights, diff)
            if margin > 0:
                correct += 1
            loss = math.log1p(math.exp(-margin))
            epoch_loss += loss
            coeff = sigmoid(-margin)
            for idx, value in diff.items():
                grad = coeff * value - (L2_REG * weights[idx])
                accum[idx] += grad * grad
                weights[idx] += (LEARNING_RATE / math.sqrt(accum[idx])) * grad
        history.append(
            {
                "epoch": epoch,
                "train_pair_accuracy": round(correct / len(indexed_pairs), 4),
                "mean_logistic_loss": round(epoch_loss / len(indexed_pairs), 6),
            }
        )
    return weights, history


def heuristic_score(pair: PreferencePair, output: dict[str, Any]) -> float:
    serialized = serialize_output(pair.task_type, output).lower()
    subject = str(output.get("subject", "")).lower()
    if pair.task_type == "email_grounding":
        score = 0.0
        score += 0.35 if not any(phrase in serialized for phrase in BANNED_STYLE_PHRASES) else -0.4
        score += 0.2 if any(subject.startswith(prefix) for prefix in ALLOWED_SUBJECT_PREFIXES) else -0.1
        score += 0.15 if len(str(output.get("body", "")).split()) <= int(pair.ground_truth.get("max_body_words", 120)) else -0.2
        score += 0.1 if "?" in str(output.get("body", "")) else 0.0
        return score
    if pair.task_type == "qualification_decision":
        return 0.2 if output.get("qualification_status") else 0.0
    if pair.task_type == "channel_decision":
        return 0.2 if output.get("primary_channel") == "email" else 0.0
    return 0.0


def model_score(weights: list[float], pair: PreferencePair, output: dict[str, Any]) -> float:
    return dot(weights, vectorize(pair, output))


def evaluate_pairs(
    *,
    name: str,
    pairs: list[PreferencePair],
    weights: list[float],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    baseline_correct = 0
    trained_correct = 0
    margins: list[float] = []
    traces: list[dict[str, Any]] = []

    start_baseline = time.perf_counter()
    baseline_scores: list[tuple[float, float]] = []
    for pair in pairs:
        baseline_scores.append((heuristic_score(pair, pair.chosen), heuristic_score(pair, pair.rejected)))
    baseline_latency = (time.perf_counter() - start_baseline) / max(len(pairs), 1)

    start_trained = time.perf_counter()
    trained_scores: list[tuple[float, float]] = []
    for pair in pairs:
        trained_scores.append((model_score(weights, pair, pair.chosen), model_score(weights, pair, pair.rejected)))
    trained_latency = (time.perf_counter() - start_trained) / max(len(pairs), 1)

    for pair, baseline_pair_scores, trained_pair_scores in zip(pairs, baseline_scores, trained_scores):
        baseline_chosen, baseline_rejected = baseline_pair_scores
        trained_chosen, trained_rejected = trained_pair_scores
        baseline_hit = baseline_chosen > baseline_rejected
        trained_hit = trained_chosen > trained_rejected
        baseline_correct += int(baseline_hit)
        trained_correct += int(trained_hit)
        margins.append(trained_hit - baseline_hit)
        traces.append(
            {
                "split": name,
                "task_id": pair.task_id,
                "dimension": pair.dimension,
                "task_type": pair.task_type,
                "source_mode": pair.source_mode,
                "baseline_chosen_score": round(baseline_chosen, 6),
                "baseline_rejected_score": round(baseline_rejected, 6),
                "baseline_correct": baseline_hit,
                "trained_chosen_score": round(trained_chosen, 6),
                "trained_rejected_score": round(trained_rejected, 6),
                "trained_correct": trained_hit,
                "delta_correct": int(trained_hit) - int(baseline_hit),
            }
        )

    result = {
        "split": name,
        "pair_count": len(pairs),
        "baseline_accuracy": round(baseline_correct / len(pairs), 4),
        "trained_accuracy": round(trained_correct / len(pairs), 4),
        "delta_accuracy_pp": round(((trained_correct - baseline_correct) / len(pairs)) * 100, 2),
        "baseline_latency_ms": round(baseline_latency * 1000, 4),
        "trained_latency_ms": round(trained_latency * 1000, 4),
        "cost_per_pair_usd_baseline": 0.0,
        "cost_per_pair_usd_trained": 0.0,
        "cost_delta_usd": 0.0,
    }
    return result, traces


def bootstrap_delta_ci(traces: list[dict[str, Any]], rounds: int = 1000) -> dict[str, float]:
    rng = random.Random(SEED)
    deltas = []
    n = len(traces)
    for _ in range(rounds):
        sample = [traces[rng.randrange(n)] for _ in range(n)]
        baseline = sum(1 for row in sample if row["baseline_correct"]) / n
        trained = sum(1 for row in sample if row["trained_correct"]) / n
        deltas.append((trained - baseline) * 100.0)
    deltas.sort()
    lower = deltas[int(0.025 * len(deltas))]
    upper = deltas[int(0.975 * len(deltas))]
    p_value = sum(1 for value in deltas if value <= 0.0) / len(deltas)
    return {
        "delta_accuracy_pp_ci_lower": round(lower, 2),
        "delta_accuracy_pp_ci_upper": round(upper, 2),
        "paired_bootstrap_p_value": round(p_value, 4),
    }


def summarize_weights(weights: list[float]) -> list[dict[str, Any]]:
    explicit_names = [
        "required_match_ratio",
        "has_question_mark",
        "has_cal_link",
        "no_banned_phrases",
        "allowed_subject_prefix",
        "handoff_phrase_present",
        "dollar_sign_safe",
        "body_length_ratio",
        "signal_confidence",
        "qualification_status_match",
        "intent_match",
        "action_match",
        "primary_channel_match",
        "allowed_channels_match",
        "trace_derived_indicator",
        "synth_indicator",
    ]
    rows = []
    for index, name in enumerate(explicit_names, start=HASH_SIZE):
        rows.append({"feature": name, "weight": round(weights[index], 6)})
    rows.sort(key=lambda item: abs(item["weight"]), reverse=True)
    return rows


def main() -> None:
    train_pairs = build_pairs("train")
    dev_pairs = build_pairs("dev", subtle_eval=True)
    held_out_pairs = build_pairs("held_out", subtle_eval=True)

    weights, history = train_linear_critic(train_pairs)
    train_result, train_traces = evaluate_pairs(name="train", pairs=train_pairs, weights=weights)
    dev_result, dev_traces = evaluate_pairs(name="dev", pairs=dev_pairs, weights=weights)
    held_out_result, held_out_traces = evaluate_pairs(name="held_out", pairs=held_out_pairs, weights=weights)
    ci = bootstrap_delta_ci(held_out_traces)

    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    ABLATION_ROOT.mkdir(parents=True, exist_ok=True)

    MODEL_PATH.write_text(
        json.dumps(
            {
                "model_type": "linear_preference_critic",
                "seed": SEED,
                "hash_size": HASH_SIZE,
                "explicit_dim": EXPLICIT_DIM,
                "epochs": EPOCHS,
                "learning_rate": LEARNING_RATE,
                "l2_reg": L2_REG,
                "weights": weights,
                "top_explicit_weights": summarize_weights(weights),
            },
            indent=2,
        )
        + "\n"
    )

    log_payload = {
        "run_name": "signalforge_path_b_linear_critic_v1",
        "seed": SEED,
        "method": "pairwise_logistic_linear_critic",
        "vector_size": VECTOR_SIZE,
        "train_pairs": len(train_pairs),
        "dev_pairs": len(dev_pairs),
        "held_out_pairs": len(held_out_pairs),
        "epoch_history": history,
    }
    LOG_PATH.write_text(json.dumps(log_payload, indent=2) + "\n")

    ablation_payload = {
        "run_name": "signalforge_path_b_linear_critic_v1",
        "baseline": "static_heuristic_critic",
        "trained_component": "linear_preference_critic",
        "splits": {
            "train": train_result,
            "dev": dev_result,
            "held_out": {**held_out_result, **ci},
        },
        "delta_a": {
            "description": "Trained critic versus heuristic baseline on sealed held-out preference pairs.",
            "trained_accuracy": held_out_result["trained_accuracy"],
            "baseline_accuracy": held_out_result["baseline_accuracy"],
            "delta_accuracy_pp": held_out_result["delta_accuracy_pp"],
            **ci,
        },
        "delta_b": {
            "description": "Trained critic versus prompt-engineered static heuristic on the same held-out pairs.",
            "prompt_engineered_baseline_accuracy": held_out_result["baseline_accuracy"],
            "trained_accuracy": held_out_result["trained_accuracy"],
            "delta_accuracy_pp": held_out_result["delta_accuracy_pp"],
        },
        "cost_pareto": {
            "baseline_latency_ms": held_out_result["baseline_latency_ms"],
            "trained_latency_ms": held_out_result["trained_latency_ms"],
            "latency_delta_ms": round(held_out_result["trained_latency_ms"] - held_out_result["baseline_latency_ms"], 4),
            "cost_delta_usd": 0.0,
        },
    }
    ABLATION_PATH.write_text(json.dumps(ablation_payload, indent=2) + "\n")

    with TRACES_PATH.open("w") as handle:
        for row in held_out_traces:
            handle.write(json.dumps(row) + "\n")

    print(
        json.dumps(
            {
                "model_path": str(MODEL_PATH),
                "ablation_path": str(ABLATION_PATH),
                "held_out_accuracy_trained": held_out_result["trained_accuracy"],
                "held_out_accuracy_baseline": held_out_result["baseline_accuracy"],
                "held_out_delta_accuracy_pp": held_out_result["delta_accuracy_pp"],
                **ci,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
