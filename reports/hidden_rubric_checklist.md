# Hidden Rubric Checklist

This checklist captures likely "hidden rubric" expectations that do not always appear as first-order source-code requirements but still affect grading quality.

## Public Artifact Coherence

- The repo should expose one clear executive-facing artifact:
  - `reports/executive_memo.md`
- The repo should expose one clear public-writing artifact:
  - `publish/devto_post.md`
- The repo should expose one clear live-demo artifact:
  - `publish/video_walkthrough_script.md`
  - `publish/video_narration_script.md`

## Number Consistency

- Executive memo uses the executed held-out ablation artifact:
  - baseline `0.5116`
  - trained `1.0000`
  - delta `+48.84pp`
  - `95% CI [34.88, 62.79]`
  - paired bootstrap `p = 0.0`
- Public dataset walkthrough uses the currently published bundle counts:
  - train `62`
  - dev `113`
  - held-out `50`

These two number families are intentionally different because the executed ablation artifact predates the later benchmark split reshaping. The repo should explain that distinction instead of silently mixing them.

## Demo Readiness

- Hugging Face dataset URL is public and stable.
- GitHub community issue URL is public and stable.
- The video script shows:
  - dataset page live
  - file list
  - manifest counts
  - one concrete task
  - one evaluator output
  - one ablation number
  - one held-out trace row
  - blog post
  - community artifact

## Honesty Signals

- The 24-hour inter-rater requirement is still explicitly marked incomplete.
- The current trained artifact is described as a local linear critic, not a stronger ORPO/SimPO result.
- Delta B is described honestly as training versus the current prompt-engineered static gate, not as the strongest imaginable prompt-only baseline.
- Ground-truth lossiness from public-signal evidence is named explicitly.

## Production Judgment

- The executive memo includes one unambiguous recommendation category:
  - `deploy with caveat`
- The memo includes one measurable kill switch:
  - send-volume drop threshold
  - complaint / override threshold

## Video Execution Risks To Avoid

- Do not switch between stale local counts and public manifest counts without explanation.
- Do not say the held-out preference rows are public; only the held-out metadata file is public.
- Do not imply the ORPO scaffold is the executed headline result.
- Do not say the 24-hour inter-rater requirement is complete.
