from __future__ import annotations

import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from training.preference_data_utils import build_preference_rows, load_tasks

BENCH_ROOT = REPO_ROOT / "tenacious_bench_v0.1"
OUT_ROOT = REPO_ROOT / "training_data" / "unsloth"


def export_split(split: str) -> dict[str, Any]:
    rows = build_preference_rows(
        load_tasks(BENCH_ROOT, split),
        split=split,
        normalize_dimensions=True,
        render_plain_strings=True,
    )
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    out_path = OUT_ROOT / f"preferences_{split}.jsonl"
    out_path.write_text("\n".join(json.dumps(row, ensure_ascii=True) for row in rows) + "\n")
    return {"split": split, "rows": len(rows), "output_path": str(out_path)}


def main() -> None:
    manifest = {
        "format": "unsloth_preference_bundle_v1",
        "splits": [
            export_split("train"),
            export_split("dev"),
            export_split("held_out"),
        ],
        "notes": [
            "prompt/chosen/rejected are plain strings for DPO/ORPO/SimPO trainers.",
            "sft_text is a ChatML-style text field for optional warm-start SFT on chosen responses.",
            "held_out export exists for final sealed evaluation and should stay untouched during tuning.",
        ],
    }
    manifest_path = OUT_ROOT / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
