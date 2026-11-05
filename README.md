# Support triage API

This is a reconstruction begun on 2026-11-05 with newly executed checkpoints, preserving the previous repository. It does not claim historical student authorship. Required stages only; no optional extras.

The local Ollama provider uses the OpenAI-compatible client. Change LLM_BASE_URL, LLM_API_KEY and LLM_MODEL to swap providers without changing code.

Stub mode: set LLM_STUB=1 in .env, then `python -m uvicorn app:app --port 8108`.

```powershell
curl.exe -X POST http://127.0.0.1:8108/triage -H 'Content-Type: application/json' -d '{"text":"I was charged twice"}'
curl.exe -X POST http://127.0.0.1:8108/triage -H 'Content-Type: application/json' -d '{}'
```

The first returns 200 and the schema-valid manual-review stub; the second returns 400 naming text, before a model call. The existing task API is retained in tasks_api.py and repository.py, reused from the earlier assignment rather than claimed as newly authored here.
