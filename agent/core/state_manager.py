from __future__ import annotations

import json
from pathlib import Path
from threading import Lock

from agent.core.models import LeadLifecycleState, LifecycleActivity, utc_now_iso


class ProspectStateStore:
    """Persist lightweight lead state outside the handlers.

    The current repository runs locally without a database-backed workflow engine.
    A file store keeps the behavior deterministic for tests and easy to inspect
    for inheriting engineers. The exact next production step is to replace this
    with Postgres or Redis-backed state plus optimistic locking.
    """

    def __init__(self, path: str | None = None) -> None:
        default_path = Path(__file__).resolve().parents[2] / "outputs" / "prospect_state.json"
        self.path = Path(path) if path else default_path
        self._lock = Lock()

    def get(self, lead_key: str, *, company_name: str, contact_email: str | None = None, phone_number: str | None = None) -> LeadLifecycleState:
        with self._lock:
            payload = self._load()
            existing = payload.get(lead_key)
            if existing is None:
                existing = self._find_matching_state(
                    payload,
                    company_name=company_name,
                    contact_email=contact_email,
                    phone_number=phone_number,
                )
            if existing is not None:
                state = LeadLifecycleState.model_validate(existing)
                if contact_email and not state.contact_email:
                    state.contact_email = contact_email
                if phone_number and not state.phone_number:
                    state.phone_number = phone_number
                return state
            return LeadLifecycleState(
                lead_key=lead_key,
                company_name=company_name,
                contact_email=contact_email,
                phone_number=phone_number,
            )

    def save(self, state: LeadLifecycleState) -> LeadLifecycleState:
        with self._lock:
            payload = self._load()
            state.updated_at = utc_now_iso()
            payload[state.lead_key] = state.model_dump()
            self._write(payload)
        return state

    def append_activity(self, state: LeadLifecycleState, activity: LifecycleActivity) -> LeadLifecycleState:
        state.activities.append(activity)
        return self.save(state)

    def _load(self) -> dict[str, object]:
        if not self.path.exists():
            return {}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            # If local state is corrupted, we fail safe by starting from a clean map
            # instead of blocking all outbound routing.
            return {}

    def _write(self, payload: dict[str, object]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @staticmethod
    def _find_matching_state(
        payload: dict[str, object],
        *,
        company_name: str,
        contact_email: str | None,
        phone_number: str | None,
    ) -> dict[str, object] | None:
        normalized_company = company_name.strip().lower()
        normalized_email = (contact_email or "").strip().lower()
        normalized_phone = (phone_number or "").strip()
        if not normalized_email and not normalized_phone:
            return None

        for candidate in payload.values():
            if not isinstance(candidate, dict):
                continue
            state = LeadLifecycleState.model_validate(candidate)
            if state.company_name.strip().lower() != normalized_company:
                continue
            if normalized_email and state.contact_email and state.contact_email.strip().lower() == normalized_email:
                return candidate
            if normalized_phone and state.phone_number and state.phone_number.strip() == normalized_phone:
                return candidate
        return None
