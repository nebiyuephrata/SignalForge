For each task, return JSON with top-level key `scores`, where each item contains:
- index
- coherence
- verifiability
- rubric_clarity
- include
- note

Use a 1-5 scale for all three dimensions.
Include a task only if it scores at least {minimum_score} on:
- coherence
- verifiability
- rubric_clarity

Seed family: {seed_family}
Tasks: {tasks_json}
