# Backend

Python 3.12 FastAPI service for profile analysis, explainable job matching, LangGraph orchestration,
and SQLite application tracking.

## Start

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
uvicorn --app-dir src job_search_assistant.main:app --reload
```

## Quality

```bash
ruff check .
ruff format --check .
mypy src/job_search_assistant
pytest --cov=job_search_assistant --cov-report=term-missing
```

The service runs without an external model or API key. Interactive API documentation is available
at `http://127.0.0.1:8000/docs`.
