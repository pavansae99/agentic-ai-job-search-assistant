# Agentic AI Job Search Assistant

[![Backend CI](https://github.com/pavansae99/agentic-ai-job-search-assistant/actions/workflows/backend-ci.yml/badge.svg)](https://github.com/pavansae99/agentic-ai-job-search-assistant/actions/workflows/backend-ci.yml)

An interview-ready backend system that turns a resume and job description into an explainable
fit decision, missing-keyword analysis, recruiter outreach, career coaching, and a persisted
application record.

This is not a chat completion wrapped in an API. The system separates domain tools, specialized
agents, typed workflow state, orchestration, persistence, and transport concerns so each can be
tested and evolved independently.

## What It Does

- Extracts skills, experience, target roles, location preferences, and work authorization.
- Parses required and preferred job qualifications.
- Scores fit using deterministic weighted components.
- Classifies results as `Strong Fit`, `Good Fit`, `Weak Fit`, or `Not Recommended`.
- Identifies missing required keywords without encouraging fabricated experience.
- Generates a recruiter email grounded in matched candidate facts.
- Provides career-coaching suggestions for concrete gaps.
- Tracks application status in SQLite.
- Exposes the workflow through a typed FastAPI contract.

## Why This Is Agentic AI

The application models a goal-directed process as cooperating components rather than one prompt:

1. Each agent has a narrow responsibility and a constrained input/output contract.
2. Tools perform concrete actions such as parsing, scoring, retrieval, and email generation.
3. LangGraph owns execution order and passes durable typed state between nodes.
4. The reasoning trace records what each node contributed.
5. Deterministic policies handle decisions that should be reproducible and auditable.
6. LangChain `BaseTool` adapters allow future chat models to select tools without coupling tools
   to a specific provider.

The MVP intentionally does not require an LLM key. This makes local execution and CI deterministic.
An LLM can later augment extraction or writing behind the existing agent interfaces while Pydantic
validation and deterministic scoring remain control boundaries.

## Workflow

```text
START
  |
  v
ResumeAnalysisAgent
  |
  v
JobAnalysisAgent
  |
  v
MatchScoringAgent
  |
  v
FitRankingAgent
  |
  v
RecruiterEmailAgent
  |
  v
END
```

The typed `JobMatchState` carries raw inputs, parsed models, component scores, final score,
ranking, missing keywords, recruiter email, and an append-only reasoning trace. The
`CareerCoachAgent` evaluates the completed graph result as a post-workflow advisor.

See [docs/agent-workflow.md](docs/agent-workflow.md) for node and state details.

## Architecture

```text
HTTP clients
    |
FastAPI routes and Pydantic contracts
    |
Application services
    +----------------------+
    |                      |
LangGraph workflow     ApplicationService
    |                      |
Specialized agents     Repository
    |                      |
Deterministic tools    SQLAlchemy
    |                      |
Local retrieval        SQLite
```

Key boundaries:

- `api/`: HTTP routing and dependency injection.
- `services/`: use-case orchestration independent of FastAPI.
- `workflows/`: graph topology and shared state.
- `agents/`: single-purpose decision or transformation units.
- `tools/`: deterministic capabilities and LangChain adapters.
- `repositories/`: persistence operations.
- `schemas/`: validation and public contracts.
- `models/` and `database/`: SQLAlchemy persistence infrastructure.

Read the design decisions in [docs/architecture.md](docs/architecture.md).

## Explainable Scoring

The initial scoring policy is deterministic:

```text
final score =
  skill overlap       * 50%
  experience match    * 20%
  location match      * 15%
  authorization fit   * 15%
```

Every component returns a `0-100` score and a plain-language explanation. Recommendation bands:

| Score | Ranking |
|---:|---|
| `85-100` | Strong Fit |
| `70-84.99` | Good Fit |
| `50-69.99` | Weak Fit |
| `< 50` | Not Recommended |

Keeping this policy outside an LLM makes it reviewable, testable, and safe to calibrate from
future outcome data.

## RAG-Ready Design

`VectorSearchTool` defines the MVP retrieval contract:

```python
document_id = store.add_document(content, metadata)
results = store.search(query, limit=5)
```

The local adapter uses cosine similarity over term-frequency vectors. It is useful for tests and
architecture validation, but it is not presented as production semantic retrieval. A Chroma,
pgvector, or managed vector database adapter can implement the same boundary later.

Potential RAG corpora include anonymized resume versions, prior job descriptions, interview notes,
and approved achievement stories. Retrieved content should be treated as evidence supplied to an
agent, not as an instruction that bypasses validation.

## Tool Calling

Agents call typed tools directly in the deterministic path. The LangChain registry also exposes
resume and job parsers as `BaseTool` instances with Pydantic argument schemas. A future model can
use `model.bind_tools(build_tool_registry())`, while authorization, persistence, and score
calculation remain controlled by application code.

## Human In The Loop

The graph has an intentional review point after ranking and before recruiter outreach. A production
version can replace the direct edge with a conditional edge:

- Auto-continue for high-confidence analysis.
- Interrupt when authorization is uncertain, the score is near a threshold, or extracted facts
  conflict.
- Let the user edit the email before sending.
- Persist the approval decision and resume the graph from a checkpoint.

No email is sent automatically in this version.

## Tech Stack

- Python 3.12
- FastAPI and Pydantic
- LangGraph and LangChain Core tools
- SQLAlchemy 2 and SQLite
- Local vector-search abstraction
- pytest and pytest-cov
- Ruff and strict mypy
- GitHub Actions

## Repository Layout

```text
backend/
  src/
    job_search_assistant/
      agents/          # focused workflow participants
      api/routes/      # FastAPI endpoints
      core/            # settings, logging, exceptions
      database/        # engine, sessions, declarative base
      models/          # SQLAlchemy models
      repositories/    # persistence boundary
      schemas/         # Pydantic contracts
      services/        # application use cases
      tools/           # parsing, retrieval, email, LangChain adapters
      workflows/       # LangGraph topology and typed state
  tests/
frontend/            # future Next.js dashboard plan
docs/                # architecture, workflow, API, test, and demo docs
```

## Run Locally

Prerequisite: Python 3.12.

```bash
git clone https://github.com/pavansae99/agentic-ai-job-search-assistant.git
cd agentic-ai-job-search-assistant/backend
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
uvicorn --app-dir src job_search_assistant.main:app --reload
```

Open:

- API documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Health check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

Configuration is read from environment variables or `.env`. Copy `.env.example` to `.env` only
when local overrides are needed.

## Test And Quality Commands

Run from `backend/`:

```bash
pytest --cov=job_search_assistant --cov-report=term-missing
ruff check .
ruff format --check .
mypy src/job_search_assistant
```

Coverage fails below 80%. The initial suite covers agents, parser tools, scoring, ranking, local
retrieval, repository/service behavior, API contracts, and the complete graph happy path.

See [docs/testing-strategy.md](docs/testing-strategy.md).

## API Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Process health |
| `POST` | `/api/profile/analyze` | Parse a resume and return coaching |
| `POST` | `/api/jobs/analyze` | Parse a job description |
| `POST` | `/api/jobs/match` | Run the complete agent workflow |
| `POST` | `/api/applications` | Track an application |
| `GET` | `/api/applications` | List applications |
| `PATCH` | `/api/applications/{application_id}` | Update status or notes |

Full examples are in [docs/api-contract.md](docs/api-contract.md).

## Application Tracking

Tracked fields include company, title, location, URL, score, notes, timestamps, and status.
Supported statuses are:

`saved`, `applied`, `recruiter_contacted`, `interview`, `rejected`, `offer`

SQLite is appropriate for the single-user MVP. The repository and service layers allow migration
to PostgreSQL without changing API handlers or agent logic.

## Security And Privacy

- Use only synthetic sample data from `backend/tests/fixtures`.
- Never commit a real resume or personally identifiable information.
- Never commit API keys; use environment variables and `.env`.
- Treat job descriptions and retrieved documents as untrusted input.
- Add authentication, per-user authorization, encryption, retention policies, and audit logs
  before storing real candidate data.
- Require user approval before any external communication.

## Roadmap

1. Add provider-neutral LLM extraction and email-polish adapters with structured output.
2. Add Chroma or pgvector embeddings, document provenance, and retrieval evaluation.
3. Add LangGraph checkpointing and human approval interrupts.
4. Add authentication and PostgreSQL migrations with Alembic.
5. Add job-source connectors behind rate-limited, policy-aware tools.
6. Build the Next.js dashboard described in `frontend/README.md`.
7. Add observability, prompt/version tracing, offline evaluations, and score calibration.

## Interview Talking Points

- Why scoring is deterministic while language generation is replaceable.
- How typed graph state reduces hidden coupling between agents.
- Why agents and tools are separate concepts.
- Where LangGraph adds value beyond a sequential function call.
- How a retrieval interface supports RAG without locking into Chroma.
- Where to place human approval, checkpointing, retries, and idempotency.
- How repository and service boundaries support a SQLite-to-PostgreSQL migration.
- How the reasoning trace supports debugging without exposing private chain-of-thought.
- Which tests protect policy behavior versus framework integration.
- Which privacy controls are required before processing real resumes.

For a concise walkthrough, use [docs/demo-script.md](docs/demo-script.md).
