# Real Run Evidence

Artifact: [outputs/verified_run.json](/home/rata/Documents/Ephrata/work/10Acadamy/training/SignalForge/outputs/verified_run.json)

## What Was Executed

- Run type: full end-to-end prospect execution
- Prospect: `Northstar Lending`
- Execution time: `2026-04-25T07:20:50.084137+00:00`
- Entry point: `.venv/bin/python -m eval.verified_execution`

## Observed Result

- Signal summary:
  `Northstar Lending shows mixed but timely hiring intent: roles moved from 3 to 12 over 60 days after a Series B on 2026-02-14, but layoffs were also recorded recently.`
- Hiring brief overall confidence: `0.79`
- Confidence calibration score:
  `0.62`
- Confidence level:
  `medium`
- Generated message model:
  `deterministic-fallback`
- Fallback occurred:
  `true`

## Why Fallback Happened

SignalForge did attempt the live OpenRouter path. The attempt did not complete because outbound name resolution failed in this environment.

Observed transport failures:

- `deepseek/deepseek-chat` attempts `1-3`: `[Errno -3] Temporary failure in name resolution`
- `qwen/qwen3-32b` attempts `1-3`: `[Errno -3] Temporary failure in name resolution`

Fallback explanation from the artifact:

- `Fallback occurred after live OpenRouter transport attempts failed: OpenRouter generation failed: [Errno -3] Temporary failure in name resolution`

## Trace Evidence

- Attempted trace id:
  `4dba3958f78f4b5487ba55339294858c`
- Prompt name:
  `generate_outreach_email`
- Transport attempted:
  `true`
- Final trace URL:
  `null`

The trace id proves the request path created a trace context before transport failure. The missing trace URL is consistent with the observed Langfuse unavailability in this environment.

## Other Real-World Boundaries Seen In The Same Run

- `company_careers_page` scraping used fixture fallback because Playwright Chromium was unavailable locally.
- `builtin`, `wellfound`, and `linkedin_public` remained explicitly skipped because this repo is still running in offline-fixture mode.
- The system still produced a valid grounded email because the deterministic fallback path remained intact.
