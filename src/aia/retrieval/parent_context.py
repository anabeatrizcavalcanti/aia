"""Construção de contexto hierárquico para chunks recuperados."""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from aia.retrieval.paths import chunks_path as runtime_chunks_path
from aia.retrieval.retrieval_result import RetrievalResult


DEFAULT_CHUNKS_PATH = "corpus/processed/chunks/alliance/all_chunks_for_embeddings.jsonl"
DEFAULT_PARENT_STRATEGY = "structural_window"
NORMATIVE_UNIT_LIST_STRATEGY = "normative_unit_list"
OVERVIEW_PARENT_STRATEGY = "overview_structural_group"
OVERVIEW_QUERY_PATTERNS = (
    r"\bquais\s+(?:são\s+)?(?:responsabilidades|deveres|regras|orientações|orientacoes|requisitos|documentos)\b",
    r"\bo\s+que\s+.+\b(?:diz|ensina|trata|orienta|estabelece)\b",
    r"\bcomo\s+.+\b(?:trata|orienta|explica|regula|estabelece)\b",
    r"\b(?:resuma|liste|sintetize|explique)\b",
)


@dataclass(slots=True)
class ParentContext:
    """Contexto expandido a partir de um chunk âncora."""

    query: str
    anchor_chunk_id: str
    anchor_document_id: str
    anchor_document: str
    anchor_score: float | None
    anchor_pre_rerank_score: float | None
    parent_key: str
    parent_title: str | None
    parent_strategy: str
    parent_expansion_status: str
    included_chunk_ids: list[str]
    included_chunk_count: int
    page_start: int | None
    page_end: int | None
    context_text: str
    context_char_count: int
    metadata: dict[str, Any] = field(default_factory=dict)
    anchor_result: RetrievalResult | None = None

    def to_dict(self) -> dict[str, Any]:
        """Converte o contexto para dicionário serializável."""
        return asdict(self)


def build_parent_key(chunk: dict[str, Any]) -> str:
    """Gera uma chave estável para a unidade documental superior do chunk."""
    document_id = _string_value(chunk.get("document_id")) or "unknown-document"

    article_number = _string_value(chunk.get("article_number"))
    paragraph_number = _string_value(chunk.get("paragraph_number"))
    paragraph_label = _string_value(chunk.get("paragraph_label"))
    paragraph_key = paragraph_number or paragraph_label
    if article_number and paragraph_key:
        return f"{document_id}::article::{_slug(article_number)}::paragraph::{_slug(paragraph_key)}"
    if article_number:
        return f"{document_id}::article::{_slug(article_number)}"

    lords_day = _string_value(chunk.get("lords_day")) or _string_value(chunk.get("section_title"))
    if chunk.get("chunk_type") == "catechism_question_answer" and lords_day:
        return f"{document_id}::group::{_slug(lords_day)}"

    chapter_reference = _string_value(chunk.get("chapter_reference"))
    if chapter_reference:
        return f"{document_id}::chapter::{_slug(chapter_reference)}"

    chapter_title = _string_value(chunk.get("chapter_title"))
    if chapter_title:
        return f"{document_id}::chapter::{_slug(chapter_title)}"

    section_reference = _string_value(chunk.get("section_reference"))
    if section_reference:
        return f"{document_id}::section::{_slug(section_reference)}"

    section_title = _string_value(chunk.get("section_title"))
    if section_title:
        return f"{document_id}::section::{_slug(section_title)}"

    chunk_type = _string_value(chunk.get("chunk_type"))
    if chunk_type:
        return f"{document_id}::chunk-type::{_slug(chunk_type)}"

    chunk_id = _string_value(chunk.get("chunk_id")) or "unknown-chunk"
    return f"{document_id}::chunk::{_slug(chunk_id)}"


class ParentContextBuilder:
    """Carrega chunks e monta contextos expandidos por estrutura documental."""

    def __init__(
        self,
        chunks_path: str | None = None,
        parent_context_max_chars: int = 9000,
        sibling_window_before: int = 1,
        sibling_window_after: int = 1,
        include_full_parent_when_small: bool = True,
        full_parent_max_chars: int = 7000,
        include_metadata_header: bool = True,
        preserve_anchor_first: bool = True,
    ) -> None:
        self.chunks_path = _repo_path(chunks_path) if chunks_path else runtime_chunks_path()
        self.parent_context_max_chars = parent_context_max_chars
        self.sibling_window_before = sibling_window_before
        self.sibling_window_after = sibling_window_after
        self.include_full_parent_when_small = include_full_parent_when_small
        self.full_parent_max_chars = full_parent_max_chars
        self.include_metadata_header = include_metadata_header
        self.preserve_anchor_first = preserve_anchor_first
        self.overview_context_max_chars = max(parent_context_max_chars, int(parent_context_max_chars * 1.5))
        self.chunks = self._load_chunks(self.chunks_path)
        self.chunk_index = {chunk["chunk_id"]: chunk for chunk in self.chunks}
        self.parent_index = self._build_parent_index(self.chunks)

    def build_contexts(
        self,
        query: str,
        anchor_results: list[RetrievalResult],
    ) -> list[ParentContext]:
        """Constrói contextos hierárquicos para resultados âncora."""
        contexts: list[ParentContext] = []
        for anchor_result in anchor_results:
            contexts.append(self._build_context(query=query, anchor_result=anchor_result))
        return contexts

    def _build_context(self, query: str, anchor_result: RetrievalResult) -> ParentContext:
        anchor_chunk = self.chunk_index.get(anchor_result.chunk_id)
        if anchor_chunk is None:
            return self._missing_anchor_context(query, anchor_result)

        parent_key = build_parent_key(anchor_chunk)
        parent_chunks = self.parent_index.get(parent_key, [anchor_chunk])
        parent_title = _parent_title(anchor_chunk)
        candidate_chunks, status, reason, strategy = self._select_chunks(
            query=query,
            anchor_chunk=anchor_chunk,
            parent_chunks=parent_chunks,
            parent_key=parent_key,
        )
        if strategy == OVERVIEW_PARENT_STRATEGY:
            parent_title = _overview_parent_title(anchor_chunk) or parent_title
            parent_key = _overview_parent_key(anchor_chunk) or parent_key
        ordered_chunks = (
            candidate_chunks
            if strategy == NORMATIVE_UNIT_LIST_STRATEGY
            else self._order_for_context(anchor_chunk, candidate_chunks)
        )
        included_chunks = self._fit_to_limit(
            anchor_chunk,
            ordered_chunks,
            max_chars=(
                self.overview_context_max_chars
                if strategy in {NORMATIVE_UNIT_LIST_STRATEGY, OVERVIEW_PARENT_STRATEGY}
                else self.parent_context_max_chars
            ),
        )
        if len(included_chunks) == 1 and included_chunks[0]["chunk_id"] == anchor_chunk["chunk_id"]:
            status = "anchor_only"
            reason = reason or "context_window_limited_to_anchor"

        context_text = self._build_context_text(
            anchor_chunk=anchor_chunk,
            chunks=included_chunks,
            parent_key=parent_key,
            parent_title=parent_title,
            status=status,
            strategy=strategy,
        )
        page_start, page_end = _page_span(included_chunks)
        metadata = self._context_metadata(
            anchor_chunk=anchor_chunk,
            parent_key=parent_key,
            parent_title=parent_title,
            status=status,
            reason=reason,
            strategy=strategy,
            included_chunks=included_chunks,
        )

        return ParentContext(
            query=query,
            anchor_chunk_id=anchor_result.chunk_id,
            anchor_document_id=anchor_result.document_id,
            anchor_document=anchor_result.document,
            anchor_score=anchor_result.score,
            anchor_pre_rerank_score=anchor_result.metadata.get("pre_rerank_score"),
            parent_key=parent_key,
            parent_title=parent_title,
            parent_strategy=strategy,
            parent_expansion_status=status,
            included_chunk_ids=[chunk["chunk_id"] for chunk in included_chunks],
            included_chunk_count=len(included_chunks),
            page_start=page_start,
            page_end=page_end,
            context_text=context_text,
            context_char_count=len(context_text),
            metadata=metadata,
            anchor_result=anchor_result,
        )

    def _select_chunks(
        self,
        query: str,
        anchor_chunk: dict[str, Any],
        parent_chunks: list[dict[str, Any]],
        parent_key: str,
    ) -> tuple[list[dict[str, Any]], str, str | None, str]:
        if _weak_parent_key(parent_key):
            return [anchor_chunk], "anchor_only", "insufficient_parent_metadata", DEFAULT_PARENT_STRATEGY

        normative_list_chunks = self._normative_unit_list_chunks(query=query, parent_chunks=parent_chunks)
        if normative_list_chunks:
            return (
                normative_list_chunks,
                "expanded",
                "normative_unit_list_query",
                NORMATIVE_UNIT_LIST_STRATEGY,
            )

        overview_chunks = self._overview_chunks(query=query, anchor_chunk=anchor_chunk)
        if overview_chunks:
            return (
                overview_chunks,
                "overview_expanded",
                "overview_query_structural_group",
                OVERVIEW_PARENT_STRATEGY,
            )

        if self.include_full_parent_when_small:
            full_parent_chars = sum(len(_chunk_block(chunk, is_anchor=False)) for chunk in parent_chunks)
            if full_parent_chars <= self.full_parent_max_chars:
                return parent_chunks, "expanded", None, DEFAULT_PARENT_STRATEGY

        anchor_index = next(
            (index for index, chunk in enumerate(parent_chunks) if chunk["chunk_id"] == anchor_chunk["chunk_id"]),
            None,
        )
        if anchor_index is None:
            return [anchor_chunk], "anchor_only", "anchor_not_found_in_parent_group", DEFAULT_PARENT_STRATEGY

        start = max(0, anchor_index - self.sibling_window_before)
        end = min(len(parent_chunks), anchor_index + self.sibling_window_after + 1)
        selected = parent_chunks[start:end]
        return selected, "expanded" if len(selected) > 1 else "anchor_only", None, DEFAULT_PARENT_STRATEGY

    def _normative_unit_list_chunks(
        self,
        query: str,
        parent_chunks: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Expande listas normativas de requisitos/documentos dentro da mesma unidade."""
        if not _is_normative_unit_list_query(query):
            return []
        if len(parent_chunks) <= 1:
            return []

        structural_children = [
            chunk
            for chunk in parent_chunks
            if _string_value(chunk.get("inciso")) or _string_value(chunk.get("alinea"))
        ]
        if not structural_children:
            return []

        ordered = sorted(parent_chunks, key=lambda chunk: chunk.get("_document_order", 0))
        return ordered

    def _overview_chunks(
        self,
        query: str,
        anchor_chunk: dict[str, Any],
    ) -> list[dict[str, Any]]:
        if not _is_overview_query(query):
            return []

        group_chunks = self._overview_group_for_anchor(anchor_chunk)
        if len(group_chunks) <= 1:
            return []

        ranked_related = [
            chunk
            for chunk in group_chunks
            if chunk.get("chunk_id") != anchor_chunk.get("chunk_id")
        ]
        ranked_related.sort(key=lambda chunk: chunk.get("_document_order", 0))
        return [anchor_chunk, *ranked_related]

    def _overview_group_for_anchor(self, anchor_chunk: dict[str, Any]) -> list[dict[str, Any]]:
        document_id = _string_value(anchor_chunk.get("document_id"))
        if not document_id:
            return []

        section_title = _string_value(anchor_chunk.get("section_title"))
        if section_title:
            section_group = [
                chunk
                for chunk in self.chunks
                if _string_value(chunk.get("document_id")) == document_id
                and _string_value(chunk.get("section_title")) == section_title
            ]
            if len(section_group) > 1:
                return sorted(section_group, key=lambda item: item.get("_document_order", 0))

        chapter_reference = _string_value(anchor_chunk.get("chapter_reference"))
        if chapter_reference:
            chapter_group = [
                chunk
                for chunk in self.chunks
                if _string_value(chunk.get("document_id")) == document_id
                and _string_value(chunk.get("chapter_reference")) == chapter_reference
            ]
            if len(chapter_group) > 1:
                return sorted(chapter_group, key=lambda item: item.get("_document_order", 0))

        return []

    def _order_for_context(
        self,
        anchor_chunk: dict[str, Any],
        chunks: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        if not self.preserve_anchor_first:
            return chunks
        related = [chunk for chunk in chunks if chunk["chunk_id"] != anchor_chunk["chunk_id"]]
        return [anchor_chunk, *related]

    def _fit_to_limit(
        self,
        anchor_chunk: dict[str, Any],
        chunks: list[dict[str, Any]],
        max_chars: int | None = None,
    ) -> list[dict[str, Any]]:
        included: list[dict[str, Any]] = []
        estimated_chars = 0
        char_limit = max_chars or self.parent_context_max_chars
        for chunk in chunks:
            is_anchor = chunk["chunk_id"] == anchor_chunk["chunk_id"]
            block_size = len(_chunk_block(chunk, is_anchor=is_anchor)) + 2
            if included and estimated_chars + block_size > char_limit:
                continue
            included.append(chunk)
            estimated_chars += block_size
        if not included:
            included.append(anchor_chunk)
        return included

    def _build_context_text(
        self,
        anchor_chunk: dict[str, Any],
        chunks: list[dict[str, Any]],
        parent_key: str,
        parent_title: str | None,
        status: str,
        strategy: str,
    ) -> str:
        parts: list[str] = []
        if self.include_metadata_header:
            page_start, page_end = _page_span(chunks)
            parts.extend(
                [
                    "[CONTEXTO DOCUMENTAL]",
                    f"Documento: {_string_value(anchor_chunk.get('document')) or anchor_chunk.get('document_id')}",
                    f"Unidade: {parent_title or parent_key}",
                    f"Referência: {_chunk_reference(anchor_chunk)}",
                    f"Páginas: {_format_pages(page_start, page_end)}",
                    f"Chunk âncora: {anchor_chunk['chunk_id']}",
                    f"Estratégia de expansão: {strategy}",
                    f"Status da expansão: {status}",
                    "",
                    "[TRECHOS]",
                ]
            )

        for chunk in chunks:
            parts.append(_chunk_block(chunk, is_anchor=chunk["chunk_id"] == anchor_chunk["chunk_id"]))
        return "\n\n".join(part for part in parts if part).strip()

    def _context_metadata(
        self,
        anchor_chunk: dict[str, Any],
        parent_key: str,
        parent_title: str | None,
        status: str,
        reason: str | None,
        strategy: str,
        included_chunks: list[dict[str, Any]],
    ) -> dict[str, Any]:
        return {
            "corpus_id": anchor_chunk.get("corpus_id"),
            "retrieval_namespace": anchor_chunk.get("retrieval_namespace"),
            "document_id": anchor_chunk.get("document_id"),
            "document": anchor_chunk.get("document"),
            "document_title": anchor_chunk.get("document_title") or anchor_chunk.get("document"),
            "document_type": anchor_chunk.get("document_type"),
            "source_category": anchor_chunk.get("source_category"),
            "denomination": anchor_chunk.get("denomination"),
            "tradition": anchor_chunk.get("tradition"),
            "full_reference": anchor_chunk.get("full_reference"),
            "document_structure_type": anchor_chunk.get("document_structure_type"),
            "source_path": anchor_chunk.get("source_path"),
            "normalized_source": anchor_chunk.get("normalized_source"),
            "parent_key": parent_key,
            "parent_title": parent_title,
            "parent_strategy": strategy,
            "parent_expansion_status": status,
            "parent_expansion_reason": reason,
            "included_chunks": [
                {
                    "chunk_id": chunk.get("chunk_id"),
                    "chunk_type": chunk.get("chunk_type"),
                    "document_type": chunk.get("document_type"),
                    "source_category": chunk.get("source_category"),
                    "document_structure_type": chunk.get("document_structure_type"),
                    "chapter_reference": chunk.get("chapter_reference"),
                    "chapter_title": chunk.get("chapter_title"),
                    "section_reference": chunk.get("section_reference"),
                    "section_title": chunk.get("section_title"),
                    "subsection_title": chunk.get("subsection_title"),
                    "paragraph_number": chunk.get("paragraph_number"),
                    "paragraph_label": chunk.get("paragraph_label"),
                    "paragraph_number_roman": chunk.get("paragraph_number_roman"),
                    "article_number": chunk.get("article_number"),
                    "inciso": chunk.get("inciso"),
                    "alinea": chunk.get("alinea"),
                    "full_reference": chunk.get("full_reference"),
                    "biblical_references": chunk.get("biblical_references"),
                    "page_start": chunk.get("page_start"),
                    "page_end": chunk.get("page_end"),
                    "text_hash": chunk.get("text_hash"),
                    "text": chunk.get("text") or chunk.get("embedding_text"),
                }
                for chunk in included_chunks
            ],
        }

    def _missing_anchor_context(self, query: str, anchor_result: RetrievalResult) -> ParentContext:
        context_text = "\n".join(
            [
                "[CONTEXTO DOCUMENTAL]",
                f"Documento: {anchor_result.document}",
                f"Chunk âncora: {anchor_result.chunk_id}",
                "Status da expansão: anchor_only",
                "",
                "[TRECHOS]",
                "--- Chunk âncora ---",
                anchor_result.text,
            ]
        )
        return ParentContext(
            query=query,
            anchor_chunk_id=anchor_result.chunk_id,
            anchor_document_id=anchor_result.document_id,
            anchor_document=anchor_result.document,
            anchor_score=anchor_result.score,
            anchor_pre_rerank_score=anchor_result.metadata.get("pre_rerank_score"),
            parent_key=f"{anchor_result.document_id}::chunk::{_slug(anchor_result.chunk_id)}",
            parent_title=None,
            parent_strategy=DEFAULT_PARENT_STRATEGY,
            parent_expansion_status="anchor_only",
            included_chunk_ids=[anchor_result.chunk_id],
            included_chunk_count=1,
            page_start=anchor_result.page_start,
            page_end=anchor_result.page_end,
            context_text=context_text,
            context_char_count=len(context_text),
            metadata={
                "corpus_id": anchor_result.metadata.get("corpus_id"),
                "retrieval_namespace": anchor_result.metadata.get("retrieval_namespace"),
                "document_type": anchor_result.metadata.get("document_type"),
                "source_category": anchor_result.metadata.get("source_category"),
                "full_reference": anchor_result.metadata.get("full_reference"),
                "parent_expansion_reason": "anchor_chunk_not_found_in_loaded_corpus",
            },
            anchor_result=anchor_result,
        )

    @staticmethod
    def _load_chunks(path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            raise FileNotFoundError(f"Arquivo de chunks não encontrado: {path}")
        chunks: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                chunk = json.loads(line)
                chunk["_document_order"] = line_number
                chunks.append(chunk)
        return chunks

    @staticmethod
    def _build_parent_index(chunks: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        parent_index: dict[str, list[dict[str, Any]]] = {}
        for chunk in chunks:
            parent_index.setdefault(build_parent_key(chunk), []).append(chunk)
        for grouped_chunks in parent_index.values():
            grouped_chunks.sort(key=lambda item: item.get("_document_order", 0))
        return parent_index


def _chunk_block(chunk: dict[str, Any], is_anchor: bool) -> str:
    label = "Chunk âncora" if is_anchor else f"Contexto relacionado: {chunk.get('chunk_id')}"
    reference = _chunk_reference(chunk)
    pages = _format_pages(chunk.get("page_start"), chunk.get("page_end"))
    text = _string_value(chunk.get("text")) or ""
    return "\n".join(
        [
            f"--- {label} ---",
            f"Chunk: {chunk.get('chunk_id')}",
            f"Referência: {reference}",
            f"Páginas: {pages}",
            "",
            text,
        ]
    ).strip()


def _is_overview_query(query: str) -> bool:
    normalized = _normalize_text(query)
    if not normalized:
        return False
    return any(re.search(pattern, normalized) for pattern in OVERVIEW_QUERY_PATTERNS)


def _is_normative_unit_list_query(query: str) -> bool:
    normalized = _normalize_text(query)
    if not normalized:
        return False
    return bool(
        re.search(
            r"\b(?:quais|liste|listar|relacione|enumere|descreva|informe)\b.*"
            r"\b(?:requisitos|documentos|documentacao|exigencias|criterios|itens)\b",
            normalized,
        )
        or re.search(
            r"\b(?:requisitos|documentos|documentacao|exigencias|criterios|itens)\b.*"
            r"\b(?:ingresso|filiacao|admissao|candidata|candidato|apresentar)\b",
            normalized,
        )
    )


def _chunk_reference(chunk: dict[str, Any]) -> str:
    full_reference = _string_value(chunk.get("full_reference"))
    if full_reference:
        return full_reference
    parts = [
        _string_value(chunk.get("chapter_reference")),
        _string_value(chunk.get("chapter_title")),
        _string_value(chunk.get("subsection_title")),
        _string_value(chunk.get("section_title")),
        _string_value(chunk.get("section_reference")),
    ]
    return " | ".join(part for part in parts if part) or "não informado"


def _parent_title(chunk: dict[str, Any]) -> str | None:
    full_reference = _string_value(chunk.get("full_reference"))
    if full_reference:
        return full_reference
    if chunk.get("chunk_type") == "catechism_question_answer":
        return _string_value(chunk.get("lords_day")) or _string_value(chunk.get("section_title"))
    chapter_reference = _string_value(chunk.get("chapter_reference"))
    chapter_title = _string_value(chunk.get("chapter_title"))
    if chapter_reference and chapter_title:
        return f"{chapter_reference} — {chapter_title}"
    return chapter_reference or chapter_title or _string_value(chunk.get("section_title"))


def _overview_parent_title(chunk: dict[str, Any]) -> str | None:
    subsection_title = _string_value(chunk.get("subsection_title"))
    section_title = _string_value(chunk.get("section_title"))
    chapter_reference = _string_value(chunk.get("chapter_reference"))
    chapter_title = _string_value(chunk.get("chapter_title"))
    if subsection_title and section_title:
        return f"{section_title} — {subsection_title}"
    if section_title:
        return section_title
    if chapter_reference and chapter_title:
        return f"{chapter_reference} — {chapter_title}"
    return chapter_reference or chapter_title


def _overview_parent_key(chunk: dict[str, Any]) -> str | None:
    document_id = _string_value(chunk.get("document_id"))
    if not document_id:
        return None
    section_title = _string_value(chunk.get("section_title"))
    if section_title:
        return f"{document_id}::overview-section::{_slug(section_title)}"
    chapter_reference = _string_value(chunk.get("chapter_reference"))
    if chapter_reference:
        return f"{document_id}::overview-chapter::{_slug(chapter_reference)}"
    topic = _string_value(chunk.get("topic"))
    if topic:
        return f"{document_id}::overview-topic::{_slug(topic)}"
    return None


def _page_span(chunks: list[dict[str, Any]]) -> tuple[int | None, int | None]:
    starts = [_int_value(chunk.get("page_start")) for chunk in chunks]
    ends = [_int_value(chunk.get("page_end")) or _int_value(chunk.get("page_start")) for chunk in chunks]
    starts = [value for value in starts if value is not None]
    ends = [value for value in ends if value is not None]
    if not starts and not ends:
        return None, None
    return min(starts) if starts else None, max(ends) if ends else None


def _format_pages(page_start: Any, page_end: Any) -> str:
    start = _int_value(page_start)
    end = _int_value(page_end)
    if start is None and end is None:
        return "não informado"
    if end is None or start == end:
        return str(start)
    return f"{start}-{end}"


def _weak_parent_key(parent_key: str) -> bool:
    return "::chunk-type::" in parent_key or "::chunk::" in parent_key


def _string_value(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _int_value(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _normalize_text(value: Any) -> str:
    normalized = unicodedata.normalize("NFKD", str(value or "").lower())
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", ascii_text).strip()


def _slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    lowered = ascii_text.lower()
    lowered = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return lowered or "sem-chave"


def _repo_path(path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return Path(__file__).resolve().parents[3] / candidate
