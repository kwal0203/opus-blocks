Opus Blocks backend.

Local setup
- copy `.env.example` to `.env` and set `OPENAI_API_KEY` if you want real LLM calls
- set `LLM_USE_OPENAI=true` to enable the OpenAI provider path

Notes
- by default the pipeline uses stubbed outputs; the OpenAI path is gated by `LLM_USE_OPENAI`
- golden set runner: `uv run python scripts/run_golden_set.py docs/golden-dataset-v0.json --results-out docs/golden-results-v0.json`

Vector store
- default backend is stub (Postgres-only); set `VECTOR_BACKEND=chroma` for local Chroma persistence
- backfill embeddings: `uv run python scripts/backfill_embeddings.py`

Infra ops
- rate limits are configurable via `RATE_LIMIT_*` env vars; disabled by default in `.env.example`

Monitoring
- metrics snapshot + alerts: `uv run python scripts/run_metrics_snapshot.py`
