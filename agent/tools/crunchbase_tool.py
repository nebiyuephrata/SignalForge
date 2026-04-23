from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path


class CrunchbaseTool:
    def __init__(self, dataset_path: str | None = None) -> None:
        if dataset_path is None:
            dataset_path = str(Path(__file__).resolve().parents[2] / "data" / "crunchbase_sample.json")
        self.dataset_path = dataset_path

    @lru_cache(maxsize=1)
    def load_dataset(self) -> list[dict[str, object]]:
        with open(self.dataset_path, "r", encoding="utf-8") as handle:
            return json.load(handle)

    def list_companies(self) -> list[dict[str, object]]:
        return list(self.load_dataset())

    def get_company_by_name(self, name: str) -> dict[str, object] | None:
        normalized = name.strip().lower()
        for company in self.load_dataset():
            if str(company.get("company_name", "")).strip().lower() == normalized:
                return company
        return None
