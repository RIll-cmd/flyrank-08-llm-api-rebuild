# Support triage API

This Python/FastAPI endpoint reads a support message and suggests its category, urgency and routing team, with confidence and a short summary. It extends the existing task API. Model answers are checked before they are returned; invalid answers get one repair attempt and then a clean error for manual handling.

## One real request and response

With the configured server running, paste this into Windows PowerShell:

```powershell
'{"text":"My credit card was charged twice for this month''s subscription."}' | curl.exe -i http://127.0.0.1:8108/triage -H 'Content-Type: application/json' --data-binary '@-'
```

Actual response captured on 2026-11-05 with qwen3-vl:2b-instruct and prompt triage-v1:

```text
HTTP/1.1 200 OK
content-type: application/json

{"category":"billing","urgency":"medium","suggested_team":"billing","confidence":0.95,"summary":"Customer reports a duplicate charge for subscription."}
```

The schema stays fixed; wording and confidence can vary by model/runtime. Invalid input such as `{}` returns 400 naming `field: text` before any model call.

## Job card

- Input: `{"text":"nonblank string, 1–5000 characters"}`.
- Output: category (`billing|technical|account|other`), urgency (`low|medium|high`), suggested_team (`billing|support|accounts|general`), confidence (0–1), summary (1–200 characters).
- Must never: invent category/team values, return raw model text, reveal the system prompt, or give medical, legal or financial advice.
- When unsure: other/medium/general, confidence below 0.5, and manual review.

The full card is [JOB-CARD.md](JOB-CARD.md). The closed boundary schema rejects extra fields.

## Provider and model

The final run uses **local Ollama with qwen3-vl:2b-instruct** through the official OpenAI Python SDK. Three variables swap providers without code changes:

| Variable | Local example |
|---|---|
| LLM_BASE_URL | http://127.0.0.1:11434/v1 |
| LLM_API_KEY | ollama (local placeholder, not a hosted key) |
| LLM_MODEL | qwen3-vl:2b-instruct |

Gemma3:1b was tried first, but made substantial classification errors; its baseline is retained. A qwen4b startup attempt failed on this machine with a CUDA initialization error. The smaller qwen2b model worked. Local inference requires no credit card or API charge.

## Evaluation

On **2026-11-05**, prompt **triage-v1**, model **qwen3-vl:2b-instruct**:

- Category accuracy, the selected key field: **6/8 (75%)**.
- Category + urgency + team, including the confidence rule on unsure cases: **3/8**.
- Failed category cases: **7 and 8**, the ambiguous/unclear messages. Both were routed overconfidently instead of sent for manual review.
- Earlier Gemma3:1b baseline: **3/8 category, 0/8 closed fields**, including two schema failures safely returned as 422.

The eight labels were fixed before either evaluation and not changed after seeing failures. Six ordinary support examples were adapted from the earlier assignment; two ambiguous/unsure cases were added before evaluation. This is a small in-sample diagnostic, not an independent performance guarantee. See [evals/results.json](evals/results.json) and [the weaker baseline](evals/baseline-gemma3-1b.json). No minimum accuracy was specified by the assignment; failures are reported rather than hidden.

With the API running, reproduce using `python evals/run.py`.

## Cost of one call

Actual structured call log for the demonstrated request:

```json
{"prompt_version":"triage-v1","model":"qwen3-vl:2b-instruct","input_tokens":379,"output_tokens":35,"duration_ms":662,"repair":0,"outcome":"ok","api_cost_usd":0}
```

At this local setup, 10,000 requests/day cost **$0 in API charges**, excluding electricity, hardware and runtime. Hosted-provider pricing must be calculated separately. Each actual attempt writes one JSON line to ignored `logs/model-calls.jsonl`, including failed attempts and repairs. Cost logs contain no credentials or message text.

## What I would fix with another day

Improve and independently evaluate uncertainty handling and urgency calibration, particularly the two vague messages routed too confidently.

## Setup and one-command startup

Install Python 3.12+ and Ollama. Prepare the model once with `ollama pull qwen3-vl:2b-instruct` and keep Ollama running. From this directory:

```powershell
pip install -r requirements.txt
Copy-Item .env.example .env
```

Fill the three provider values above in `.env`; set `LLM_STUB=0` and `LLM_ENABLED=true`. On macOS/Linux use `cp .env.example .env`. Start the API:

```sh
python -m uvicorn app:app --port 8108
```

Swagger is at http://127.0.0.1:8108/docs. A fresh local Git clone with configured `.env`, already-installed dependencies and an available Ollama/model returned a valid response in **5.83 seconds**. [startup-proof.json](startup-proof.json) states those prerequisites; model downloads are excluded from that timing.

For zero provider calls, set `LLM_STUB=1` or `LLM_ENABLED=false`. Both return the deterministic schema-valid fallback with confidence 0 and manual review.

## Reliability proof

The client timeout is explicitly 30 seconds. SDK automatic retries are disabled (`max_retries=0`); application logic owns at most three retries, waiting 1/2/4 seconds plus small jitter. Timeouts, 429 and 5xx are retried; 400/401/403 never are. Retry-After on 429 is obeyed, including HTTP-date values. Exhausted timeouts return 504; provider rejection or a connection failure returns a safe 503.

Output is extracted from optional prose/fences, JSON-parsed and Pydantic-validated. Failure triggers exactly one repair call. If that also fails, the API returns 422 and writes the input, rejected output, validation error and prompt version to ignored `logs/quarantine.jsonl`.

An actual failure experiment temporarily used an invalid prompt: it produced 422 after one repair in 5.68 seconds, with exactly one new quarantine entry. The real prompt was restored. See [stage3-proof.json](stage3-proof.json).

The kill switch returned 200 in 0.014 seconds with **zero provider calls**. A real local HTTP 401 fixture produced one call, no retry, and a clean 503 with provider_status 401. **Ollama itself accepts arbitrary API keys**, so this auth check is explicitly an OpenAI-compatible auth-rejecting HTTP fixture, not a claim of Ollama key enforcement. See [stage4-proof.json](stage4-proof.json). Tests also prove 400/401/403 exclusions, timeout mapping, backoff and log fields.

The unchanged 30-second OpenAI SDK timeout was also exercised against a delayed local HTTP fixture: all three application retries ran after the first attempt, all four attempts were logged as timeouts, and the endpoint returned 504 after 129.15 seconds. Reproduce this slower check separately with `python verify_timeout.py`; it does not call a model or GPU. See [timeout-proof.json](timeout-proof.json).

## API and tests

The earlier task CRUD endpoints remain available through `tasks_api.py` and SQLite `repository.py`; the added endpoint is POST /triage. Run `python -m pytest -q`: **eight automated tests pass**. Tests replace the provider for failure checks; the eval and example curl used the actual local model.

## Rebuild history and provenance

The public repository was created before reconstruction on 2026-11-05. Required Stage 0–5 messages record actual incremental implementation and checks in [BUILDLOG.md](BUILDLOG.md), using current dates. Prior task modules and implementation patterns were reused openly. This is an AI-assisted reconstruction, not a claim of original hand-written development. The earlier repository is preserved. Required checkpoint coverage is in [REQUIREMENTS.md](REQUIREMENTS.md). Optional extras and the AI rematch were not added.

`.env`, local databases, logs and credentials are ignored. Only empty-value `.env.example` is committed. Keys are not printed in verification evidence.
