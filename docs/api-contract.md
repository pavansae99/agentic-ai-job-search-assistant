# API Contract

Base URL: `http://127.0.0.1:8000`

FastAPI also publishes OpenAPI documentation at `/docs`.

## Health

`GET /health`

```json
{
  "status": "healthy",
  "service": "agentic-ai-job-search-assistant",
  "version": "0.1.0"
}
```

## Analyze Profile

`POST /api/profile/analyze`

```json
{
  "raw_resume_text": "Senior Software Engineer with 9 years of experience..."
}
```

The response contains `profile`, `career_suggestions`, and `reasoning_trace`.

## Analyze Job

`POST /api/jobs/analyze`

```json
{
  "raw_job_description": "Company: Acme Cloud\nTitle: Senior Backend Engineer..."
}
```

The response contains normalized required skills, preferred skills, minimum experience, location,
and work-authorization requirements.

## Match Resume To Job

`POST /api/jobs/match`

```json
{
  "raw_resume_text": "Senior Software Engineer with 9 years...",
  "raw_job_description": "Senior Backend Engineer requiring Python..."
}
```

Representative response:

```json
{
  "parsed_profile": {
    "skills": ["Go", "Kafka", "Kubernetes", "Python"],
    "years_of_experience": 9,
    "target_roles": ["Senior Software Engineer"],
    "location_preferences": ["Remote"],
    "work_authorization": "Authorized to work in the US without sponsorship",
    "summary": "9 years of experience; 4 recognized skills..."
  },
  "parsed_job": {
    "title": "Senior Backend Engineer",
    "company": "Acme Cloud",
    "required_skills": ["Go", "Kafka", "Kubernetes", "Python"],
    "preferred_skills": ["LangGraph"],
    "minimum_years_experience": 7,
    "location": "Remote",
    "work_authorization_requirement": "US work authorization required; sponsorship unavailable",
    "summary": "Senior Backend Engineer requiring..."
  },
  "scoring": {
    "skill_score": 100,
    "experience_score": 100,
    "location_score": 100,
    "authorization_score": 100,
    "final_score": 100,
    "weights": {
      "skills": 0.5,
      "experience": 0.2,
      "location": 0.15,
      "authorization": 0.15
    },
    "explanations": {
      "skills": "Matched 4 of 4 required skills."
    }
  },
  "ranking": "Strong Fit",
  "missing_keywords": [],
  "recruiter_email": "Subject: Interest in Senior Backend Engineer at Acme Cloud...",
  "career_suggestions": ["Lead with quantified impact..."],
  "reasoning_trace": ["ResumeAnalysisAgent extracted...", "JobAnalysisAgent extracted..."]
}
```

## Create Application

`POST /api/applications`

```json
{
  "company": "Acme Cloud",
  "title": "Senior Backend Engineer",
  "location": "Remote",
  "job_url": "https://example.com/jobs/123",
  "status": "saved",
  "match_score": 94.5,
  "notes": "High-priority role"
}
```

Returns `201 Created` with the generated ID and timestamps.

## List Applications

`GET /api/applications`

Returns application records newest first.

## Update Application

`PATCH /api/applications/{application_id}`

```json
{
  "status": "interview",
  "notes": "Technical interview scheduled"
}
```

Valid statuses are `saved`, `applied`, `recruiter_contacted`, `interview`, `rejected`, and
`offer`. An unknown ID returns `404`; invalid or empty payloads return `422`.
