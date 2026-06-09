# Agent Workflow

## Graph

```text
START
  -> resume_analysis
  -> job_analysis
  -> match_scoring
  -> fit_ranking
  -> recruiter_email
  -> END
```

The graph is built with LangGraph `StateGraph` and compiled once per workflow instance.

## State

| Field | Owner | Purpose |
|---|---|---|
| `raw_resume_text` | caller | Original resume input |
| `parsed_profile` | ResumeAnalysisAgent | Validated candidate facts |
| `raw_job_description` | caller | Original job input |
| `parsed_job` | JobAnalysisAgent | Validated job requirements |
| `scoring` | MatchScoringAgent | Component scores and explanations |
| `match_score` | MatchScoringAgent | Final numeric score |
| `missing_keywords` | MatchScoringAgent | Missing required skills |
| `ranking` | FitRankingAgent | Recommendation band |
| `recruiter_email` | RecruiterEmailAgent | Grounded outreach draft |
| `reasoning_trace` | all nodes | Append-only execution summary |

## Nodes

`ResumeAnalysisAgent` calls `ResumeParserTool` and emits a `CandidateProfile`.

`JobAnalysisAgent` calls `JobParserTool` and separates required from preferred qualifications.

`MatchScoringAgent` calls `MatchScoringService` to compute skill, experience, location, and
authorization scores. It also identifies missing required keywords.

`FitRankingAgent` maps the final score to a stable category. Keeping thresholds in code makes policy
changes visible in review and tests.

`RecruiterEmailAgent` uses only matched profile facts. Missing job skills are excluded so outreach
does not invent experience.

`CareerCoachAgent` runs against the completed graph result and produces truthful next actions.

## Tool Calling

The deterministic path invokes tools directly. `build_tool_registry()` exposes parser tools as
LangChain `BaseTool` objects with Pydantic input schemas. A future LLM-based planner can select
from that registry while the workflow still validates state before advancing.

## Human Review Extension

A production graph can insert an `approval` node between ranking and email:

```text
fit_ranking
  -> route_for_review
       -> approval_interrupt -> recruiter_email
       -> recruiter_email
```

Review should trigger for uncertain authorization, conflicting parsed facts, near-threshold scores,
or any external side effect. LangGraph checkpointing can persist state while waiting for user
input and resume from the exact node afterward.

## Failure Policy

- Pydantic rejects invalid state at system boundaries.
- Deterministic node failures are not retried blindly.
- Future provider calls should retry only transient failures with bounded backoff.
- External actions should use idempotency keys.
- Logs and traces must redact resume content and secrets.
