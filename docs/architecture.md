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
                         +----------+-----------+
                                    |
             +----------------------+----------------------+
             |                                             |
             v                                             v
   +---------+----------+                      +-----------+----------+
   | LangGraph workflow |                      | Application tracking |
   +---------+----------+                      +-----------+----------+
             |                                             |
       +-----+------------------+                          v
       |                        |                   +------+------+
       v                        v                   | Repository  |
+------+--------+       +-------+----------+        +------+------+
| AI-facing    |       | Scoring/ranking |               |
| agents       |       | agents          |               v
+------+--------+       +-------+----------+        +------+------+
       |                        |                   | SQLAlchemy  |
       v                        v                   +------+------+
+------+--------+       +-------+----------+               |
| LLMProvider  |       | Deterministic    |               v
+---+------+---+       | scoring policy   |          +----+---+
    |      |           +------------------+          | SQLite |
    |      |                                         +--------+
    v      v
+---+---+  +----------+
| OpenAI|  | Mock     |
| API   |  | provider |
+-------+  +-----+----+
                   |
                   v
             +-----+-------------+
             | Deterministic     |
             | parsing and email |
             +-------------------+

VectorSearchTool -> local lexical index -> future Chroma/pgvector adapter
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

`llm` owns provider selection, OpenAI SDK integration, deterministic fallback, structured-output
schemas, timeout/retry configuration, and provider error normalization. Agents import only the
provider protocol.

`schemas` are typed contracts shared at controlled boundaries. `models` are persistence-specific.

## Key Decisions

### Deterministic First

Resume parsing is intentionally lightweight and scoring is deterministic. This establishes a
reliable baseline for tests, demos, and future LLM evaluation. Model output should improve
extraction recall or writing quality, not silently redefine authorization or ranking policy.

### Configuration-Time Fallback

`LLM_PROVIDER=auto` uses OpenAI only when a non-blank key is present. Missing credentials select
the deterministic provider before a workflow starts. An OpenAI failure after execution begins is
returned as a typed service error rather than silently switching implementations. This makes
quality, latency, and reasoning traces consistent within one request.

One provider instance is injected into all AI-facing agents in a workflow. This keeps credentials
and SDK construction at the composition boundary and makes provider behavior easy to replace in
tests.

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
