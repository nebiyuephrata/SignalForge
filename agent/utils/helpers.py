from datetime import UTC, datetime
from typing import Iterable


def utc_now() -> datetime:
    return datetime.now(UTC)


def compact_text(parts: Iterable[str]) -> str:
    return " ".join(part.strip() for part in parts if part and part.strip())
