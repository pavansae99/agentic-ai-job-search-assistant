"""LangGraph orchestration for the resume-to-outreach workflow."""

from typing import Any, cast

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from job_search_assistant.agents.career_coach_agent import CareerCoachAgent
from job_search_assistant.agents.fit_ranking_agent import FitRankingAgent
from job_search_assistant.agents.job_analysis_agent import JobAnalysisAgent
from job_search_assistant.agents.match_scoring_agent import MatchScoringAgent
from job_search_assistant.agents.recruiter_email_agent import RecruiterEmailAgent
from job_search_assistant.agents.resume_analysis_agent import ResumeAnalysisAgent
from job_search_assistant.schemas.job import JobMatchResponse
from job_search_assistant.workflows.job_match_state import JobMatchState


class JobMatchWorkflow:
    """Build and execute the typed multi-agent graph."""

    def __init__(
        self,
        resume_analysis_agent: ResumeAnalysisAgent | None = None,
        job_analysis_agent: JobAnalysisAgent | None = None,
        match_scoring_agent: MatchScoringAgent | None = None,
        fit_ranking_agent: FitRankingAgent | None = None,
        recruiter_email_agent: RecruiterEmailAgent | None = None,
        career_coach_agent: CareerCoachAgent | None = None,
    ) -> None:
        self._resume_analysis_agent = resume_analysis_agent or ResumeAnalysisAgent()
        self._job_analysis_agent = job_analysis_agent or JobAnalysisAgent()
        self._match_scoring_agent = match_scoring_agent or MatchScoringAgent()
        self._fit_ranking_agent = fit_ranking_agent or FitRankingAgent()
        self._recruiter_email_agent = recruiter_email_agent or RecruiterEmailAgent()
        self._career_coach_agent = career_coach_agent or CareerCoachAgent()
        self.graph = self._build_graph()

    def _build_graph(
        self,
    ) -> CompiledStateGraph[JobMatchState, None, JobMatchState, JobMatchState]:
        graph = StateGraph(JobMatchState)
        graph.add_node("resume_analysis", self._analyze_resume)
        graph.add_node("job_analysis", self._analyze_job)
        graph.add_node("match_scoring", self._score_match)
        graph.add_node("fit_ranking", self._rank_fit)
        graph.add_node("recruiter_email", self._draft_recruiter_email)
        graph.add_edge(START, "resume_analysis")
        graph.add_edge("resume_analysis", "job_analysis")
        graph.add_edge("job_analysis", "match_scoring")
        graph.add_edge("match_scoring", "fit_ranking")
        graph.add_edge("fit_ranking", "recruiter_email")
        graph.add_edge("recruiter_email", END)
        return graph.compile()

    def run(self, raw_resume_text: str, raw_job_description: str) -> JobMatchResponse:
        """Run the graph and map its final state to an API response."""

        result = cast(
            JobMatchState,
            self.graph.invoke(
                {
                    "raw_resume_text": raw_resume_text,
                    "raw_job_description": raw_job_description,
                    "reasoning_trace": [],
                }
            ),
        )
        profile = result["parsed_profile"]
        job = result["parsed_job"]
        scoring = result["scoring"]
        suggestions = self._career_coach_agent.review_match(
            profile,
            job,
            scoring,
            result["missing_keywords"],
        )
        trace = [
            *result["reasoning_trace"],
            "CareerCoachAgent generated grounded improvement suggestions.",
        ]
        return JobMatchResponse(
            parsed_profile=profile,
            parsed_job=job,
            scoring=scoring,
            ranking=result["ranking"],
            missing_keywords=result["missing_keywords"],
            recruiter_email=result["recruiter_email"],
            career_suggestions=suggestions,
            reasoning_trace=trace,
        )

    def _analyze_resume(self, state: JobMatchState) -> dict[str, Any]:
        profile = self._resume_analysis_agent.run(state["raw_resume_text"])
        return {
            "parsed_profile": profile,
            "reasoning_trace": [
                f"ResumeAnalysisAgent extracted {len(profile.skills)} skills and "
                f"{profile.years_of_experience:g} years of experience."
            ],
        }

    def _analyze_job(self, state: JobMatchState) -> dict[str, Any]:
        job = self._job_analysis_agent.run(state["raw_job_description"])
        return {
            "parsed_job": job,
            "reasoning_trace": [
                f"JobAnalysisAgent extracted {len(job.required_skills)} required skills."
            ],
        }

    def _score_match(self, state: JobMatchState) -> dict[str, Any]:
        scoring, missing = self._match_scoring_agent.run(
            state["parsed_profile"],
            state["parsed_job"],
        )
        return {
            "scoring": scoring,
            "match_score": scoring.final_score,
            "missing_keywords": missing,
            "reasoning_trace": [
                f"MatchScoringAgent calculated a weighted score of {scoring.final_score:.2f}."
            ],
        }

    def _rank_fit(self, state: JobMatchState) -> dict[str, Any]:
        ranking = self._fit_ranking_agent.run(state["match_score"])
        return {
            "ranking": ranking,
            "reasoning_trace": [f"FitRankingAgent classified the role as {ranking.value}."],
        }

    def _draft_recruiter_email(self, state: JobMatchState) -> dict[str, Any]:
        email = self._recruiter_email_agent.run(
            state["parsed_profile"],
            state["parsed_job"],
            state["ranking"],
            state["missing_keywords"],
        )
        return {
            "recruiter_email": email,
            "reasoning_trace": [
                "RecruiterEmailAgent generated outreach grounded in matched candidate skills."
            ],
        }
