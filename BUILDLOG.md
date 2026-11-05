# Build log

2026-11-05 reconstruction. Public repository created before implementation. Source of truth: all 22 pages of `W7 - Put an LLM behind your API (1).pdf`. Job: support triage, preserving category/urgency/team vocabulary and adding explicitly required confidence field. Required stages only.

## Stage 0
`python src/llm/hello.py`: real Ollama gemma3:1b returned `ready`, exit 0. `.env` absent from `git status --short --untracked-files=all`; placeholder .env.example committed. Initially openai missing, installed 2.54.0. qwen3-vl:4b-instruct attempt failed with local CUDA initialization 500; changed only LLM_MODEL to assignment-recommended gemma3:1b, then succeeded. No fabricated provider success. Three environment variables select the OpenAI-compatible endpoint/model/key.
