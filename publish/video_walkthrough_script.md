# Six-Minute Walkthrough Script

## 1. Dataset Walkthrough

- Open the Hugging Face dataset URL live.
- Say: “This is the public Tenacious Bench Path B preference dataset.”
- Scroll the dataset card and call out the seven datasheet sections:
  - motivation
  - composition
  - collection process
  - preprocessing, cleaning, and labeling
  - uses
  - distribution
  - maintenance
- Open the file list and point to:
  - `preferences_train.jsonl`
  - `preferences_dev.jsonl`
  - `preferences_held_out_metadata.json`
  - `manifest.json`
- Open `manifest.json` and say: “This shows the three discoverable partitions and their counts: train `62`, dev `113`, held-out `50`.”
- Open one row in `preferences_train.jsonl` and point to `source_mode`.

## 2. End-to-End Task Scoring

- Open one concrete task from `tenacious_bench_v0.1/.../tasks.jsonl`.
- Show the input fields, candidate output, and ground truth.
- Run or show the evaluator output for that task.
- Narrate one specific rubric check, such as the banned-phrase check or question-mark requirement.

## 3. Ablation Result

- Open `ablations/ablation_results.json`.
- Point to the held-out delta and confidence interval.
- Open `ablations/held_out_traces.jsonl`.
- Trace one numeric claim back to a specific held-out row.

## 4. Blog Post

- Open the public GitHub URL for `publish/blog_post.md`.
- Scroll enough to show the structure and length.

## 5. Community Engagement

- Open the live issue URL:
  - `https://github.com/nebiyuephrata/SignalForge/issues/1`
- Say: “This is the public community-engagement artifact tied to the benchmark release.”

## 6. Time Split

- dataset: `2:00`
- task scoring: `1:15`
- ablation: `1:30`
- blog post: `0:35`
- community artifact: `0:25`
- transitions / close: `0:15`
