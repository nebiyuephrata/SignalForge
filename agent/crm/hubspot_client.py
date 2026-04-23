from __future__ import annotations

from typing import Any, Callable

import httpx

from agent.utils.config import Settings, get_settings


class HubSpotClient:
    def __init__(
        self,
        settings: Settings | None = None,
        http_client_factory: Callable[[], httpx.Client] | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.http_client_factory = http_client_factory or (lambda: httpx.Client(timeout=20.0))

    def upsert_contact(self, *, email: str, properties: dict[str, Any]) -> dict[str, Any]:
        if not self.settings.hubspot_api_key:
            return {"status": "failed", "error": "missing_api_key"}
        existing = self._search_contact(email)
        if existing:
            return self._update_contact(existing["id"], properties)
        return self._create_contact(properties)

    def create_note(self, *, contact_id: str, body: str) -> dict[str, Any]:
        if not self.settings.hubspot_api_key:
            return {"status": "failed", "error": "missing_api_key"}

        payload = {
            "properties": {
                "hs_note_body": body,
            },
            "associations": [
                {
                    "to": {"id": contact_id},
                    "types": [
                        {
                            "associationCategory": "HUBSPOT_DEFINED",
                            "associationTypeId": 202,
                        }
                    ],
                }
            ],
        }
        return self._request("POST", "/crm/v3/objects/notes", json=payload)

    def _search_contact(self, email: str) -> dict[str, Any] | None:
        payload = {
            "filterGroups": [
                {
                    "filters": [
                        {"propertyName": "email", "operator": "EQ", "value": email},
                    ]
                }
            ],
            "limit": 1,
        }
        response = self._request("POST", "/crm/v3/objects/contacts/search", json=payload)
        results = response.get("results", [])
        return results[0] if isinstance(results, list) and results else None

    def _create_contact(self, properties: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/crm/v3/objects/contacts", json={"properties": properties})

    def _update_contact(self, contact_id: str, properties: dict[str, Any]) -> dict[str, Any]:
        return self._request("PATCH", f"/crm/v3/objects/contacts/{contact_id}", json={"properties": properties})

    def _request(self, method: str, path: str, json: dict[str, Any]) -> dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.settings.hubspot_api_key}",
            "Content-Type": "application/json",
        }
        try:
            with self.http_client_factory() as client:
                response = client.request(
                    method,
                    f"{self.settings.hubspot_base_url}{path}",
                    headers=headers,
                    json=json,
                )
                response.raise_for_status()
                payload = response.json()
                return payload if isinstance(payload, dict) else {"payload": payload}
        except httpx.HTTPError as exc:
            return {"status": "failed", "error": str(exc), "path": path}
