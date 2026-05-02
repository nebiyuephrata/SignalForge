# Video Narration Script

Use this as the spoken track while following `publish/video_walkthrough_script.md`.

## Opening

"This demo shows the public dataset, the scoring path for one concrete task, the held-out ablation result, and the public write-up artifacts for Tenacious-Bench v0.1 and the Path B critic."

## 1. Dataset Walkthrough

"I’m starting on the live Hugging Face dataset page, not a local file. This is the public preference dataset for the Path B route."

"As I scroll the dataset card, you can see the seven datasheet sections: motivation, composition, collection process, preprocessing and labeling, uses, distribution, and maintenance."

"In the file list, I’m showing the train file, the dev file, the held-out metadata file, and the manifest. The held-out rows are intentionally not public, but the held-out partition is still discoverable."

"Now I’m opening `manifest.json`. This is the easiest place to see the three discoverable partitions and their counts: train `62`, dev `113`, and held-out `50`."

"I’m opening one train row here to show that each example carries structural metadata, including the source mode. That matters because this benchmark mixes trace-derived, programmatic, multi-LLM synthesis, and hand-authored tasks rather than relying on only one authoring route."

## 2. End-to-End Task Scoring

"Next I’m showing one concrete benchmark task from the local benchmark files. On screen you can see the task input, the candidate output, and the ground-truth fields that the evaluator will check."

"The important point is that this evaluator is not a vague ‘does this sound good’ grader. It scores explicit dimensions like grounded language, confidence alignment, tone safety, directness constraints, and routing safety."

"Here I’m pointing to one concrete rubric check. For example, this task requires a question-mark behavior and bans specific over-claiming phrases. That means the score is tied to observable task properties, not only a free-form judgment."

"When I run the evaluator, the output shows the numerical breakdown by dimension, not just one aggregate score. So the viewer can see exactly why the task passed or failed."

## 3. Ablation Result

"Now I’m opening the ablation results. The headline Delta A result is the trained Path B critic versus the pre-trained heuristic gate on the executed held-out preference set."

"The visible number here is a `+48.84` percentage-point lift, from `0.5116` baseline accuracy to `1.0000` trained accuracy, with a `95%` confidence interval of `[34.88, 62.79]` from a paired bootstrap test."

"I’m opening the held-out trace artifact next. This is important because I want to show that the ablation table is backed by row-level evidence, not just a summary number."

"What I would say here is: this table-level claim comes from these held-out preference rows, and the statistical treatment is a paired bootstrap over the held-out trace set. So the result is not just a point estimate; it includes uncertainty."

"One honesty note: the executed ablation artifact uses the earlier held-out evaluation slice, while the currently published dataset manifest reflects the later public bundle counts. I’m keeping those two number families separate rather than mixing them."

## 4. Blog Post

"Now I’m opening the public blog-style write-up in GitHub. I’m scrolling briefly so the structure is visible and it is clear this is a substantive artifact, not a placeholder."

"The point of this post is to explain why a generic benchmark was not enough for this workflow and why the benchmark had to target Tenacious-specific failure modes."

## 5. Community Engagement

"This is the public GitHub issue used as the community-engagement artifact. I’m showing the live URL and the visible content so it is clear the benchmark work was surfaced outside the internal repo files."

## 6. Close

"The short version is: there is a real public dataset, a real deterministic evaluator, a real held-out ablation result, and real public artifacts explaining the work. The main unresolved item is still the true 24-hour inter-rater rerun, which I am keeping explicit rather than overstating."
