"""OpenAI Responses API implementation of the LLM provider contract."""

from typing import NoReturn, TypeVar

import openai
from openai import OpenAI
from openai.types.responses import ParsedResponse
from pydantic import BaseModel, ValidationError

from job_search_assistant.llm.prompts import (
    EMAIL_DRAFT_INSTRUCTIONS,
    JOB_EXTRACTION_INSTRUCTIONS,
    PROMPT_VERSION_BY_OPERATION,
    RESUME_EXTRACTION_INSTRUCTIONS,
)
from job_search_assistant.llm.provider import (
    LLMProviderAuthenticationError,
    LLMProviderConfigurationError,
    LLMProviderInvalidResponseError,
    LLMProviderRateLimitError,
    LLMProviderRefusalError,
    LLMProviderTimeoutError,
    LLMProviderTransientError,
)
from job_search_assistant.llm.schemas import (
    JobRequirementsExtraction,
    LLMOperation,
    LLMProviderMetadata,
    RecruiterEmailDraft,
    ResumeProfileExtraction,
)
from job_search_assistant.schemas.job import ParsedJob
from job_search_assistant.schemas.profile import CandidateProfile
from job_search_assistant.schemas.scoring import FitCategory

StructuredOutput = TypeVar("StructuredOutput", bound=BaseModel)


class OpenAIProvider:
    """Use OpenAI Structured Outputs for extraction and drafting."""

    name = "openai"

    def __init__(
        self,
        api_key: str,
        model: str,
        timeout_seconds: float,
        max_retries: int,
        client: OpenAI | None = None,
    ) -> None:
        self._model = model
        self._client = client or OpenAI(
            api_key=api_key,
            timeout=timeout_seconds,
            max_retries=max_retries,
        )

    @property
    def model(self) -> str:
        """Return the configured OpenAI model identifier."""

        return self._model

    def extract_resume_profile(self, raw_resume_text: str) -> CandidateProfile:
        """Extract resume facts through a structured OpenAI response."""

        extraction = self._parse_structured(
            response_schema=ResumeProfileExtraction,
            instructions=RESUME_EXTRACTION_INSTRUCTIONS,
            input_text=raw_resume_text,
            operation=LLMOperation.RESUME_EXTRACTION,
        )
        return extraction.to_domain()

    def extract_job_requirements(self, raw_job_description: str) -> ParsedJob:
        """Extract job facts through a structured OpenAI response."""

        extraction = self._parse_structured(
            response_schema=JobRequirementsExtraction,
            instructions=JOB_EXTRACTION_INSTRUCTIONS,
            input_text=raw_job_description,
            operation=LLMOperation.JOB_EXTRACTION,
        )
        return extraction.to_domain()

    def generate_recruiter_email(
        self,
        profile: CandidateProfile,
        job: ParsedJob,
        ranking: FitCategory,
        matched_skills: list[str],
    ) -> str:
        """Generate a structured, grounded recruiter email draft."""

        input_text = (
            f"Candidate profile:\n{profile.model_dump_json()}\n\n"
            f"Job requirements:\n{job.model_dump_json()}\n\n"
            f"Fit ranking: {ranking.value}\n"
            f"Validated matched skills: {matched_skills}"
        )
        draft = self._parse_structured(
            response_schema=RecruiterEmailDraft,
            instructions=EMAIL_DRAFT_INSTRUCTIONS,
            input_text=input_text,
            operation=LLMOperation.RECRUITER_EMAIL,
        )
        return draft.render()

    def _parse_structured(
        self,
        response_schema: type[StructuredOutput],
        instructions: str,
        input_text: str,
        operation: LLMOperation,
    ) -> StructuredOutput:
        try:
            response = self._client.responses.parse(
                model=self._model,
                instructions=instructions,
                input=input_text,
                text_format=response_schema,
                store=False,
            )
        except (openai.AuthenticationError, openai.PermissionDeniedError) as exc:
            raise LLMProviderAuthenticationError(
                "The OpenAI credentials are invalid or unauthorized.",
                request_id=exc.request_id,
            ) from exc
        except openai.RateLimitError as exc:
            raise LLMProviderRateLimitError(
                "The OpenAI rate limit was exceeded.",
                request_id=exc.request_id,
            ) from exc
        except openai.APITimeoutError as exc:
            raise LLMProviderTimeoutError("The OpenAI request timed out.") from exc
        except openai.APIConnectionError as exc:
            raise LLMProviderTransientError("The OpenAI API could not be reached.") from exc
        except (openai.InternalServerError, openai.ConflictError) as exc:
            raise LLMProviderTransientError(
                "The OpenAI service encountered a transient failure.",
                request_id=exc.request_id,
            ) from exc
        except openai.APIResponseValidationError as exc:
            raise LLMProviderInvalidResponseError(
                "OpenAI returned a response that failed SDK validation.",
                response_kind="parse_failure",
                request_id=exc.response.headers.get("x-request-id"),
            ) from exc
        except (openai.LengthFinishReasonError, openai.ContentFilterFinishReasonError) as exc:
            raise LLMProviderInvalidResponseError(
                "OpenAI returned an incomplete response.",
                response_kind="incomplete",
            ) from exc
        except openai.APIStatusError as exc:
            self._raise_status_error(exc)
        except ValidationError as exc:
            raise LLMProviderInvalidResponseError(
                "OpenAI structured output failed schema validation.",
                response_kind="parse_failure",
            ) from exc
        except openai.APIError as exc:
            raise LLMProviderInvalidResponseError(
                "The OpenAI request failed before producing a valid response.",
                response_kind="provider_error",
            ) from exc

        self._raise_for_response_state(response, operation)
        if response.output_parsed is None:
            raise LLMProviderInvalidResponseError(
                "OpenAI returned no parsed structured output.",
                response_kind="parse_failure",
                request_id=self._response_request_id(response),
            )
        return response.output_parsed

    def metadata_for(self, operation: LLMOperation) -> LLMProviderMetadata:
        """Return OpenAI model and prompt provenance for internal traces."""

        return LLMProviderMetadata(
            provider=self.name,
            model=self._model,
            prompt_version=PROMPT_VERSION_BY_OPERATION[operation],
            operation=operation,
        )

    def close(self) -> None:
        """Close the shared OpenAI HTTP client."""

        self._client.close()

    @staticmethod
    def _raise_for_response_state(
        response: ParsedResponse[StructuredOutput],
        operation: LLMOperation,
    ) -> None:
        request_id = OpenAIProvider._response_request_id(response)
        for output_item in response.output:
            if output_item.type != "message":
                continue
            for content_item in output_item.content:
                if content_item.type == "refusal":
                    raise LLMProviderRefusalError(
                        f"OpenAI refused the {operation.value} operation.",
                        request_id=request_id,
                    )

        if response.status == "incomplete":
            reason = (
                response.incomplete_details.reason
                if response.incomplete_details is not None
                else "unknown"
            )
            raise LLMProviderInvalidResponseError(
                f"OpenAI returned an incomplete response ({reason}).",
                response_kind="incomplete",
                request_id=request_id,
            )

        if response.status not in {None, "completed"}:
            raise LLMProviderInvalidResponseError(
                "OpenAI returned a non-completed response.",
                response_kind="failed",
                request_id=request_id,
            )

    @staticmethod
    def _raise_status_error(error: openai.APIStatusError) -> NoReturn:
        if error.status_code in {408, 409} or error.status_code >= 500:
            raise LLMProviderTransientError(
                "The OpenAI service encountered a transient failure.",
                request_id=error.request_id,
            ) from error
        if error.status_code in {400, 404, 422}:
            raise LLMProviderConfigurationError(
                "The OpenAI request or model configuration is invalid.",
                request_id=error.request_id,
            ) from error
        raise LLMProviderInvalidResponseError(
            "The OpenAI API returned an unexpected status.",
            response_kind="provider_error",
            request_id=error.request_id,
        ) from error

    @staticmethod
    def _response_request_id(response: ParsedResponse[StructuredOutput]) -> str | None:
        request_id = getattr(response, "_request_id", None)
        return request_id if isinstance(request_id, str) else None
