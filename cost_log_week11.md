# Week 11 Cost Log

## 2026-04-29

- `$0.00` — local repo inventory and benchmark scaffolding
- `$0.00` — trace-derived benchmark authoring from existing repo artifacts
- `$0.01593473` — multi-LLM synthesis authoring via OpenRouter (`google/gemini-2.5-flash` generation plus `qwen/qwen3-32b` judge filtering), logged in `generation_scripts/synthesis_cache.json`
- `$0.00` — contamination-check implementation and local validation
- `$0.00` — Path B preference-data formatting from local benchmark splits
- `$0.00` — local Path B linear critic training run in `training/run_path_b_critic.py`
- `$0.00` — held-out bootstrap ablation and trace export in `ablations/`
- `$0.00` — synthesis memo drafting from paper review and local evidence

## Budget buckets

Planned envelope for the full Week 11 cycle:

- dataset authoring: `$3–5`
- training: `$0–5`
- held-out evaluation: `$2–3`
- reserve: `$1–2`

Notes:

- No paid eval-tier model runs logged yet.
- Synthesis-model spend is now logged from the actual benchmark authoring pass.
- Training compute remains local and effectively `$0.00` in this environment.
- This log should still be extended if the repo moves from the local linear critic to a GPU-backed SimPO/ORPO run.
