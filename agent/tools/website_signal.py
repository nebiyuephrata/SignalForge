from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from agent.core.models import WebsiteBehaviorSignal, WebsiteVisitEvent


class WebsiteSignalStore:
    """Persist and summarize website visits as deterministic behavioral signals."""

    def __init__(self, path: str | None = None) -> None:
        default_path = Path(__file__).resolve().parents[2] / "logs" / "website_visits.jsonl"
        self.path = Path(path) if path else default_path

    def record_visit(self, event: WebsiteVisitEvent) -> WebsiteVisitEvent:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event.model_dump()) + "\n")
        return event

    def recent_visits(
        self,
        *,
        company_name: str,
        contact_email: str | None = None,
        lookback_days: int = 30,
    ) -> list[WebsiteVisitEvent]:
        if not self.path.exists():
            return []
        cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
        visits: list[WebsiteVisitEvent] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            payload = json.loads(line)
            event = WebsiteVisitEvent.model_validate(payload)
            if event.company_name.strip().lower() != company_name.strip().lower():
                continue
            if contact_email and (event.contact_email or "").strip().lower() != contact_email.strip().lower():
                continue
            try:
                event_time = datetime.fromisoformat(event.timestamp.replace("Z", "+00:00"))
            except ValueError:
                continue
            if event_time >= cutoff:
                visits.append(event)
        visits.sort(key=lambda item: item.timestamp)
        return visits

    def behavioral_signal(
        self,
        *,
        company_name: str,
        contact_email: str | None = None,
    ) -> WebsiteBehaviorSignal | None:
        visits = self.recent_visits(company_name=company_name, contact_email=contact_email)
        if not visits:
            return None
        recent_pages = list(dict.fromkeys(event.page_visited for event in visits[-5:]))
        last_visit = visits[-1]
        high_intent = any(page.lower() in {"/pricing", "/demo", "/book", "/case-studies"} for page in recent_pages)
        confidence = 0.82 if high_intent else 0.64 if len(visits) >= 2 else 0.48
        return WebsiteBehaviorSignal(
            visit_count=len(visits),
            recent_pages=recent_pages,
            last_visit_at=last_visit.timestamp,
            follow_up_recommended=high_intent,
            confidence=confidence,
        )
