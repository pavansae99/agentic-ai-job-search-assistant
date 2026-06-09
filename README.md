# Agentic AI Job Search Assistant

[![Backend CI](https://github.com/pavansae99/agentic-ai-job-search-assistant/actions/workflows/backend-ci.yml/badge.svg)](https://github.com/pavansae99/agentic-ai-job-search-assistant/actions/workflows/backend-ci.yml)

An interview-ready backend system that turns a resume and job description into an explainable
fit decision, missing-keyword analysis, recruiter outreach, career coaching, and a persisted
application record.

This is not a chat completion wrapped in an API. The system separates domain tools, specialized
agents, a provider-neutral LLM boundary, typed workflow state, orchestration, persistence, and
transport concerns so each can be tested and evolved independently. It can run with OpenAI
Structured Outputs or in a fully deterministic, API-key-free mode.

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
7. A typed `LLMProvider` protocol lets extraction and drafting use OpenAI without putting SDK
   imports, credentials, retries, or transport concerns inside agents.

`LLM_PROVIDER=auto` selects OpenAI when `OPENAI_API_KEY` is configured and otherwise falls back to
the deterministic provider. Tests force the deterministic provider. Pydantic validation and
deterministic scoring remain control boundaries regardless of which provider performs extraction
or drafting.

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

See [docs/agent-workflow.md](docs/agent-workflow.md) for node and state details and
[docs/llm-architecture.md](docs/llm-architecture.md) for provider selection and failure policy.

## Architecture

```text
HTTP clients
    |
FastAPI routes and Pydantic contracts
    |
Application services
    |
+--- JobMatchWorkflow -------------------+
|                                         |
|    +--- AI-facing agents                +--- Application tracking
|    |        |                                    |
|    |    LLMProvider                         Repository
|    |      /     \                                 |
|    | OpenAI    Mock                         SQLAlchemy
|    |    |        |                                |
|    | Structured  Deterministic tools             SQLite
|    | Outputs
|    |
|    +--- Scoring and ranking agents
|             |
|        Deterministic policy
```

Key boundaries:

- `api/`: HTTP routing and dependency injection.
- `services/`: use-case orchestration independent of FastAPI.
- `workflows/`: graph topology and shared state.
- `agents/`: single-purpose decision or transformation units.
- `llm/`: provider protocol, factory, OpenAI adapter, deterministic fallback, and provider schemas.
- `tools/`: deterministic capabilities and LangChain adapters.
- `repositories/`: persistence operations.
- `schemas/`: validation and public contracts.
- `models/` and `database/`: SQLAlchemy persistence infrastructure.

Read the design decisions in [docs/architecture.md](docs/architecture.md).

## LLM Provider Layer

The workflow uses one provider instance for resume extraction, job extraction, and recruiter email
drafting. Agents depend only on `LLMProvider`; they never import the OpenAI SDK.

| Configuration | Runtime behavior |
|---|---|
| `LLM_PROVIDER=auto`, key present | Use `OpenAIProvider` |
| `LLM_PROVIDER=auto`, key absent or blank | Use deterministic `MockProvider` |
| `LLM_PROVIDER=mock` | Always use deterministic tools |
| `LLM_PROVIDER=openai`, key present | Use `OpenAIProvider` |
| `LLM_PROVIDER=openai`, key absent or blank | Fail application startup |

The OpenAI adapter uses the Responses API with native Pydantic Structured Outputs:

```python
response = client.responses.parse(
    model=settings.openai_model,
    instructions=trusted_system_instructions,
    input=untrusted_resume_or_job_text,
    text_format=ResumeProfileExtraction,
    store=False,
)
```

Provider output is validated at the boundary and converted to stable domain schemas. The adapter
uses bounded SDK retries and a configurable timeout. Authentication, rate-limit, timeout,
transient, invalid-response, and refusal failures have distinct internal types; FastAPI returns a
redacted `503`. Runtime failures do not silently switch algorithms.

FastAPI lifespan creates one provider/client, shared service set, and compiled LangGraph workflow.
Existing reasoning traces include provider, model, and versioned prompt metadata without changing
public response schemas.

The deterministic score remains authoritative:

```text
LLM or local tools -> validated facts -> deterministic score -> deterministic ranking
```

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
- OpenAI Python SDK and Structured Outputs
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
      llm/             # provider protocol and adapters
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

Run without an external model:

```bash
export LLM_PROVIDER=mock
```

Enable OpenAI:

```bash
export LLM_PROVIDER=openai
export OPENAI_API_KEY="your-key"
export OPENAI_MODEL="gpt-5.4-mini"
```

Never commit `.env` or an API key. `auto` is the default and requires no key for local startup.
Selecting `openai` explicitly requires a non-blank key and fails startup otherwise.

## Test And Quality Commands

Run from `backend/`:

```bash
pytest --cov=job_search_assistant --cov-report=term-missing
ruff check .
ruff format --check .
mypy src/job_search_assistant
```

Coverage fails below 90%. The suite covers provider selection, typed errors, refusal and incomplete
responses, shared lifecycle, structured OpenAI calls without network access, scoring, persistence,
API contracts, and the complete graph.

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
- The OpenAI adapter sends only the text required for the requested extraction or draft and sets
  `store=False`; review provider data controls before processing real candidate information.
- Provider errors are logged without resume or job content and returned to clients as a generic `503`.
- Add authentication, per-user authorization, encryption, retention policies, and audit logs
  before storing real candidate data.
- Require user approval before any external communication.

## 🚀 Roadmap

### Completed
- [x] FastAPI backend
- [x] LangGraph workflow orchestration
- [x] Multi-agent architecture
- [x] OpenAI Structured Outputs integration
- [x] Provider-agnostic LLM layer
- [x] Deterministic scoring engine
- [x] Application tracking with SQLite
- [x] Typed error handling
- [x] Shared provider lifecycle management
- [x] 95%+ automated test coverage
- [x] CI, Ruff, Mypy, and quality gates

### In Progress
- [ ] Human-in-the-loop review workflow
- [ ] Confidence scoring and evidence tracking
- [ ] End-to-end workflow deadlines

### Planned
- [ ] RAG with ChromaDB / pgvector
- [ ] Planner agent for autonomous job search actions
- [ ] Memory layer for applications and interview history
- [ ] Next.js + Tailwind dashboard
- [ ] Authentication and user accounts
- [ ] Rate limiting and usage controls
- [ ] Cost and token observability
- [ ] Multi-provider support (Gemini, Claude)
- [ ] Docker deployment
- [ ] PostgreSQL + Alembic migrations

## Interview Talking Points

- Why scoring is deterministic while language generation is replaceable.
- How typed graph state reduces hidden coupling between agents.
- Why agents and tools are separate concepts.
- Where LangGraph adds value beyond a sequential function call.
- Why the provider factory falls back only during configuration, not after a runtime model failure.
- How Structured Outputs and domain validation constrain probabilistic extraction.
- Why one injected provider instance is shared across a workflow invocation.
- How a retrieval interface supports RAG without locking into Chroma.
- Where to place human approval, checkpointing, retries, and idempotency.
- How repository and service boundaries support a SQLite-to-PostgreSQL migration.
- How the reasoning trace supports debugging without exposing private chain-of-thought.
- Which tests protect policy behavior versus framework integration.
- Which privacy controls are required before processing real resumes.

For a concise walkthrough, use [docs/demo-script.md](docs/demo-script.md).
