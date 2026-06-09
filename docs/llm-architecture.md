# LLM Provider Architecture

## Purpose

The provider layer adds model-backed extraction and drafting without allowing an LLM to own
scoring policy, persistence, HTTP contracts, or workflow topology. Phase 1 hardening adds strict
configuration, typed failures, refusal and incomplete-response handling, versioned provenance,
and an application-scoped provider lifecycle.

## Components

```text
FastAPI lifespan
    |
ApplicationContainer
    +--- one LLMProvider / SDK client
    +--- one ProfileAnalysisService
    +--- one JobAnalysisService
             |
             +--- one compiled JobMatchWorkflow
                         |
              +----------+-----------+
              |          |           |
         ResumeAgent   JobAgent   EmailAgent
              \          |          /
                    LLMProvider
                    /         \
            OpenAIProvider   MockProvider
                 |               |
          Responses API     deterministic tools

Validated facts -> deterministic scoring -> deterministic ranking
```

Files:

- `container.py`: application-scoped provider and service composition.
- `api/dependencies.py`: FastAPI access to shared services.
- `llm/provider.py`: protocol, typed errors, and provider factory.
- `llm/openai_provider.py`: OpenAI Responses API adapter.
- `llm/mock_provider.py`: deterministic implementation.
- `llm/prompts.py`: versioned provider instructions.
- `llm/schemas.py`: provider output and provenance schemas.

## Provider Contract

```python
class LLMProvider(Protocol):
    @property
    def name(self) -> str: ...

    def extract_resume_profile(self, raw_resume_text: str) -> CandidateProfile: ...
    def extract_job_requirements(self, raw_job_description: str) -> ParsedJob: ...
    def generate_recruiter_email(...) -> str: ...

    def metadata_for(self, operation: LLMOperation) -> LLMProviderMetadata: ...
    def close(self) -> None: ...
```

Agents depend on this protocol and have no OpenAI imports. The container creates one provider,
injects it into all AI-facing services and agents, and closes it during FastAPI shutdown.

## Selection And Configuration Safety

| `LLM_PROVIDER` | API key | Result |
|---|---|---|
| `auto` | present | Start with `OpenAIProvider` |
| `auto` | missing or blank | Start with deterministic `MockProvider` |
| `mock` | any | Start with deterministic `MockProvider` |
| `openai` | present | Start with `OpenAIProvider` |
| `openai` | missing or blank | Fail startup with `LLMProviderConfigurationError` |

Fallback happens only during configuration. Once OpenAI is selected, a runtime failure does not
silently rerun the request with a different implementation.

## Shared Lifecycle

FastAPI lifespan builds `ApplicationContainer` once:

```text
startup
  -> validate provider configuration
  -> create provider and OpenAI client
  -> create services
  -> compile LangGraph workflow

requests
  -> resolve shared services from app.state

shutdown
  -> close provider and OpenAI HTTP client
```

This reuses the HTTP connection pool and compiled graph while keeping graph invocation state
request-scoped. Tests can supply an isolated container factory or provider.

## Structured Output Flow

The adapter uses the Responses API with Pydantic Structured Outputs:

```python
response = client.responses.parse(
    model=settings.openai_model,
    instructions=RESUME_EXTRACTION_INSTRUCTIONS,
    input=raw_resume_text,
    text_format=ResumeProfileExtraction,
    store=False,
)
```

The provider inspects response state before accepting `output_parsed`:

1. Scan output content for a model refusal.
2. Reject `incomplete` responses and record the incomplete reason.
3. Reject failed, cancelled, queued, or other non-completed responses.
4. Reject a completed response without parsed structured output.
5. Convert validated provider schemas to stable domain schemas.

Structured output guarantees schema adherence, not factual correctness. Evidence spans,
confidence, evaluation datasets, and human review remain required before high-stakes use.

## Error Taxonomy

| Error | Meaning | Retryable |
|---|---|---|
| `LLMProviderConfigurationError` | Missing explicit credentials or invalid request/model configuration | No |
| `LLMProviderAuthenticationError` | Invalid credentials or provider permission failure | No |
| `LLMProviderRateLimitError` | Provider rate limit | Yes |
| `LLMProviderTimeoutError` | SDK request timeout | Yes |
| `LLMProviderTransientError` | Connection, conflict, or provider server failure | Yes |
| `LLMProviderInvalidResponseError` | Failed, incomplete, malformed, or unparseable response | No |
| `LLMProviderRefusalError` | Model refusal | No |

FastAPI returns a generic `503` for runtime provider failures. Logs contain the internal category,
retryable flag, and provider request ID when available, but not resume text, job text, prompts, API
keys, or provider response bodies.

Configuration errors raised during container construction fail application startup rather than
being translated into an HTTP response.

## Model And Prompt Provenance

Version constants are defined in `llm/prompts.py`:

- `resume-extraction-v1`
- `job-extraction-v1`
- `recruiter-email-v1`

Internal reasoning traces include:

```text
provider=openai model=gpt-5.4-mini prompt_version=resume-extraction-v1
```

The public response schemas are unchanged because metadata is embedded in the existing
`reasoning_trace`. Production deployments should pin a model snapshot and add structured
telemetry before using prompt metadata for evaluation or rollback.

## Deterministic Control Boundary

The provider can improve extraction and drafting. It cannot change:

- Component weights.
- Score calculations.
- Ranking thresholds.
- Application status rules.
- Persistence behavior.
- Whether an email is sent.

```text
untrusted text
    -> provider extraction
    -> response-state checks
    -> Pydantic validation
    -> deterministic scoring
    -> deterministic ranking
    -> grounded provider drafting
```

## Timeout And Retry Policy

```dotenv
OPENAI_TIMEOUT_SECONDS=30
OPENAI_MAX_RETRIES=2
# LLM_WORKFLOW_DEADLINE_SECONDS=90
```

Timeout and retry values configure each SDK operation. The deadline setting is reserved for a
future end-to-end cancellation implementation and is intentionally not enforced in Phase 1.
Circuit breakers are also deferred.

## Security And Privacy

- Resume and job text are treated as untrusted data.
- Prompts prohibit following instructions embedded in source text.
- Output must satisfy constrained Pydantic schemas.
- `store=False` is sent on Responses API requests.
- API keys use `SecretStr` and environment variables.
- Tests use deterministic or fake clients and never make provider requests.
- Shared clients do not store candidate text in application state.

Real candidate data still requires authentication, authorization, consent, quotas, retention and
deletion controls, provider-policy review, spend controls, and a data-processing assessment.

## Test Strategy

Provider and lifecycle tests verify:

- Every provider selection and missing-key case.
- Explicit OpenAI startup failure.
- Timeout and retry forwarding.
- Structured schema and `store=False` forwarding.
- Authentication, permission, rate-limit, timeout, connection, conflict, server, bad-request, and
  generic SDK error mapping.
- Refusal, incomplete, non-completed, and parse-failure responses.
- Versioned provider metadata.
- One provider reused across requests and closed once.
- End-to-end LangGraph injection with deterministic scoring.
- Redacted HTTP provider failures.

## Deferred Work

1. End-to-end workflow deadlines and cancellation.
2. Authentication, quotas, rate limiting, and spend controls.
3. Extraction evidence, confidence, and human review.
4. Pinned production model snapshots and evaluation gates.
5. Usage, cost, latency, retry, and request-ID telemetry.
6. Circuit breaking and load shedding.
7. Provider contract tests against a dedicated non-production project.

## References

- [OpenAI Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs)
- [OpenAI Python SDK](https://github.com/openai/openai-python)
- [OpenAI data controls](https://developers.openai.com/api/docs/guides/your-data)
