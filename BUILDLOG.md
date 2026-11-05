# Build log

2026-11-05 reconstruction. Public repository created before implementation. Source of truth: all 22 pages of `W7 - Put an LLM behind your API (1).pdf`. Job: support triage, preserving category/urgency/team vocabulary and adding explicitly required confidence field. Required stages only.

## Stage 0
`python src/llm/hello.py`: real Ollama gemma3:1b returned `ready`, exit 0. `.env` absent from `git status --short --untracked-files=all`; placeholder .env.example committed. Initially openai missing, installed 2.54.0. qwen3-vl:4b-instruct attempt failed with local CUDA initialization 500; changed only LLM_MODEL to assignment-recommended gemma3:1b, then succeeded. No fabricated provider success. Three environment variables select the OpenAI-compatible endpoint/model/key.

## Stage 1
Built Pydantic input and closed output schema first; added confidence 0–1, strict types, no extra fields. Reused existing task API modules (tasks_api.py and repository.py) and added /triage. LLM_STUB=1: valid message 200 and schema-valid manual review; missing, numeric, over-5000 and whitespace text each 400 with field:text. No model client exists on this route yet: zero model calls.

## Stage 2
Prompt triage-v1.md has role, full schema, restrictions, unsure rule and three examples. System/user messages separated; user text JSON-encoded; temperature 0. Real gemma3:1b TestClient calls with stub off returned three raw answers. Duplicate-charge: billing/high/billing; app-crash: technical/high/technical; unclear: other/medium/general. Surprise: model invented suggested_team=technical (outside enum), and marked routine duplicate-charge urgency high. This deliberately temporary raw stage exposes why Stage 3 is necessary; do not deploy this checkpoint as the final API.

## Stage 3
Three offline tests pass: input/stub, repair once plus quarantine, fenced output extraction. Fresh live checkpoint temporarily replaced the prompt with an instruction to always return INVALID; actual gemma response and one repair both failed schema validation, resulting422 in5.68seconds and exactlyone new quarantine line. The versioned triage prompt was restored in finally. stage3-proof.json records the actual result. No raw invalid output is returned to the caller.

## Stage 4
Implemented30second timeout, max_retries=0 onSDK, three own retries with1/2/4second backoff plus jitter, obeying numeric/date Retry-After on429. Never retries400/401/403. Structured JSONL per attempt includes version/model/token counts/duration/repair/outcome and localAPIcost0. Eight offline tests pass. Live kill switch returnedfallback200 in0.014seconds withzero providercalls. ActualHTTP401 fixture returnedclean503/provider_status401 withone providercall, no retry. Ollama itself accepts arbitraryAPIkeys, so401 enforcement was deliberately tested against a clearly labeled local auth-rejecting OpenAI-compatible fixture, not falsely attributed toOllama. stage4-proof.json records both.

## Stage 5
Eight fixed labeled cases were created before evaluation, including ambiguous and unsure cases. Gemma3:1b measured 3/8 category and 0/8 closed fields; retained baseline. Swapped only the model to qwen3-vl:2b-instruct and reran unchanged cases: 6/8 category (75%), 3/8 closed fields, all eight responses schema-valid 200. Cases 7/8 were overconfidently misrouted; reported without changing labels. Actual PowerShell curl returned billing/medium/billing/confidence0.95. Cost example: 379 input and35 output tokens, 662ms, zero API USD. Fresh configured local Git clone returned200 in5.83seconds with dependencies/model already available; prerequisites recorded. Ordered README includes exact sample, job card, provider vars, scores, cost estimate and one-day limitation.
