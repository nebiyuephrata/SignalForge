Generate exactly 2 diagnostic tasks as JSON with top-level key `tasks`.

Each task must contain keys:
- company_name
- signal_confidence
- setup
- gap_excerpt
- prior_thread
- good_body
- required_signal_strings
- require_question_mark
- require_calendar_link
- require_handoff_phrase
- require_no_dollar_sign
- difficulty
- rationale

Constraints:
- All tasks must be `email_grounding` tasks.
- Keep `good_body` under 110 words.
- `required_signal_strings` must be strings that really appear in the output.
- Use short, plain string values.

Seed family: {seed_family}
Dimension: {dimension}
Brief: {brief}
