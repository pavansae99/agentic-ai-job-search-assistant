# LLM Integration Architecture Review

## Phase 1 Hardening Status

This review captured the pre-hardening provider layer. The following status supersedes resolved
findings while preserving the original review as architectural history.

| Review finding | Status |
|---|---|
| Explicit OpenAI configuration fails open | Resolved: startup now fails without a usable key |
| Provider and graph rebuilt per request | Resolved: FastAPI lifespan owns one shared container |
| Provider failures lack categories | Resolved: seven typed categories are implemented |
| Refusal and incomplete output are not distinguished | Resolved |
| Prompt versions are not tracked | Resolved in reasoning traces |
| Model alias is not reproducible | Partially resolved: model is traced; snapshot pinning remains |
| No end-to-end deadline | Deferred; a configuration placeholder documents the next boundary |
| Public spend, privacy, confidence, and evaluation controls | Deferred |

Implementation details are in [llm-hardening.md](llm-hardening.md).

## Executive Summary

The LLM integration is a strong first production-oriented increment and is suitable for a
portfolio demonstration. It uses the current OpenAI Responses API, native Pydantic Structured
Outputs, a provider protocol, constructor injection, deterministic fallback, bounded SDK
configuration, typed errors, and network-free tests. Deterministic scoring remains outside the
model boundary, which is the most important architectural decision in this change.

The integration is not ready for real candidate data or public traffic. After Phase 1 hardening,
the principal remaining risks are paid endpoints without authentication or rate limiting,
model-extracted facts being treated as authoritative without evidence or confidence,
retry-amplified end-to-end latency, and incomplete privacy and operational controls.

**Review recommendation:** approve for the portfolio MVP. Do not describe the system as
production-ready until the remaining production gaps in this document are addressed.

## Review Scope

This review covers:

1. `OpenAIProvider` implementation.
2. Provider abstraction and factory behavior.
3. Error and response handling.
4. Timeout and retry behavior.
5. Dependency injection and lifecycle management.
6. Test design and coverage quality.
7. Security and privacy implications.
8. Structured Outputs usage.
9. Operational readiness.
10. Maintainability and future provider support.

## Strengths

### Clear AI Boundary

- `LLMProvider` is small, typed, and owned by the consuming application rather than by the SDK.
- Agents do not import OpenAI classes or read credentials.
- Lazy provider imports keep the deterministic path independent from OpenAI runtime construction.
- One provider instance is shared across the AI-facing agents within a workflow.
- Existing API success contracts remain unchanged.

### Correct Control Placement

- OpenAI is used for probabilistic extraction and drafting.
- Skill, experience, location, authorization, final score, and ranking remain deterministic.
- The email agent receives validated matched skills and does not present missing skills as
  candidate experience.
- Provider output is converted into stable domain schemas before scoring.

### Appropriate OpenAI API Usage

- The implementation uses the Responses API, which is the primary API in the current Python SDK.
- `responses.parse(..., text_format=PydanticModel)` is an appropriate Structured Outputs pattern.
- Structured Outputs provide schema adherence rather than JSON syntax alone.
- `store=False` avoids default Responses application-state storage.
- `gpt-5.4-mini` supports both the Responses API and Structured Outputs.

### Sensible Reliability Baseline

- Timeout and retry counts are configurable and constrained by Pydantic.
- Timeout, connection, rate-limit, status, and generic SDK failures are normalized.
- API clients receive a redacted `503` response rather than provider internals.
- A missing or blank API key has deterministic behavior.

### Strong Initial Test Design

- Tests never require an API key or make an external request.
- A fake Responses client verifies schema selection, model forwarding, and `store=False`.
- SDK exception families are mapped through parameterized tests.
- Provider-factory paths include missing and blank keys.
- The workflow injection test proves that deterministic scoring remains authoritative.
- The HTTP error test confirms that upstream details are not returned to the caller.

## Prioritized Risks

### High: Public LLM Endpoints Can Create Unbounded Spend

The profile and job routes construct model-backed services without authentication, per-user
authorization, rate limiting, quotas, or request accounting. Once an API key is configured, a
public caller can trigger paid OpenAI requests. `/api/jobs/match` performs three sequential model
operations: resume extraction, job extraction, and email drafting.

Relevant code:

- `backend/src/job_search_assistant/api/routes/profiles.py`
- `backend/src/job_search_assistant/api/routes/jobs.py`

Required before public deployment:

- Authenticate every model-backed endpoint.
- Add per-user and global request/token budgets.
- Apply rate limiting at both application and gateway layers.
- Set project-level OpenAI spend and rate limits.
- Record usage, latency, provider, model, and outcome without recording resume content.

### High: Schema-Valid Extraction Is Not Necessarily Factually Correct

Structured Outputs guarantee that a response follows the schema; they do not prove that extracted
skills, years, location, or work authorization are supported by the source text. The workflow
currently passes model output directly into deterministic scoring. A hallucinated authorization
or experience value can therefore produce a precise but incorrect recommendation.

Relevant code:

- `backend/src/job_search_assistant/llm/schemas.py`
- `backend/src/job_search_assistant/workflows/job_match_workflow.py`

Recommended improvement:

- Return source evidence spans for important extracted fields.
- Add field-level confidence or `known`, `unknown`, and `conflicting` states.
- Route ambiguous authorization and near-threshold scores to human review.
- Prevent unknown fields from receiving perfect compatibility scores.
- Build a golden evaluation dataset and measure extraction precision and recall.

### High: Timeout Plus Retries Can Produce Excessive End-to-End Latency

The client uses a 30-second timeout and two retries by default. The SDK retries connection errors,
408, 409, 429, and server errors. Timed-out requests are also retried. A single provider operation
can therefore make up to three attempts. Because the match workflow performs three provider
operations sequentially, a rough worst-case budget can approach nine timed attempts, plus retry
backoff. The configured timeout is not an end-to-end workflow deadline.

Relevant code:

- `backend/src/job_search_assistant/core/settings.py`
- `backend/src/job_search_assistant/llm/openai_provider.py`

Recommended improvement:

- Define separate connect, read, write, and pool timeouts with `httpx.Timeout`.
- Add an end-to-end request or workflow deadline.
- Set retry policy per operation and error category.
- Consider fewer retries for synchronous user-facing requests.
- Emit retry count, attempt latency, and final failure reason.
- Add a circuit breaker or load-shedding policy for sustained provider failure.

### Resolved: Explicit OpenAI Configuration Failed Open

When `LLM_PROVIDER=openai` is configured without a usable key, the factory logs a warning and
returns `MockProvider`. This keeps development convenient, but it can hide a production
misconfiguration and silently change extraction quality.

Relevant code:

- `backend/src/job_search_assistant/llm/provider.py`

Recommended policy:

- `auto` plus no key: deterministic fallback is acceptable.
- `mock`: always deterministic.
- `openai` plus no key: fail application startup with a configuration error.
- Production environment plus `auto`: consider requiring an explicit provider choice.

### Resolved: Provider And LangGraph Objects Were Built Per Request

Each route creates a new service. Each service creates a provider, and job services compile a new
LangGraph workflow. This discards reusable HTTP connection pools, adds graph compilation overhead,
and leaves SDK client cleanup to garbage collection.

Relevant code:

- `backend/src/job_search_assistant/api/routes/profiles.py`
- `backend/src/job_search_assistant/api/routes/jobs.py`
- `backend/src/job_search_assistant/services/job_analysis_service.py`

Recommended improvement:

- Build the OpenAI client, provider, services, and compiled graph during application lifespan.
- Reuse them through FastAPI dependencies or application state.
- Close the SDK client explicitly during shutdown.
- Keep only invocation state request-scoped.

### Medium: All Provider Failures Become The Same `503`

Authentication failures, invalid model names, permission errors, malformed requests, rate limits,
timeouts, and provider server failures do not have the same operational meaning. Mapping all of
them to `LLMProviderError` and HTTP `503` makes client behavior simple but weakens diagnosis and
retry safety.

Relevant code:

- `backend/src/job_search_assistant/llm/openai_provider.py`
- `backend/src/job_search_assistant/main.py`

Recommended improvement:

- Separate transient, rate-limit, configuration, authentication, refusal, and invalid-response
  errors.
- Fail fast for authentication, permission, and model configuration errors.
- Include `Retry-After` when appropriate.
- Log OpenAI request IDs for successful and failed requests.
- Return stable internal error codes while keeping user-facing messages redacted.

### Resolved: Refusal And Incomplete Responses Were Not Distinguished

The implementation checks only `response.output_parsed is None`. OpenAI documents refusal output
and incomplete responses, including `max_output_tokens`, as conditions applications should handle.
The current behavior converts all such outcomes into a generic invalid-response error.

Recommended improvement:

- Inspect response status and output content before reading `output_parsed`.
- Map refusals, content filtering, incomplete output, and parse failures separately.
- Decide which outcomes are retryable.
- Add tests for refusal and incomplete-response paths.

### Medium: Model And Prompt Versions Are Not Reproducible

`gpt-5.4-mini` is a moving alias. OpenAI provides the snapshot
`gpt-5.4-mini-2026-03-17` for stable behavior. Prompt strings are source constants but have no
identifier in traces or evaluation results.

Recommended improvement:

- Pin a model snapshot in production and update it deliberately.
- Keep aliases available for experimentation.
- Assign a version to each extraction and email prompt.
- Record model snapshot, prompt version, latency, token usage, and provider request ID.
- Require golden-dataset evaluation before changing a model or prompt.

### Medium: `store=False` Is Necessary But Not A Complete Privacy Policy

Resume and work-authorization text is sensitive. `store=False` avoids Responses application-state
retention, but it does not by itself guarantee zero retention. OpenAI documents separate abuse
monitoring retention, and Zero Data Retention requires organizational approval and configuration.

Recommended improvement:

- Obtain explicit user consent before sending resume content to a provider.
- Document the exact provider, region, retention mode, and subprocessors.
- Evaluate Zero Data Retention or Modified Abuse Monitoring eligibility.
- Support regional processing where required.
- Minimize transmitted fields and redact contact details not needed for extraction.
- Add deletion, retention, audit, and incident-response procedures.

### Low: `MockProvider` Is A Misleading Runtime Name

The class is not only a test double; it is the supported deterministic runtime implementation and
can serve production requests. `DeterministicProvider` or `LocalProvider` would describe its
behavior more accurately. A separate mock or stub can remain test-only.

### Low: The Protocol May Become Too Broad

The current combined extraction and drafting protocol is reasonable for this scope. If provider
capabilities diverge, split it into focused protocols such as `ProfileExtractor`,
`JobRequirementsExtractor`, and `RecruiterEmailDrafter`. Do not split it before that distinction
provides a real implementation or testing benefit.

## Test Quality Review

The tests are materially better than coverage-only tests. They verify behavior at the provider,
workflow, and HTTP boundaries. The fake client also keeps the suite deterministic and inexpensive.

Remaining high-value tests:

- End-to-end deadline and retry-budget behavior after deadline enforcement is implemented.
- Prompt-injection fixtures that attempt to override extraction instructions.
- Evidence-grounding and hallucination regression cases.
- Token and character boundary cases.
- Structured log-redaction and successful request-ID observability.
- A gated provider contract test against a non-production OpenAI project.

The current fake implements only the small surface the adapter calls. That is appropriate for unit
tests, but it can drift from SDK behavior. A small optional contract test should complement it,
not replace it.

## Technical Debt

- Provider results do not include usage, latency, request ID, finish status, or confidence.
- No concurrency policy, rate limiter, circuit breaker, or provider health metric exists.
- No total workflow deadline or cancellation propagation exists.
- There is no dependency lock file, so SDK behavior can change within the allowed major version.
- The synchronous provider contract limits future high-concurrency deployment options.

## Production Gaps

Before processing real resumes or enabling public traffic, add:

- Authentication, authorization, quotas, and rate limiting.
- Total deadlines, granular timeouts, retry budgets, and circuit breaking.
- Provider request IDs, structured metrics, token/cost telemetry, and alerting.
- Pinned model snapshots and evaluation-gated prompt updates.
- Extraction evidence, confidence, evaluations, and human-review routing.
- Consent, retention, deletion, regional processing, and provider data-control policy.
- Secret management or workload identity instead of developer `.env` files.
- Staging and production OpenAI projects with separate access and spend limits.
- Load, concurrency, failure-injection, and recovery testing.

## Recommended Improvement Order

1. Add authentication, quotas, rate limiting, and project spend limits.
2. Define and enforce an end-to-end latency budget.
3. Add extraction evidence and human review for sensitive or uncertain facts.
4. Pin the production model snapshot and add evaluation gates.
5. Add request-ID, usage, cost, latency, retry, and outcome telemetry.
6. Complete privacy and data-retention controls for real candidate data.
7. Add golden-dataset evaluations and a gated provider contract test.

## Final Assessment

| Area | Assessment |
|---|---|
| Provider abstraction | Strong MVP boundary |
| OpenAI integration | Correct API and Structured Outputs approach |
| Deterministic scoring separation | Strong |
| Error handling | Strong Phase 1 classification and redaction |
| Timeout handling | Configured; no total deadline |
| Retry behavior | SDK-backed; latency and cost budget not controlled |
| Dependency injection | Shared application lifecycle implemented |
| Test quality | Strong provider/lifecycle baseline; model evaluation remains |
| Security | Safe repository practices; unsafe for public paid traffic |
| Privacy | `store=False` is good; production governance is incomplete |
| Observability | Minimal |
| Production readiness | Not production-ready |
| Portfolio readiness | Strong |

## References

- [OpenAI Python SDK: errors, request IDs, retries, timeouts, and client lifecycle](https://github.com/openai/openai-python)
- [OpenAI Structured Outputs guide](https://developers.openai.com/api/docs/guides/structured-outputs)
- [OpenAI data controls](https://developers.openai.com/api/docs/guides/your-data)
- [OpenAI production best practices](https://developers.openai.com/api/docs/guides/production-best-practices)
- [GPT-5.4 mini model capabilities and snapshots](https://developers.openai.com/api/docs/models/gpt-5.4-mini)
