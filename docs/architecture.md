# Architecture

## Context

The system accepts sensitive candidate text and untrusted job descriptions, produces an
explainable recommendation, and persists application workflow state. The architecture therefore
optimizes for explicit contracts, replaceable AI providers, deterministic policy, and testability.

## System Diagram

```text
                         +----------------------+
                         |  Next.js dashboard   |
                         |  (future)            |
                         +----------+-----------+
                                    |
                                    | HTTPS / JSON
                                    v
+----------------+       +----------+-----------+
| API consumers  +------>| FastAPI route layer |
+----------------+       +----------+-----------+
                                    |
                                    v
                         +----------+-----------+
                         | Application services |
                         +----+-------------+---+
                              |             |
                              v             v
                   +----------+---+   +-----+----------------+
                   | LangGraph    |   | Application service |
                   | workflow     |   +-----+----------------+
                   +------+-------+         |
                          |                 v
                          v           +-----+------+
                   +------+-------+   | Repository |
                   | Agents       |   +-----+------+
                   +------+-------+         |
                          |                 v
                          v           +-----+------+
                   +------+-------+   | SQLAlchemy |
                   | Tools        |   +-----+------+
                   +------+-------+         |
                          |                 v
                    +-----+------+     +----+---+
                    | Local/Chroma|     | SQLite |
                    | retrieval   |     +--------+
                    +------------+
```

## Layer Responsibilities

The backend uses the `src/job_search_assistant` package layout. This prevents accidental imports
from the repository root and gives the installed Python package a descriptive, collision-resistant
name.

`api` validates transport input, selects response models, and translates domain exceptions.
Routes do not implement scoring or database queries.

`services` represent use cases. They coordinate agents, workflows, and repositories without
depending on HTTP.

`workflows` define graph topology and the state contract. A node returns only the fields it owns.

`agents` apply one decision or transformation. They are provider-neutral and accept dependencies
through constructors.

`tools` perform concrete operations. Current parsing, scoring support, email generation, and
retrieval are deterministic. LangChain adapters expose selected tools for future model-driven
selection.

`repositories` isolate SQLAlchemy query behavior. Services own not-found policy and response
mapping.

`schemas` are typed contracts shared at controlled boundaries. `models` are persistence-specific.

## Key Decisions

### Deterministic First

Resume parsing is intentionally lightweight and scoring is deterministic. This establishes a
reliable baseline for tests, demos, and future LLM evaluation. Model output should improve
extraction recall or writing quality, not silently redefine authorization or ranking policy.

### Typed State

`JobMatchState` is the contract between nodes. It prevents nodes from relying on hidden globals
and makes checkpoint serialization feasible. The `reasoning_trace` reducer appends concise
execution facts; it is an audit summary, not private chain-of-thought.

### Repository Boundary

SQLite can be replaced with PostgreSQL by changing engine configuration and migrations. Routes
and workflow nodes do not know which database is used.

### Replaceable Retrieval

The vector tool currently stores documents in memory and calculates cosine similarity from term
frequencies. A production adapter should add embeddings, durable storage, tenant isolation,
metadata filters, provenance, and retrieval-quality evaluation.

## Reliability And Scale

The MVP executes synchronously because each operation is local and bounded. At production scale:

- Move expensive parsing and embedding work to a task queue.
- Use request and workflow identifiers for idempotency.
- Add retries only around transient provider or database failures.
- Store LangGraph checkpoints for resumable human review.
- Add database migrations and connection pooling.
- Emit structured traces, metrics, and redacted logs.

## Security Boundaries

Resume and job text must be treated as sensitive and untrusted. Production controls should include
authentication, object-level authorization, encrypted storage, retention/deletion workflows,
prompt-injection defenses, output validation, egress controls, audit logs, and explicit approval
before sending communication.
