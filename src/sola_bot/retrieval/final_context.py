"""Estruturas da saída final de retrieval."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class FinalContext:
    """Contexto documental consolidado para uso pela camada RAG."""

    query: str
    rank: int
    parent_key: str
    parent_title: str | None
    document_id: str
    document: str
    context_text: str
    context_char_count: int
    included_chunk_ids: list[str]
    anchor_chunk_ids: list[str]
    anchor_scores: list[float | None]
    page_start: int | None
    page_end: int | None
    source_paths: list[str]
    context_status: str
    content_priority: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Converte o contexto final para dicionário serializável."""
        return asdict(self)


@dataclass(slots=True)
class RetrievalContextPackage:
    """Pacote final de contextos documentais recuperados."""

    query: str
    contexts: list[FinalContext]
    context_count: int
    total_context_chars: int
    documents: list[str]
    source_map: dict[str, dict[str, Any]]
    retrieval_stages: list[str]
    filters: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Converte o pacote para dicionário serializável."""
        data = asdict(self)
        data["contexts"] = [context.to_dict() for context in self.contexts]
        return data


def build_context_package_text(package: RetrievalContextPackage) -> str:
    """Monta o texto consolidado para a camada RAG."""
    lines: list[str] = [
        "[CONTEXTOS DOCUMENTAIS RECUPERADOS]",
        "",
        f"Pergunta: {package.query}",
        "",
    ]
    for index, context in enumerate(package.contexts, start=1):
        lines.extend(
            [
                f"[FONTE {index}]",
                f"Documento: {context.document}",
                f"Tipo de fonte: {context.content_priority}",
                f"Unidade: {context.parent_title or context.parent_key}",
                f"Referência: {context.metadata.get('full_reference') or context.parent_title or context.parent_key}",
                f"Páginas: {_format_pages(context.page_start, context.page_end)}",
                f"Chunks âncora: {', '.join(context.anchor_chunk_ids)}",
                f"Chunks incluídos: {', '.join(context.included_chunk_ids)}",
                f"Status: {context.context_status}",
                f"Prioridade de conteúdo: {context.content_priority}",
                "",
                "Texto:",
                context.context_text,
                "",
            ]
        )
    return "\n".join(lines).strip()


def _format_pages(page_start: int | None, page_end: int | None) -> str:
    if page_start is None and page_end is None:
        return "não informado"
    if page_end is None or page_start == page_end:
        return str(page_start)
    return f"{page_start}-{page_end}"
