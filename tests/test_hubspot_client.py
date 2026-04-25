import httpx
import json

from agent.crm.hubspot_client import HubSpotClient
from agent.utils.config import Settings


def test_hubspot_client_prefers_access_token_for_auth() -> None:
    captured_headers: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_headers["authorization"] = request.headers.get("Authorization", "")
        return httpx.Response(200, json={"results": []}, request=request)

    settings = Settings.model_construct(
        hubspot_api_key="legacy-api-key",
        hubspot_access_token="pat-live-access-token",
    )
    client = HubSpotClient(
        settings=settings,
        http_client_factory=lambda: httpx.Client(transport=httpx.MockTransport(handler)),
    )

    client.upsert_contact(email="smoke@example.com", properties={"email": "smoke@example.com"})

    assert captured_headers["authorization"] == "Bearer pat-live-access-token"


def test_hubspot_client_falls_back_to_api_key_when_access_token_missing() -> None:
    captured_headers: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_headers["authorization"] = request.headers.get("Authorization", "")
        return httpx.Response(200, json={"results": []}, request=request)

    settings = Settings.model_construct(
        hubspot_api_key="legacy-api-key",
        hubspot_access_token="",
    )
    client = HubSpotClient(
        settings=settings,
        http_client_factory=lambda: httpx.Client(transport=httpx.MockTransport(handler)),
    )

    client.upsert_contact(email="smoke@example.com", properties={"email": "smoke@example.com"})

    assert captured_headers["authorization"] == "Bearer legacy-api-key"


def test_hubspot_client_upserts_by_email_when_search_is_blocked_by_missing_read_scopes() -> None:
    requests: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append((request.method, request.url.path))
        if request.url.path.endswith("/search"):
            return httpx.Response(
                403,
                json={
                    "status": "error",
                    "category": "MISSING_SCOPES",
                },
                request=request,
            )
        return httpx.Response(
            200,
            json={
                "status": "COMPLETE",
                "results": [{"id": "contact-123"}],
            },
            request=request,
        )

    settings = Settings.model_construct(hubspot_access_token="pat-live-access-token")
    client = HubSpotClient(
        settings=settings,
        http_client_factory=lambda: httpx.Client(transport=httpx.MockTransport(handler)),
    )

    result = client.upsert_contact(email="smoke@example.com", properties={"email": "smoke@example.com"})

    assert result["id"] == "contact-123"
    assert requests == [
        ("POST", "/crm/v3/objects/contacts/search"),
        ("POST", "/crm/v3/objects/contacts/batch/upsert"),
    ]


def test_hubspot_client_note_payload_includes_timestamp() -> None:
    captured_payload: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_payload
        captured_payload = json.loads(request.content.decode("utf-8"))
        return httpx.Response(200, json={"id": "note-123"}, request=request)

    settings = Settings.model_construct(hubspot_access_token="pat-live-access-token")
    client = HubSpotClient(
        settings=settings,
        http_client_factory=lambda: httpx.Client(transport=httpx.MockTransport(handler)),
    )

    client.create_note(contact_id="contact-123", body="hello")

    properties = captured_payload["properties"]
    assert properties["hs_note_body"] == "hello"
    assert properties["hs_timestamp"]


def test_hubspot_client_creates_missing_signalforge_properties_then_retries_update() -> None:
    requests: list[tuple[str, str, dict[str, object]]] = []
    patch_calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal patch_calls
        payload = json.loads(request.content.decode("utf-8"))
        requests.append((request.method, request.url.path, payload))

        if request.method == "PATCH" and request.url.path == "/crm/v3/objects/contacts/contact-123":
            patch_calls += 1
            if patch_calls == 1:
                return httpx.Response(
                    400,
                    json={
                        "status": "error",
                        "category": "VALIDATION_ERROR",
                        "errors": [
                            {
                                "message": "Property \"signalforge_stage\" does not exist",
                                "code": "PROPERTY_DOESNT_EXIST",
                                "context": {"propertyName": ["signalforge_stage"]},
                            }
                        ],
                    },
                    request=request,
                )
            return httpx.Response(200, json={"id": "contact-123"}, request=request)

        if request.method == "POST" and request.url.path == "/crm/v3/properties/contacts":
            return httpx.Response(201, json={"name": payload["name"]}, request=request)

        raise AssertionError(f"Unexpected request: {request.method} {request.url.path}")

    settings = Settings.model_construct(hubspot_access_token="pat-live-access-token")
    client = HubSpotClient(
        settings=settings,
        http_client_factory=lambda: httpx.Client(transport=httpx.MockTransport(handler)),
    )

    result = client.update_contact_properties(
        contact_id="contact-123",
        properties={"signalforge_stage": "email_sent"},
    )

    assert result["id"] == "contact-123"
    assert requests == [
        ("PATCH", "/crm/v3/objects/contacts/contact-123", {"properties": {"signalforge_stage": "email_sent"}}),
        (
            "POST",
            "/crm/v3/properties/contacts",
            {
                "groupName": "contactinformation",
                "name": "signalforge_stage",
                "label": "SignalForge Stage",
                "type": "string",
                "fieldType": "text",
            },
        ),
        ("PATCH", "/crm/v3/objects/contacts/contact-123", {"properties": {"signalforge_stage": "email_sent"}}),
    ]
