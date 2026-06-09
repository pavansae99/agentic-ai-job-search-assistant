# Backend

Python 3.12 FastAPI service for profile analysis, explainable job matching, LangGraph orchestration,
provider-neutral OpenAI integration, deterministic fallback behavior, and SQLite application
tracking.

## Start

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
uvicorn --app-dir src job_search_assistant.main:app --reload
```

The default `LLM_PROVIDER=auto` uses OpenAI when `OPENAI_API_KEY` is present and deterministic
tools otherwise. To select a mode explicitly:

```bash
export LLM_PROVIDER=mock
# or
export LLM_PROVIDER=openai
export OPENAI_API_KEY="your-key"
```

Explicit `openai` mode fails application startup when the key is missing or blank. FastAPI
lifespan reuses one provider/client and compiled workflow across requests.

See `../docs/llm-architecture.md` for provider behavior and failure policy.

## Quality

```bash
ruff check .
ruff format --check .
mypy src/job_search_assistant
pytest --cov=job_search_assistant --cov-report=term-missing
```

The service still runs without an external model or API key. Coverage is enforced at 90%.
Interactive API documentation is available at `http://127.0.0.1:8000/docs`.
