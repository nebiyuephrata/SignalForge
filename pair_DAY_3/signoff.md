# Sign-off — Day 3

**Asker (signing off):** Ephrata Nebiyu  
**Explainer (received from):** Nureye Nigus  
**Topic:** Training and post-training mechanics — pairwise preference learning and lexical shortcut formation  
**Date:** 2026-05-07

---

## Judgement

- [x] **Closed** — gap is closed; I can now defend the mechanism unaided.
- [ ] **Partially closed**
- [ ] **Not closed**

## What I understand now that I did not before

I understand much more clearly now that the Day 3 failure is not just "the
critic is using shortcuts," but that pairwise preference training gives the
model a very specific optimization target: rank chosen above rejected, not
learn a fully calibrated absolute notion of commercial usefulness. The part
that landed most for me is the asymmetry between **rejection boundaries** and
**acceptance calibration**. Rejected examples often contain cheaper, more
repeated, more local cues, so a small judge can improve quickly by learning a
compact negative boundary without yet learning the richer compositional concept
of what a truly good `pass` output is. I can now also explain why harder
negatives matter mechanistically: lexically compliant but commercially weak
rejected examples remove easy separability and force the model to learn within
the compliant region instead of winning on surface cues alone.

## Why this is now closed

The explainer gave me the training-mechanics account I was missing. I can now
defend why SimPO/ORPO-style pair construction, margin-based ranking, and small
model capacity make lexical compliance easier to internalize than deeper
commercial judgment, and why this is not the same thing as saying "the model
needs more data." More importantly, I can connect that mechanism back to my own
repo artifacts: the unresolved note in `reports/executive_memo.md`, the Path B
rationale in `methodology_rationale.md`, and the next redesign of
`training_data/path_b_preferences.jsonl` all now point to the same concrete
intervention, which is adding harder lexically compliant negatives so the critic
has to learn commercially meaningful distinctions rather than just shortcut
separability.
