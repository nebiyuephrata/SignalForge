# Thread — Day 3

**1/**  
Why can a SimPO-tuned judge get much better at spotting bad outputs before it
gets equally good at recognizing acceptable ones? Because pairwise preference
training only asks the model to rank `chosen > rejected`, not to learn a fully
calibrated absolute notion of “good.”

**2/**  
That means a small judge can win the objective by learning cheap rejection
cues first: banned phrasing, obvious policy violations, unsupported claims,
wrong channel choices. Those are often lower-entropy, more repeated signals than
the diverse ways an answer can be acceptably good.

**3/**  
So rejection is often a boundary-detection problem, while acceptance is a
calibration problem. “This is clearly bad” can be learned from a few sharp
features. “This is acceptable and commercially useful” is usually more
compositional.

**4/**  
That’s why harder negatives matter. If rejected examples are too easy, the
model learns shortcut separability. But if rejected examples are lexically
compliant and policy-safe yet still generic or commercially weak, the judge has
to learn inside the compliant region.

**5/**  
This is also why prompt-only changes usually won’t fix the failure. The issue
is not just attention to the rubric. It’s the learned scoring geometry created
by the pair distribution and the preference objective.

**6/**  
The practical rule: if your judge is great at `fail` but shaky on `pass`, don’t
just ask for more data. Ask what features make rejection easier than
acceptance, and redesign your preference pairs so the model can’t win on cheap
surface cues alone.

