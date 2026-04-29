# Reporting Artifacts

This directory contains reviewer-facing Week 11 report materials derived from the benchmark and evaluation files.

Key files:

- [week11_status_report.md](./week11_status_report.md): the narrative report aligned to the interim-report rubric
- [bench_composition.json](./bench_composition.json): machine-readable composition cube
- [bench_composition_table.md](./bench_composition_table.md): markdown cross-tab used in the report appendix
- [worked_examples.json](./worked_examples.json): scored examples used in the report walkthrough
- [inter_rater_report.json](./inter_rater_report.json): report-ready agreement summary

Rebuild the derived reporting artifacts with:

```bash
.venv/bin/python generation_scripts/build_reporting_artifacts.py
```
