"""Estruturas de resposta da geração RAG."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class Citation:
    """Fonte documental citável na resposta."""

    source_id: str
    document: str
    document_id: str
    parent_title: str | None
    pages: str | None
    anchor_chunk_ids: list[str]
    included_chunk_ids: list[str]
    source_paths: list[str]
    document_type: str | None = None
    source_category: str | None = None
    denomination: str | None = None
    tradition: str | None = None
    full_reference: str | None = None
    document_structure_type: str | None = None
    content_priority: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Converte a citação para dicionário serializável."""
        return asdict(self)


@dataclass(slots=True)
class RagAnswer:
    """Resposta gerada ou recusa baseada em evidência documental."""

    query: str
    answer: str
    status: str
    used_context_count: int
    used_documents: list[str]
    used_sources: list[str]
    citations: list[Citation]
    refusal_reason: str | None
    model: str | None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Converte a resposta para dicionário serializável."""
        data = asdict(self)
        data["citations"] = [citation.to_dict() for citation in self.citations]
        return data
