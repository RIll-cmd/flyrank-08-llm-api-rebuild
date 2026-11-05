# Required checkpoint map

All 22 pages of the supplied assignment were read, including requirements, done-means, resources and glossary. Optional extras, stretch and AI rematch are excluded.

- Stage 0: JOB-CARD, local provider ready, ignored .env and empty-value .env.example.
- Stage 1: existing task API plus triage; Pydantic input and closed output; bad input 400 names text; stub makes zero model calls.
- Stage 2: versioned prompt with all five parts; separate JSON-encoded user message; three real answers and observations.
- Stage 3: prose/fence extraction, JSON parse, schema validation, exactly one repair, 422 and quarantine; never raw output in final contract.
- Stage 4: explicit 30 s client timeout; bounded 1/2/4 s jitter retries for timeout/429/5xx only; Retry-After; SDK retries explicitly off; per-call structured cost logs; kill switch fallback.
- Stage 5: eight hand-labelled eval cases (ambiguous and unsure included), endpoint runner with failures and actual score; README ordered as assigned; no tracked key/history; public repo and six stage commits; under-five-minute configured startup checked.

Concrete command outputs and limitations are in BUILDLOG.md.
