"""Shared deterministic text extraction helpers."""

import re

SKILL_ALIASES: dict[str, tuple[str, ...]] = {
    "Agentic AI": ("agentic ai", "ai agents", "multi-agent"),
    "AWS": ("aws", "amazon web services"),
    "Azure": ("azure",),
    "Docker": ("docker", "containers"),
    "FastAPI": ("fastapi",),
    "GCP": ("gcp", "google cloud"),
    "Git": ("git", "github"),
    "Go": ("golang", "go language", "go developer"),
    "gRPC": ("grpc",),
    "Java": ("java",),
    "Kafka": ("kafka",),
    "Kubernetes": ("kubernetes", "k8s"),
    "LangChain": ("langchain",),
    "LangGraph": ("langgraph",),
    "Linux": ("linux",),
    "LLMs": ("llm", "large language model"),
    "Microservices": ("microservices", "micro-services"),
    "PostgreSQL": ("postgresql", "postgres"),
    "Python": ("python",),
    "RAG": ("retrieval augmented generation", "retrieval-augmented generation", "rag"),
    "Redis": ("redis",),
    "REST": ("rest api", "restful"),
    "SQL": ("sql",),
    "SQLAlchemy": ("sqlalchemy",),
    "Terraform": ("terraform",),
}

ROLE_NAMES = (
    "Senior Software Engineer",
    "Staff Software Engineer",
    "Principal Engineer",
    "Backend Engineer",
    "Platform Engineer",
    "Cloud Engineer",
    "AI Engineer",
    "Machine Learning Engineer",
)


def contains_phrase(text: str, phrase: str) -> bool:
    """Match a phrase without treating punctuation as part of a word."""

    return bool(re.search(rf"(?<!\w){re.escape(phrase)}(?!\w)", text, flags=re.IGNORECASE))


def extract_skills(text: str) -> list[str]:
    """Return normalized skills found in free text."""

    return [
        canonical
        for canonical, aliases in SKILL_ALIASES.items()
        if any(contains_phrase(text, alias) for alias in aliases)
    ]


def extract_years(text: str) -> float:
    """Return the highest explicit years-of-experience value in text."""

    values = re.findall(
        r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)(?:\s+of)?\s+(?:professional\s+)?experience",
        text,
        flags=re.IGNORECASE,
    )
    if not values:
        values = re.findall(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)", text, re.IGNORECASE)
    return max((float(value) for value in values), default=0.0)


def extract_labeled_value(text: str, labels: tuple[str, ...]) -> str | None:
    """Extract the text following a line-oriented label."""

    label_pattern = "|".join(re.escape(label) for label in labels)
    match = re.search(
        rf"^(?:{label_pattern})\s*:\s*(.+)$",
        text,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    return match.group(1).strip() if match else None
