from pathlib import Path
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@pytest.fixture(autouse=True)
def patch_openrouter_for_tests(monkeypatch):
    from agent.llm.client import LLMClientResponse

    def fake_chat_json(self, **kwargs):  # noqa: ANN001, ANN202
        content = {
            "subject": "SignalForge test outreach",
            "body": "It looks like hiring activity may be moving. Is that directionally right?",
            "claims_used": ["funding_event", "job_post_velocity"],
        }
        metadata = kwargs.get("metadata", {})
        company_name = metadata.get("company_name", "this company")
        content["subject"] = f"{company_name}: signal review"
        content["body"] = f"It looks like {company_name} may be seeing hiring movement. Is that directionally right?"
        return LLMClientResponse(
            content=content,
            model="test/fake-openrouter",
            usage={"input": 12, "output": 18, "total": 30},
            cost_details={},
            latency_ms=1,
            trace_id="test-trace-id",
            trace_url="http://trace.local/test-trace-id",
            cached=False,
            prompt_snapshot=kwargs,
        )

    monkeypatch.setattr("agent.llm.client.OpenRouterClient.chat_json", fake_chat_json)
