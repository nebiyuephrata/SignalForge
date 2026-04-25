# Directory Index

## Hidden Top-Level Folders

- `.git`: Git metadata and branch history for the repository.
- `.pytest_cache`: local pytest cache data created by test runs.
- `.qodo`: local assistant or IDE metadata; not part of the SignalForge runtime.
- `.venv`: local Python virtual environment when created in-repo.

## Product Folders

- `agent`: Core business logic for enrichment, scoring, orchestration, guards, channels, CRM, and calendar behavior.
- `backend`: FastAPI application, HTTP routes, request/response schemas, and service-layer wiring.
- `configs`: Small YAML configuration files for thresholds, signal weights, and model labels.
- `data`: Local deterministic fixtures for company records, layoffs, and job-post HTML used during enrichment.
- `demo`: Human-readable demo assets and walkthrough notes.
- `docs`: Architecture diagrams and longer-form system notes beyond the README.
- `eval`: Adversarial cases, probe analysis helpers, and evaluation harness code.
- `frontend`: Vite/React interface for inspecting runs and outputs locally.
- `logs`: Append-only JSONL runtime logs and failure traces.
- `method`: Mechanism-design documentation for the confidence calibration layer.
- `outputs`: Generated JSON artifacts from prospect runs, channel plans, and evaluation summaries.
- `probes`: Machine-readable probe library and the markdown failure analysis derived from it.
- `scripts`: Convenience scripts for local execution, summaries, and batch runs.
- `tenacious_sales_data`: Seed context, policies, schemas, and supporting artifacts for the Tenacious use case.
- `tests`: Regression tests for API routes, integrations, orchestration, scoring, and the LLM guardrail layer.
