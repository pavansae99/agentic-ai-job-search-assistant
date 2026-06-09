# Phase 1 LLM Hardening

## Status

Phase 1 hardening is implemented on `feature/llm-provider-layer`.

The phase strengthens the existing provider integration without adding frontend work, RAG,
planner agents, authentication, or new public API fields.

## Implemented

### Configuration Safety

- `auto` uses OpenAI only when a non-blank key exists.
- `auto` without a key uses deterministic local tools.
- `mock` always uses deterministic local tools.
- `openai` without a usable key raises `LLMProviderConfigurationError` during startup.

### Typed Errors

The provider boundary now distinguishes configuration, authentication, rate-limit, timeout,
transient, invalid-response, and refusal failures. Runtime failures remain redacted as HTTP `503`
responses while internal logs retain category and request-ID metadata.

### Response State Handling

The OpenAI adapter rejects:

- Model refusals.
- Incomplete responses, including the documented incomplete reason.
- Failed, cancelled, queued, and other non-completed responses.
- Completed responses without parsed structured output.
- SDK or Pydantic response-validation failures.

### Shared Lifecycle

`ApplicationContainer` is initialized once during FastAPI lifespan. It owns one provider, one SDK
client, shared services, and one compiled LangGraph workflow. The provider is closed during
shutdown.

### Version Metadata

Resume extraction, job extraction, and recruiter-email prompts have explicit version constants.
Existing reasoning traces now include provider, model, and prompt version without changing public
response schemas.

### Verification

The hardening suite includes provider selection, error mapping, refusal/incomplete handling,
metadata, client configuration, shared lifecycle, and shutdown tests.

Current result: 61 tests pass with 95.56% branch-aware coverage; Ruff, formatting, and strict mypy
also pass.

## Tradeoffs

- Runtime provider categories are intentionally not exposed to API callers.
- All runtime categories currently return `503`; stable public error codes are deferred.
- The configured workflow deadline is a placeholder and is not yet enforced.
- The default model remains an alias for developer convenience; production snapshot pinning is
  deferred.
- `MockProvider` retains its existing name to avoid unrelated renaming in this focused phase.

## Deferred

- End-to-end workflow cancellation.
- Circuit breakers and load shedding.
- Authentication, quotas, rate limiting, and spend controls.
- Extraction confidence, source evidence, and human review.
- Structured usage, cost, latency, and retry telemetry.
- Production model snapshot pinning and golden-dataset evaluation gates.
