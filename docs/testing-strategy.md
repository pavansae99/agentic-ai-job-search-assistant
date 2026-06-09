# Testing Strategy

## Goals

Tests protect decision policy, graph contracts, persistence behavior, and HTTP integration without
calling paid or nondeterministic external services.

## Test Layers

Unit tests cover:

- Resume and job extraction, including sparse-input defaults.
- Weighted scoring and each recommendation threshold.
- Grounded email generation.
- Career-coaching behavior.
- Local vector search and input validation.
- LangChain tool registration and invocation.
- Repository/service create, list, update, and not-found behavior.

Workflow tests invoke the compiled LangGraph and assert final state, ranking, email, and trace.

Integration tests use FastAPI `TestClient` with a temporary SQLite database. They validate status
codes, serialized contracts, application lifecycle behavior, and request validation.

## Coverage

The configured minimum is 80% branch-aware coverage:

```bash
pytest --cov=job_search_assistant --cov-report=term-missing
```

Coverage is a guardrail, not the objective. High-value assertions focus on score calculations,
authorization compatibility, state transitions, and persistence outcomes.

## CI Gates

GitHub Actions runs on pushes and pull requests:

1. Install the package with development dependencies.
2. Run Ruff lint checks.
3. Verify Ruff formatting.
4. Run strict mypy against application code.
5. Run pytest with branch coverage and the 80% threshold.

## Future Testing

- Property-based tests for score bounds and monotonicity.
- Golden datasets for parser and ranking evaluation.
- Contract tests for Chroma or pgvector adapters.
- Prompt and structured-output regression tests for each model provider.
- Checkpoint/resume and human-approval tests.
- PostgreSQL migration and concurrency tests.
- Security tests for prompt injection, authorization, and data deletion.
