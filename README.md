Opus Blocks backend.

Local setup
- copy `.env.example` to `.env` and set `OPENAI_API_KEY` if you want real LLM calls
- set `LLM_USE_OPENAI=true` to enable the OpenAI provider path

Notes
- by default the pipeline uses stubbed outputs; the OpenAI path is gated by `LLM_USE_OPENAI`
- golden set runner: `uv run python scripts/run_golden_set.py docs/golden-dataset-v0.json --results-out docs/golden-results-v0.json`
