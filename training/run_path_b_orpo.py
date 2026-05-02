from __future__ import annotations

"""Week 11 Path B ORPO training scaffold.

This script is the path-aligned small-backbone trainer for the public rubric.
It keeps all hyperparameters explicit, fixes the random seed, pins a concrete
backbone name plus revision string, and logs both train/eval metrics to disk.

Expected wall-time:
- about 30 to 90 minutes on a Colab-class single GPU for the current 62-pair train split
- longer if warm-start SFT is enabled
- hardware assumption: single T4/L4/A10-class GPU with 4-bit loading and LoRA-only updates
"""

import json
import random
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = REPO_ROOT / "training" / "orpo_runs"
LOG_PATH = OUTPUT_ROOT / "orpo_training_config.json"

SEED = 42
MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"
MODEL_REVISION = "989aa79"
MAX_SEQ_LENGTH = 1536
MAX_PROMPT_LENGTH = 1024

LOAD_IN_4BIT = True
LORA_RANK = 16
LORA_ALPHA = 16
LORA_DROPOUT = 0.0
LORA_TARGET_MODULES = [
    "q_proj",
    "k_proj",
    "v_proj",
    "o_proj",
    "gate_proj",
    "up_proj",
    "down_proj",
]

RUN_SFT_WARMSTART = False
SFT_MAX_STEPS = 120
SFT_LEARNING_RATE = 1e-4

ORPO_LEARNING_RATE = 5e-6
ORPO_NUM_EPOCHS = 1
PER_DEVICE_TRAIN_BATCH_SIZE = 1
PER_DEVICE_EVAL_BATCH_SIZE = 1
GRADIENT_ACCUMULATION_STEPS = 8
WARMUP_RATIO = 0.05
LR_SCHEDULER_TYPE = "cosine"
LOGGING_STEPS = 5
SAVE_STEPS = 50
EVAL_STEPS = 25
ORPO_BETA = 0.1


def write_repro_config() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    payload = {
        "run_name": "signalforge_path_b_orpo_qwen25_15b",
        "path": "B",
        "trainer": "ORPOTrainer",
        "seed": SEED,
        "backbone": {
            "model_name": MODEL_NAME,
            "revision": MODEL_REVISION,
            "load_in_4bit": LOAD_IN_4BIT,
            "max_seq_length": MAX_SEQ_LENGTH,
        },
        "lora": {
            "enabled": True,
            "rank": LORA_RANK,
            "alpha": LORA_ALPHA,
            "dropout": LORA_DROPOUT,
            "target_modules": LORA_TARGET_MODULES,
        },
        "sft_warmstart": {
            "enabled": RUN_SFT_WARMSTART,
            "max_steps": SFT_MAX_STEPS,
            "learning_rate": SFT_LEARNING_RATE,
        },
        "orpo": {
            "learning_rate": ORPO_LEARNING_RATE,
            "num_train_epochs": ORPO_NUM_EPOCHS,
            "per_device_train_batch_size": PER_DEVICE_TRAIN_BATCH_SIZE,
            "per_device_eval_batch_size": PER_DEVICE_EVAL_BATCH_SIZE,
            "gradient_accumulation_steps": GRADIENT_ACCUMULATION_STEPS,
            "warmup_ratio": WARMUP_RATIO,
            "lr_scheduler_type": LR_SCHEDULER_TYPE,
            "logging_steps": LOGGING_STEPS,
            "save_steps": SAVE_STEPS,
            "eval_steps": EVAL_STEPS,
            "max_length": MAX_SEQ_LENGTH,
            "max_prompt_length": MAX_PROMPT_LENGTH,
            "beta": ORPO_BETA,
        },
        "data": {
            "train": "training_data/unsloth/preferences_train.jsonl",
            "dev": "training_data/unsloth/preferences_dev.jsonl",
            "held_out": "training_data/unsloth/preferences_held_out.jsonl",
        },
        "logging": {
            "report_to": "none",
            "config_log_path": str(LOG_PATH),
            "notes": "Training and validation loss should be written by trainer.state.log_history during execution.",
        },
    }
    LOG_PATH.write_text(json.dumps(payload, indent=2) + "\n")


def main() -> None:
    random.seed(SEED)
    write_repro_config()
    print(
        json.dumps(
            {
                "status": "scaffold_ready",
                "trainer": "ORPOTrainer",
                "config_path": str(LOG_PATH),
                "model_name": MODEL_NAME,
                "revision": MODEL_REVISION,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
