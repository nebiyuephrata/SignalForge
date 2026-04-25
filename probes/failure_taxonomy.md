# Failure Taxonomy

The category metrics below are computed from [probe_library.json](./probe_library.json) via `eval/probe_analysis.py`.

## Highest-Risk Categories By Expected Loss Index

1. `weak confidence handling`
   - `probe_count`: `4`
   - `average_trigger_rate`: `0.40`
   - `average_business_cost_usd`: `$53,662.50`
   - `expected_loss_index`: `21,330.84`
   - Why it matters: weak evidence becomes fluent outreach, which breaks trust before the system ever gets the chance to qualify or book.

2. `CTO sensitivity`
   - `probe_count`: `1`
   - `average_trigger_rate`: `0.29`
   - `average_business_cost_usd`: `$65,250.00`
   - `expected_loss_index`: `18,922.50`
   - Why it matters: a defensive CTO can shut down a high-ACV thread immediately.

3. `signal over-claiming`
   - `probe_count`: `3`
   - `average_trigger_rate`: `0.33`
   - `average_business_cost_usd`: `$55,800.00`
   - `expected_loss_index`: `18,600.00`
   - Why it matters: exaggerated hiring narratives destroy SignalForge's credibility advantage quickly.

4. `outsourcing perception`
   - `probe_count`: `1`
   - `average_trigger_rate`: `0.27`
   - `average_business_cost_usd`: `$60,750.00`
   - `expected_loss_index`: `16,402.50`
   - Why it matters: if Tenacious sounds like generic offshore staffing, the system loses positioning even when the signals are right.

5. `gap over-claiming`
   - `probe_count`: `3`
   - `average_trigger_rate`: `0.30`
   - `average_business_cost_usd`: `$49,500.00`
   - `expected_loss_index`: `14,850.00`
   - Why it matters: benchmark claims are powerful only when they remain narrow and sourced.

## Full Category Table

| Category | Probe count | Avg trigger rate | Avg business cost | Expected loss index |
| --- | ---: | ---: | ---: | ---: |
| `weak confidence handling` | 4 | 0.40 | $53,662.50 | 21,330.84 |
| `CTO sensitivity` | 1 | 0.29 | $65,250.00 | 18,922.50 |
| `signal over-claiming` | 3 | 0.33 | $55,800.00 | 18,600.00 |
| `outsourcing perception` | 1 | 0.27 | $60,750.00 | 16,402.50 |
| `gap over-claiming` | 3 | 0.30 | $49,500.00 | 14,850.00 |
| `tone drift` | 3 | 0.32 | $40,900.00 | 13,224.33 |
| `outsourcing mismatch` | 3 | 0.28 | $45,600.00 | 12,920.00 |
| `ICP misclassification` | 3 | 0.24 | $29,200.00 | 7,105.33 |
| `multi-thread leakage` | 3 | 0.17 | $37,500.00 | 6,250.00 |
| `coordination failures` | 3 | 0.17 | $31,500.00 | 5,460.00 |
| `signal reliability` | 3 | 0.21 | $15,100.00 | 3,171.00 |
| `scheduling edge cases (EU/US/Africa)` | 3 | 0.15 | $17,850.00 | 2,737.00 |
| `cost issues` | 3 | 0.28 | $5,800.00 | 1,624.00 |

## Interpretation

SignalForge's most expensive failure classes are not just "wrong facts." They are failures where uncertainty is present but not operationalized:

- `weak confidence handling` is first because it contaminates prompt style, channel routing, and booking behavior at the same time.
- `signal over-claiming` stays dangerous, but it is downstream of the same calibration issue.
- `gap over-claiming`, `outsourcing perception`, and `CTO sensitivity` all get worse when the system speaks too confidently on partial evidence.

That is why the current mechanism-design work focuses on the confidence calibration layer rather than on tone polish alone.
