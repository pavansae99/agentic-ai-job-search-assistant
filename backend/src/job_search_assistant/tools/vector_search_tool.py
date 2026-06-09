"""Small in-memory vector-search abstraction with a replaceable backend."""

import math
import re
from collections import Counter
from dataclasses import dataclass, field
from threading import RLock
from uuid import uuid4


@dataclass(frozen=True)
class SearchResult:
    """A document returned from semantic-like local retrieval."""

    document_id: str
    content: str
    score: float
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class _Document:
    content: str
    metadata: dict[str, str]


class VectorSearchTool:
    """Thread-safe local cosine search implementing the future vector-store contract."""

    def __init__(self) -> None:
        self._documents: dict[str, _Document] = {}
        self._lock = RLock()

    def add_document(
        self,
        content: str,
        metadata: dict[str, str] | None = None,
        document_id: str | None = None,
    ) -> str:
        """Add a document and return its stable identifier."""

        if not content.strip():
            raise ValueError("Document content cannot be empty.")
        identifier = document_id or str(uuid4())
        with self._lock:
            self._documents[identifier] = _Document(content, metadata or {})
        return identifier

    def search(self, query: str, limit: int = 5) -> list[SearchResult]:
        """Rank documents using cosine similarity over normalized term frequencies."""

        if limit < 1:
            raise ValueError("Search limit must be at least 1.")
        query_vector = self._vectorize(query)
        with self._lock:
            scored = [
                SearchResult(
                    document_id=identifier,
                    content=document.content,
                    score=round(self._cosine(query_vector, self._vectorize(document.content)), 4),
                    metadata=document.metadata,
                )
                for identifier, document in self._documents.items()
            ]
        return sorted(scored, key=lambda result: result.score, reverse=True)[:limit]

    @staticmethod
    def _vectorize(text: str) -> Counter[str]:
        tokens = re.findall(r"[a-z0-9+#.]+", text.casefold())
        return Counter(tokens)

    @staticmethod
    def _cosine(left: Counter[str], right: Counter[str]) -> float:
        if not left or not right:
            return 0.0
        shared = left.keys() & right.keys()
        dot_product = sum(left[token] * right[token] for token in shared)
        left_norm = math.sqrt(sum(value**2 for value in left.values()))
        right_norm = math.sqrt(sum(value**2 for value in right.values()))
        return dot_product / (left_norm * right_norm)
