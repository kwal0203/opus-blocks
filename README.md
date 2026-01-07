Opus Blocks backend.

Local setup
- copy `.env.example` to `.env` and set `OPENAI_API_KEY` if you want real LLM calls
- set `LLM_USE_OPENAI=true` to enable the OpenAI provider path

Notes
- by default the pipeline uses stubbed outputs; the OpenAI path is gated by `LLM_USE_OPENAI`
- golden set runner: `uv run python scripts/run_golden_set.py docs/golden-dataset-v0.json --results-out docs/golden-results-v0.json`
- job dispatch is disabled by default; set `JOBS_ENQUEUE_ENABLED=true` and run a Celery worker to execute extract/generate/verify
- token budgets and circuit breaker controls are configurable via `LLM_TOKEN_BUDGET_*` and `CIRCUIT_BREAKER_*`

Vector store
- default backend is stub (Postgres-only); set `VECTOR_BACKEND=chroma` for local Chroma persistence
- backfill embeddings: `uv run python scripts/backfill_embeddings.py`

Infra ops
- rate limits are configurable via `RATE_LIMIT_*` env vars; disabled by default in `.env.example`

Monitoring
- metrics snapshot + alerts: `uv run python scripts/run_metrics_snapshot.py`

Frontend (testing UI)
- quick ops panel lives in `frontend/` (Vite + React)
- run: `cd frontend && npm install && npm run dev`
- Vite proxies `/api` to `http://localhost:8000` to avoid CORS during local testing
- optional: set `VITE_API_BASE_URL` to override the API prefix (defaults to `/api/v1`)
- Base URL input defaults to `VITE_API_BASE_URL` when the app loads

Docker compose (all-in-one dev)
- bring up everything: `docker compose up --build`
- API: `http://localhost:8000`
- Frontend: `http://localhost:5173`
