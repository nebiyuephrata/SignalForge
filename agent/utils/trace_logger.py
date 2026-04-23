from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path


def append_jsonl_log(path: str, payload: dict[str, object]) -> None:
    log_path = Path(path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    enriched_payload = {
        "timestamp": datetime.now(UTC).isoformat(),
        **payload,
    }
    with open(log_path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(enriched_payload) + "\n")


def write_json(path: str, payload: dict[str, object]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
