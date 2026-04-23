from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

import httpx
from langfuse import Langfuse

from agent.utils.config import Settings, get_settings
from agent.utils.logger import get_logger

logger = get_logger(__name__)


class OpenRouterClientError(RuntimeError):
    """Raised when OpenRouter generation fails."""


@dataclass
class LLMClientResponse:
    content: dict[str, Any]
    model: str
    usage: dict[str, int]
    cost_details: dict[str, float]
    latency_ms: int
    trace_id: str
    trace_url: str | None
    cached: bool
    prompt_snapshot: dict[str, Any]


class OpenRouterClient:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._cache: dict[str, LLMClientResponse] = {}
        self._langfuse = self._build_langfuse_client()

    def chat_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        prompt_name: str,
        temperature: float = 0.4,
        max_tokens: int | None = None,
        metadata: dict[str, str] | None = None,
        strict_mode: bool = False,
    ) -> LLMClientResponse:
        if not self.settings.openrouter_api_key:
            raise OpenRouterClientError("OPENROUTER_API_KEY is not configured.")

        bounded_temperature = min(max(temperature, 0.3), 0.5)
        bounded_max_tokens = min(max_tokens or self.settings.openrouter_max_tokens, self.settings.openrouter_max_tokens)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        prompt_snapshot = {
            "messages": messages,
            "temperature": bounded_temperature,
            "max_tokens": bounded_max_tokens,
            "strict_mode": strict_mode,
            "metadata": metadata or {},
        }
        cache_key = json.dumps(
            {
                "primary_model": self.settings.openrouter_model,
                "fallback_model": self.settings.openrouter_fallback_model,
                **prompt_snapshot,
            },
            sort_keys=True,
        )
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            return LLMClientResponse(**{**cached.__dict__, "cached": True})

        trace_id = self._create_trace_id()
        trace_url = self._trace_url(trace_id)
        last_error: Exception | None = None

        for model_name in (self.settings.openrouter_model, self.settings.openrouter_fallback_model):
            for attempt in range(3):
                started = time.perf_counter()
                payload = {
                    "model": model_name,
                    "messages": messages,
                    "temperature": bounded_temperature,
                    "max_tokens": bounded_max_tokens,
                    "response_format": {"type": "json_object"},
                    "metadata": metadata or {},
                    "trace": {
                        "trace_id": trace_id,
                        "trace_name": "signalforge-run-prospect",
                        "generation_name": prompt_name,
                    },
                }
                try:
                    with self._langfuse_generation(
                        trace_id=trace_id,
                        prompt_name=prompt_name,
                        model_name=model_name,
                        prompt_snapshot=prompt_snapshot,
                    ) as generation:
                        response = self._post(payload)
                        latency_ms = int((time.perf_counter() - started) * 1000)
                        body = response.json()
                        content = self._parse_json_content(body)
                        usage = self._extract_usage(body)
                        cost_details = self._extract_cost_details(body)
                        generation.update(
                            output=content,
                            model=model_name,
                            usage_details=usage or None,
                            cost_details=cost_details or None,
                            metadata={
                                "latency_ms": latency_ms,
                                "response_id": str(body.get("id", "")),
                                "cached": False,
                            },
                        )
                        result = LLMClientResponse(
                            content=content,
                            model=model_name,
                            usage=usage,
                            cost_details=cost_details,
                            latency_ms=latency_ms,
                            trace_id=trace_id,
                            trace_url=trace_url,
                            cached=False,
                            prompt_snapshot=prompt_snapshot,
                        )
                        self._cache[cache_key] = result
                        self._flush_langfuse()
                        return result
                except Exception as exc:  # noqa: BLE001
                    last_error = exc
                    logger.warning(
                        "OpenRouter request failed for model=%s attempt=%s prompt=%s: %s",
                        model_name,
                        attempt + 1,
                        prompt_name,
                        exc,
                    )
                    if attempt == 2:
                        break

        raise OpenRouterClientError(f"OpenRouter generation failed: {last_error}") from last_error

    def _post(self, payload: dict[str, Any]) -> httpx.Response:
        headers = {
            "Authorization": f"Bearer {self.settings.openrouter_api_key}",
            "Content-Type": "application/json",
        }
        with httpx.Client(timeout=self.settings.openrouter_timeout_seconds) as client:
            response = client.post(
                f"{self.settings.openrouter_base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            return response

    def _parse_json_content(self, body: dict[str, Any]) -> dict[str, Any]:
        try:
            raw_content = body["choices"][0]["message"]["content"]
            if isinstance(raw_content, dict):
                return raw_content
            return json.loads(raw_content)
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise OpenRouterClientError("OpenRouter response did not contain valid JSON output.") from exc

    def _extract_usage(self, body: dict[str, Any]) -> dict[str, int]:
        usage = body.get("usage", {})
        return {
            "input": int(usage.get("prompt_tokens", 0) or 0),
            "output": int(usage.get("completion_tokens", 0) or 0),
            "total": int(usage.get("total_tokens", 0) or 0),
        }

    def _extract_cost_details(self, body: dict[str, Any]) -> dict[str, float]:
        candidates = [
            body.get("cost"),
            body.get("cost_usd"),
            body.get("total_cost"),
            body.get("usage", {}).get("cost"),
            body.get("usage", {}).get("cost_usd"),
        ]
        for candidate in candidates:
            if isinstance(candidate, (int, float)):
                return {"estimated_cost_usd": float(candidate)}
        return {}

    def _build_langfuse_client(self) -> Langfuse | None:
        if not (self.settings.langfuse_public_key and self.settings.langfuse_secret_key):
            return None
        if not self._langfuse_host_reachable():
            logger.warning("Langfuse host is unreachable. Continuing without trace export.")
            return None
        try:
            return Langfuse(
                public_key=self.settings.langfuse_public_key,
                secret_key=self.settings.langfuse_secret_key,
                host=self.settings.langfuse_host,
                environment=self.settings.app_env,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Langfuse client initialization failed: %s", exc)
            return None

    def _langfuse_host_reachable(self) -> bool:
        try:
            with httpx.Client(timeout=1.0) as client:
                client.get(self.settings.langfuse_host)
            return True
        except Exception:  # noqa: BLE001
            return False

    def _langfuse_generation(
        self,
        *,
        trace_id: str,
        prompt_name: str,
        model_name: str,
        prompt_snapshot: dict[str, Any],
    ):
        if self._langfuse is None:
            from contextlib import nullcontext

            return nullcontext(_NullGeneration())
        return self._langfuse.start_as_current_observation(
            as_type="generation",
            name=prompt_name,
            model=model_name,
            input=prompt_snapshot,
            trace_context={"trace_id": trace_id},
        )

    def _create_trace_id(self) -> str:
        if self._langfuse is not None:
            return self._langfuse.create_trace_id(seed=uuid4().hex)
        return uuid4().hex

    def _trace_url(self, trace_id: str) -> str | None:
        if self._langfuse is None:
            return None
        try:
            return self._langfuse.get_trace_url(trace_id=trace_id)
        except Exception:  # noqa: BLE001
            return None

    def _flush_langfuse(self) -> None:
        if self._langfuse is None:
            return
        try:
            self._langfuse.flush()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Langfuse flush failed: %s", exc)


class _NullGeneration:
    def update(self, **_: Any) -> None:
        return
