# Frontend Roadmap

The first release focuses on the backend and agent architecture. A future dashboard will use
Next.js, TypeScript, and a small component system.

Planned views:

- Candidate profile review with editable extracted facts.
- Job-description analysis and component score visualization.
- Human approval screen for recruiter outreach.
- Kanban-style application pipeline.
- Retrieval evidence and reasoning-trace inspection.
- Privacy controls for deleting candidate and application data.

The frontend should consume the documented FastAPI contract rather than duplicating scoring or
workflow policy in browser code.
