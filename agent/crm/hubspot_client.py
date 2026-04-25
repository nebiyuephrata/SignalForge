from __future__ import annotations

from datetime import datetime, timezone
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
        if not email:
            return {"status": "skipped", "error": "missing_email"}
        if not self._credential:
            return self._offline_result("missing_api_key", properties)
        existing = self._search_contact(email)
        if existing.get("status") == "failed":
            if self._should_upsert_without_search(existing):
                return self._upsert_contact_by_email(email=email, properties=properties)
            return existing
        if existing.get("results"):
            return self._update_contact(str(existing["results"][0]["id"]), properties)
        return self._create_contact(properties)

    def update_contact_properties(self, *, contact_id: str, properties: dict[str, Any]) -> dict[str, Any]:
        if not contact_id:
            return {"status": "skipped", "error": "missing_contact_id"}
        if not self._credential:
            return self._offline_result("missing_api_key", properties)
        response = self._update_contact(contact_id, properties)
        missing_properties = self._missing_contact_properties(response)
        if missing_properties and self._ensure_contact_properties(missing_properties):
            return self._update_contact(contact_id, properties)
        return response

    def create_note(self, *, contact_id: str, body: str) -> dict[str, Any]:
        if not contact_id:
            return {"status": "skipped", "error": "missing_contact_id"}
        if not self._credential:
            return self._offline_result("missing_api_key", {"body": body})

        payload = {
            "properties": {
                "hs_note_body": body,
                "hs_timestamp": datetime.now(timezone.utc).isoformat(),
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

    def create_activity(self, *, contact_id: str, subject: str, body: str, channel: str) -> dict[str, Any]:
        return self.create_note(contact_id=contact_id, body=f"[{channel}] {subject}\n\n{body}")

    def _search_contact(self, email: str) -> dict[str, Any]:
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
        return self._request("POST", "/crm/v3/objects/contacts/search", json=payload)

    def _create_contact(self, properties: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/crm/v3/objects/contacts", json={"properties": properties})

    def _update_contact(self, contact_id: str, properties: dict[str, Any]) -> dict[str, Any]:
        return self._request("PATCH", f"/crm/v3/objects/contacts/{contact_id}", json={"properties": properties})

    def _upsert_contact_by_email(self, *, email: str, properties: dict[str, Any]) -> dict[str, Any]:
        payload = self._request(
            "POST",
            "/crm/v3/objects/contacts/batch/upsert",
            json={
                "inputs": [
                    {
                        "id": email,
                        "idProperty": "email",
                        "properties": properties,
                    }
                ]
            },
        )
        results = payload.get("results", [])
        if isinstance(results, list) and results:
            result = results[0]
            if isinstance(result, dict):
                result.setdefault("status", "success")
                return result
        return payload

    def _create_contact_property(self, definition: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/crm/v3/properties/contacts", json=definition)

    def _request(self, method: str, path: str, json: dict[str, Any]) -> dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self._credential}",
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
        except httpx.HTTPStatusError as exc:
            return {
                "status": "failed",
                "error": f"http_{exc.response.status_code}",
                "path": path,
                "response": self._safe_json(exc.response),
            }
        except httpx.HTTPError as exc:
            return {"status": "failed", "error": "transport_error", "detail": str(exc), "path": path}

        payload = self._safe_json(response)
        payload.setdefault("status", "success")
        return payload

    @staticmethod
    def _safe_json(response: httpx.Response) -> dict[str, Any]:
        try:
            body = response.json()
            return body if isinstance(body, dict) else {"payload": body}
        except ValueError:
            return {"text": response.text}

    @staticmethod
    def _offline_result(error: str, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "status": "offline_fallback",
            "error": error,
            "todo": "Set HUBSPOT_ACCESS_TOKEN or HUBSPOT_API_KEY and rerun the same lifecycle step to perform the real write.",
            "payload": payload,
        }

    @property
    def _credential(self) -> str:
        return self.settings.hubspot_access_token or self.settings.hubspot_api_key

    @staticmethod
    def _should_upsert_without_search(search_response: dict[str, Any]) -> bool:
        response = search_response.get("response", {})
        if not isinstance(response, dict):
            return False
        return (
            search_response.get("error") == "http_403"
            and response.get("category") == "MISSING_SCOPES"
        )

    @staticmethod
    def _missing_contact_properties(response: dict[str, Any]) -> list[str]:
        if response.get("error") != "http_400":
            return []
        payload = response.get("response", {})
        if not isinstance(payload, dict):
            return []

        missing: list[str] = []
        for error in payload.get("errors", []):
            if not isinstance(error, dict):
                continue
            if error.get("code") != "PROPERTY_DOESNT_EXIST":
                continue
            context = error.get("context", {})
            if not isinstance(context, dict):
                continue
            for property_name in context.get("propertyName", []):
                if isinstance(property_name, str) and property_name.startswith("signalforge_"):
                    missing.append(property_name)
        return sorted(set(missing))

    def _ensure_contact_properties(self, property_names: list[str]) -> bool:
        success = True
        for property_name in property_names:
            definition = self._contact_property_definition(property_name)
            if definition is None:
                success = False
                continue
            response = self._create_contact_property(definition)
            if response.get("status") == "failed":
                error = str(response.get("error", ""))
                category = str(response.get("response", {}).get("category", ""))
                if error != "http_409" and category != "CONFLICT":
                    success = False
        return success

    @staticmethod
    def _contact_property_definition(property_name: str) -> dict[str, Any] | None:
        definitions: dict[str, dict[str, str]] = {
            "signalforge_signal_confidence": {
                "label": "SignalForge Signal Confidence",
                "type": "number",
                "fieldType": "number",
            },
            "signalforge_ai_maturity": {
                "label": "SignalForge AI Maturity",
                "type": "number",
                "fieldType": "number",
            },
            "signalforge_ai_maturity_confidence": {
                "label": "SignalForge AI Maturity Confidence",
                "type": "string",
                "fieldType": "text",
            },
            "signalforge_company_size": {
                "label": "SignalForge Company Size",
                "type": "number",
                "fieldType": "number",
            },
            "signalforge_last_funding_round": {
                "label": "SignalForge Last Funding Round",
                "type": "string",
                "fieldType": "text",
            },
            "signalforge_funding_date": {
                "label": "SignalForge Funding Date",
                "type": "string",
                "fieldType": "text",
            },
            "signalforge_job_posts_current": {
                "label": "SignalForge Job Posts Current",
                "type": "number",
                "fieldType": "number",
            },
            "signalforge_job_posts_60d_ago": {
                "label": "SignalForge Job Posts 60d Ago",
                "type": "number",
                "fieldType": "number",
            },
            "signalforge_recent_layoffs": {
                "label": "SignalForge Recent Layoffs",
                "type": "number",
                "fieldType": "number",
            },
            "signalforge_recent_layoff_date": {
                "label": "SignalForge Recent Layoff Date",
                "type": "string",
                "fieldType": "text",
            },
            "signalforge_recent_leadership_change": {
                "label": "SignalForge Recent Leadership Change",
                "type": "string",
                "fieldType": "text",
            },
            "signalforge_recent_leadership_date": {
                "label": "SignalForge Recent Leadership Date",
                "type": "string",
                "fieldType": "text",
            },
            "signalforge_intent_level": {
                "label": "SignalForge Intent Level",
                "type": "string",
                "fieldType": "text",
            },
            "signalforge_last_event_at": {
                "label": "SignalForge Last Event At",
                "type": "string",
                "fieldType": "text",
            },
            "signalforge_next_action": {
                "label": "SignalForge Next Action",
                "type": "string",
                "fieldType": "text",
            },
            "signalforge_stage": {
                "label": "SignalForge Stage",
                "type": "string",
                "fieldType": "text",
            },
            "signalforge_qualification_status": {
                "label": "SignalForge Qualification Status",
                "type": "string",
                "fieldType": "text",
            },
            "signalforge_booking_url": {
                "label": "SignalForge Booking URL",
                "type": "string",
                "fieldType": "text",
            },
            "signalforge_last_booking_start": {
                "label": "SignalForge Last Booking Start",
                "type": "string",
                "fieldType": "text",
            },
            "signalforge_booking_event_type": {
                "label": "SignalForge Booking Event Type",
                "type": "string",
                "fieldType": "text",
            },
        }
        definition = definitions.get(property_name)
        if definition is None:
            return None
        return {
            "groupName": "contactinformation",
            "name": property_name,
            "label": definition["label"],
            "type": definition["type"],
            "fieldType": definition["fieldType"],
        }
