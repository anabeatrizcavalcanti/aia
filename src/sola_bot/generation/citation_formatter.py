"""Formatação de citações a partir do source_map do retrieval."""

from __future__ import annotations

from typing import Any

from sola_bot.generation.rag_answer import Citation
from sola_bot.retrieval.final_context import RetrievalContextPackage


def citations_from_source_map(package: RetrievalContextPackage, max_sources: int = 5) -> list[Citation]:
    """Converte `source_map` do pacote final em citações estruturadas."""
    citations: list[Citation] = []
    for source_id, source in list(package.source_map.items())[:max_sources]:
        citations.append(
            Citation(
                source_id=source_id,
                document=str(source.get("document_title") or source.get("document") or ""),
                document_id=str(source.get("document_id") or ""),
                parent_title=_optional_text(source.get("parent_title")),
                pages=_optional_text(source.get("pages")),
                anchor_chunk_ids=[str(item) for item in source.get("anchor_chunk_ids", [])],
                included_chunk_ids=[str(item) for item in source.get("included_chunk_ids", [])],
                source_paths=[str(item) for item in source.get("source_paths", [])],
                document_type=_optional_text(source.get("document_type")),
                source_category=_optional_text(source.get("source_category")),
                denomination=_optional_text(source.get("denomination")),
                tradition=_optional_text(source.get("tradition")),
                full_reference=_optional_text(source.get("full_reference")),
                document_structure_type=_optional_text(source.get("document_structure_type")),
                content_priority=_optional_text(source.get("content_priority")),
            )
        )
    return citations


def format_citation(citation: Citation, index: int) -> str:
    """Formata uma citação em texto legível."""
    title = citation.full_reference or citation.parent_title or "unidade não informada"
    pages = citation.pages if citation.pages and citation.pages != "não informado" else "página não informada"
    page_label = f"p. {pages}" if pages != "página não informada" else pages
    source_kind = _source_kind_label(citation)
    return f"[{index}] {citation.document}, {title}, {page_label}. Tipo: {source_kind}."


def format_citations(citations: list[Citation]) -> list[str]:
    """Formata uma lista de citações."""
    return [format_citation(citation, index) for index, citation in enumerate(citations, start=1)]


def citation_metadata(citations: list[Citation]) -> list[dict[str, Any]]:
    """Retorna as citações como metadados JSON."""
    return [citation.to_dict() for citation in citations]


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _source_kind_label(citation: Citation) -> str:
    if citation.content_priority == "doctrinal" or citation.source_category == "doctrinal_document":
        return "fonte doutrinária/confessional"
    if citation.content_priority == "normative" or citation.source_category == "denominational_normative_document":
        return "fonte normativa/administrativa"
    return "fonte documental"
