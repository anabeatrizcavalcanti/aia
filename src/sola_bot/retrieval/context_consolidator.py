"""Consolidação do contexto hierárquico para a saída final de retrieval."""

from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from dataclasses import replace
from typing import Any

from sola_bot.retrieval.final_context import FinalContext, RetrievalContextPackage
from sola_bot.retrieval.parent_context import ParentContext


DEFAULT_FILTERS = {
}
DOCTRINAL_CHUNK_TYPES = {
    "doctrinal_article",
    "confessional_paragraph",
    "confession_paragraph",
    "confessional_section",
    "catechism_question_answer",
    "error_refutation",
    "conclusion_paragraph",
    "numbered_doctrinal_point",
}
DOCTRINAL_DOCUMENT_TYPES = {
    "confession_of_faith",
    "catechism",
    "doctrinal_canons",
}
NORMATIVE_DOCUMENT_TYPES = {
    "constitution",
    "internal_regiment",
    "normative_ethics",
    "administrative_resolution",
}
INTRODUCTORY_CHUNK_TYPES = {
    "introductory_context",
    "preface",
    "summary",
    "index",
    "bibliographic_note",
    "special_layout",
}
DOCTRINAL_TERMS = {
    "doutrina",
    "ensina",
    "ensino",
    "salvação",
    "salvacao",
    "batismo",
    "eleição",
    "eleicao",
    "justificação",
    "justificacao",
    "regeneração",
    "regeneracao",
    "regenerado",
    "regenerada",
    "regenerados",
    "regeneradas",
    "regenerar",
    "expiação",
    "expiacao",
    "escrituras",
    "sacramentos",
    "perseverança",
    "perseveranca",
    "fé",
    "fe",
    "graça",
    "graca",
}
NORMATIVE_TERMS = {
    "alianca",
    "aliança",
    "constituicao",
    "constituição",
    "regimento",
    "codigo",
    "código",
    "etica",
    "ética",
    "resolucao",
    "resolução",
    "filiacao",
    "filiação",
    "filiada",
    "filiado",
    "igreja",
    "local",
    "deveres",
    "ordenacao",
    "ordenação",
    "ministro",
    "ministerio",
    "ministério",
    "pastor",
    "disciplina",
    "emancipacao",
    "emancipação",
    "congregacao",
    "congregação",
    "campo",
    "missao",
    "missão",
    "missoes",
    "missões",
    "missionario",
    "missionário",
    "missionarios",
    "missionários",
    "contribuicao",
    "contribuição",
    "documentos",
    "candidato",
    "requisito",
    "requisitos",
    "processo",
    "artigo",
    "inciso",
    "paragrafo",
    "parágrafo",
    "diretoria",
    "conselho",
}
DENOMINATIONAL_SCOPE_TERMS = {
    "alianca",
    "aliança",
}
SPECIFIC_DOCUMENT_TERMS = {
    "westminster",
    "londres",
    "batista",
    "dort",
    "heidelberg",
    "catecismo",
    "canones",
    "cânones",
    "congregacional",
    "constituicao",
    "constituição",
    "regimento",
    "codigo",
    "código",
    "etica",
    "ética",
    "resolucao",
    "resolução",
}


class ContextConsolidator:
    """Agrupa, prioriza e limita contextos hierárquicos."""

    def __init__(
        self,
        final_context_top_k: int = 4,
        max_total_context_chars: int = 18000,
        max_context_chars_per_parent: int = 9000,
        consolidate_by_parent_key: bool = True,
        deduplicate_included_chunks: bool = True,
        prefer_expanded_contexts: bool = True,
        reduce_introductory_context_for_doctrinal_queries: bool = True,
        keep_anchor_only_when_no_expanded_alternative: bool = True,
        preserve_document_diversity: bool = True,
        max_contexts_per_parent_key: int = 1,
    ) -> None:
        self.final_context_top_k = final_context_top_k
        self.max_total_context_chars = max_total_context_chars
        self.max_context_chars_per_parent = max_context_chars_per_parent
        self.consolidate_by_parent_key = consolidate_by_parent_key
        self.deduplicate_included_chunks = deduplicate_included_chunks
        self.prefer_expanded_contexts = prefer_expanded_contexts
        self.reduce_introductory_context_for_doctrinal_queries = reduce_introductory_context_for_doctrinal_queries
        self.keep_anchor_only_when_no_expanded_alternative = keep_anchor_only_when_no_expanded_alternative
        self.preserve_document_diversity = preserve_document_diversity
        self.max_contexts_per_parent_key = max_contexts_per_parent_key

    def consolidate(
        self,
        query: str,
        parent_contexts: list[ParentContext],
        filters: dict[str, Any] | None = None,
    ) -> RetrievalContextPackage:
        """Consolida contextos hierárquicos em um pacote final."""
        merged_filters = self._merge_filters(filters)
        query_intent = classify_query_intent(query)
        query_is_doctrinal = query_intent in {"doctrinal", "mixed"}
        query_is_normative = query_intent in {"normative", "mixed"}
        grouped_contexts = self._group_contexts(parent_contexts)
        candidates = [
            self._build_final_context(query, group, parent_key, query_is_doctrinal, query_is_normative)
            for parent_key, group in grouped_contexts.items()
        ]
        candidates, removal_metadata = self._remove_introductory_anchor_only(candidates, query_is_doctrinal)
        candidates = self._apply_anchor_only_handling(candidates)
        candidates = sorted(candidates, key=lambda context: context.metadata["ranking_score"], reverse=True)
        candidates, dedupe_metadata = self._deduplicate_chunks_across_contexts(candidates)
        candidates, diversity_metadata = self._promote_document_diversity(
            candidates=candidates,
            query=query,
            filters=merged_filters,
        )
        selected, limit_metadata = self._apply_limits(candidates)

        ranked_contexts = [
            replace(context, rank=rank)
            for rank, context in enumerate(selected, start=1)
        ]
        source_map = build_source_map(ranked_contexts)
        documents = sorted({context.document_id for context in ranked_contexts})
        metadata = {
            "corpus_scope": "alliance_documents",
            "parent_contexts_received": len(parent_contexts),
            "candidate_parent_contexts": len(candidates),
            "final_context_top_k": self.final_context_top_k,
            "query_intent": query_intent,
            "query_is_doctrinal": query_is_doctrinal,
            "query_is_normative": query_is_normative,
            "contexts_fused_by_parent_key": sum(max(0, len(group) - 1) for group in grouped_contexts.values()),
            "removed_contexts": removal_metadata,
            "deduplication": dedupe_metadata,
            "document_diversity": diversity_metadata,
            "char_limits": limit_metadata,
            "ordering_heuristic": (
                "ranking_score = best_anchor_score + content_priority_bonus + expanded_bonus "
                "- introductory_penalty - anchor_only_penalty"
            ),
        }
        return RetrievalContextPackage(
            query=query,
            contexts=ranked_contexts,
            context_count=len(ranked_contexts),
            total_context_chars=sum(context.context_char_count for context in ranked_contexts),
            documents=documents,
            source_map=source_map,
            retrieval_stages=[
                "vector_retrieval",
                "bm25_retrieval",
                "reciprocal_rank_fusion",
                "hybrid_retrieval",
                "cross_encoder_reranking",
                "hierarchical_retrieval",
                "context_consolidation",
                "final_context_package",
            ],
            filters=merged_filters,
            metadata=metadata,
        )

    def _group_contexts(self, contexts: list[ParentContext]) -> dict[str, list[ParentContext]]:
        grouped: dict[str, list[ParentContext]] = defaultdict(list)
        for index, context in enumerate(contexts):
            key = context.parent_key if self.consolidate_by_parent_key else f"{context.parent_key}::{index}"
            grouped[key].append(context)
        return dict(grouped)

    def _build_final_context(
        self,
        query: str,
        contexts: list[ParentContext],
        parent_key: str,
        query_is_doctrinal: bool,
        query_is_normative: bool,
    ) -> FinalContext:
        ordered_contexts = sorted(contexts, key=_parent_context_sort_key, reverse=True)
        base = ordered_contexts[0]
        anchor_chunk_ids = _unique([context.anchor_chunk_id for context in ordered_contexts])
        anchor_scores = [context.anchor_score for context in ordered_contexts]
        included_chunk_ids = _unique(
            chunk_id for context in ordered_contexts for chunk_id in context.included_chunk_ids
        )
        source_paths = _unique(
            value
            for context in ordered_contexts
            for value in [
                str(context.metadata.get("source_path") or ""),
                str(context.anchor_result.source_path if context.anchor_result else ""),
            ]
            if value
        )
        page_start = _min_nullable(context.page_start for context in ordered_contexts)
        page_end = _max_nullable(context.page_end for context in ordered_contexts)
        content_priority = _content_priority(ordered_contexts)
        best_score = _best_score(ordered_contexts)
        statuses = [context.parent_expansion_status for context in ordered_contexts]
        context_status = "expanded" if "expanded" in statuses else "anchor_only"
        if len(ordered_contexts) > 1:
            context_status = f"{context_status}_consolidated"

        context_text, truncated = _truncate_context(
            base.context_text,
            self.max_context_chars_per_parent,
        )
        ranking_score = _ranking_score(
            best_score=best_score,
            content_priority=content_priority,
            context_status=context_status,
            query_is_doctrinal=query_is_doctrinal,
            query_is_normative=query_is_normative,
        )
        metadata = {
            "corpus_id": base.metadata.get("corpus_id"),
            "retrieval_namespace": base.metadata.get("retrieval_namespace"),
            "document_title": base.metadata.get("document_title") or base.anchor_document,
            "document_type": base.metadata.get("document_type"),
            "source_category": base.metadata.get("source_category"),
            "denomination": base.metadata.get("denomination"),
            "tradition": base.metadata.get("tradition"),
            "full_reference": base.metadata.get("full_reference"),
            "document_structure_type": base.metadata.get("document_structure_type"),
            "parent_context_count": len(ordered_contexts),
            "source_parent_keys": [context.parent_key for context in ordered_contexts],
            "original_expansion_statuses": statuses,
            "anchor_chunk_types": [
                context.anchor_result.chunk_type
                for context in ordered_contexts
                if context.anchor_result is not None
            ],
            "included_chunks": _included_chunk_metadata(ordered_contexts),
            "best_anchor_score": best_score,
            "ranking_score": ranking_score,
            "context_truncated": truncated,
            "consolidation_decision": (
                "merged_by_parent_key" if len(ordered_contexts) > 1 else "single_parent_context"
            ),
            "anchor_only_handling": None,
            "introductory_handling": None,
        }
        return FinalContext(
            query=query,
            rank=0,
            parent_key=parent_key,
            parent_title=base.parent_title,
            document_id=base.anchor_document_id,
            document=base.anchor_document,
            context_text=context_text,
            context_char_count=len(context_text),
            included_chunk_ids=included_chunk_ids,
            anchor_chunk_ids=anchor_chunk_ids,
            anchor_scores=anchor_scores,
            page_start=page_start,
            page_end=page_end,
            source_paths=source_paths,
            context_status=context_status,
            content_priority=content_priority,
            metadata=metadata,
        )

    def _remove_introductory_anchor_only(
        self,
        contexts: list[FinalContext],
        query_is_doctrinal: bool,
    ) -> tuple[list[FinalContext], dict[str, Any]]:
        if not self.reduce_introductory_context_for_doctrinal_queries or not query_is_doctrinal:
            return contexts, {"removed_introductory_anchor_only": []}

        has_expanded_doctrinal = any(
            context.content_priority == "doctrinal" and "expanded" in context.context_status
            for context in contexts
        )
        removed: list[str] = []
        kept: list[FinalContext] = []
        for context in contexts:
            if (
                has_expanded_doctrinal
                and context.content_priority == "introductory"
                and context.context_status.startswith("anchor_only")
            ):
                removed.append(context.parent_key)
                continue
            kept.append(context)
        return kept, {"removed_introductory_anchor_only": removed}

    def _apply_anchor_only_handling(self, contexts: list[FinalContext]) -> list[FinalContext]:
        has_expanded = any("expanded" in context.context_status for context in contexts)
        updated: list[FinalContext] = []
        for context in contexts:
            metadata = dict(context.metadata)
            if context.context_status.startswith("anchor_only"):
                if has_expanded and self.prefer_expanded_contexts:
                    metadata["anchor_only_handling"] = "deprioritized_due_to_expanded_alternatives"
                    metadata["ranking_score"] -= 1.0
                elif self.keep_anchor_only_when_no_expanded_alternative:
                    metadata["anchor_only_handling"] = "kept_because_no_expanded_alternative"
                else:
                    metadata["anchor_only_handling"] = "kept"
            else:
                metadata["anchor_only_handling"] = "not_anchor_only"
            updated.append(replace(context, metadata=metadata))
        return updated

    def _deduplicate_chunks_across_contexts(
        self,
        contexts: list[FinalContext],
    ) -> tuple[list[FinalContext], dict[str, Any]]:
        if not self.deduplicate_included_chunks:
            return contexts, {"deduplicated_chunk_ids": []}

        seen: set[str] = set()
        deduplicated: list[str] = []
        updated: list[FinalContext] = []
        for context in contexts:
            retained = []
            removed = []
            for chunk_id in context.included_chunk_ids:
                if chunk_id in seen:
                    removed.append(chunk_id)
                    deduplicated.append(chunk_id)
                    continue
                seen.add(chunk_id)
                retained.append(chunk_id)
            metadata = dict(context.metadata)
            metadata["deduplicated_included_chunk_ids"] = removed
            updated.append(replace(context, included_chunk_ids=retained or context.included_chunk_ids, metadata=metadata))
        return updated, {"deduplicated_chunk_ids": deduplicated, "deduplicated_chunk_count": len(deduplicated)}

    def _promote_document_diversity(
        self,
        candidates: list[FinalContext],
        query: str,
        filters: dict[str, Any],
    ) -> tuple[list[FinalContext], dict[str, Any]]:
        """Intercala documentos relevantes quando a consulta não restringe uma fonte."""
        if not self.preserve_document_diversity or len(candidates) <= 1:
            return candidates, {"applied": False, "reason": "disabled_or_single_candidate"}
        if filters.get("document_id"):
            return candidates, {"applied": False, "reason": "document_filter_present"}
        if _query_mentions_specific_document(query):
            return candidates, {"applied": False, "reason": "specific_document_mentioned"}

        available_document_ids = _unique(context.document_id for context in candidates)
        topic_matched = [context for context in candidates if _parent_unit_matches_query(context, query)]
        topic_matched_document_ids = _unique(context.document_id for context in topic_matched)
        if len(topic_matched_document_ids) >= 2:
            top_topic_by_document: dict[str, FinalContext] = {}
            for context in topic_matched:
                top_topic_by_document.setdefault(context.document_id, context)

            promoted = sorted(
                top_topic_by_document.values(),
                key=lambda context: _metadata_score(context),
                reverse=True,
            )[: self.final_context_top_k]
            promoted_keys = {context.parent_key for context in promoted}
            remainder = [context for context in candidates if context.parent_key not in promoted_keys]
            return promoted + remainder, {
                "applied": True,
                "reason": "topic_matched_one_context_per_document_promoted",
                "promoted_documents": [context.document_id for context in promoted],
                "available_documents": available_document_ids,
                "topic_matched_documents": topic_matched_document_ids,
                "topic_matched_parent_keys": [context.parent_key for context in topic_matched],
            }

        if topic_matched:
            matched_keys = {context.parent_key for context in topic_matched}
            candidates = topic_matched + [
                context for context in candidates if context.parent_key not in matched_keys
            ]

        document_ids = _unique(context.document_id for context in candidates)
        if len(document_ids) <= 1:
            return candidates, {"applied": False, "reason": "single_document_available"}

        best_score = _metadata_score(candidates[0])
        relevance_floor = _diversity_relevance_floor(best_score)
        top_by_document: dict[str, FinalContext] = {}
        for context in candidates:
            if _metadata_score(context) < relevance_floor:
                continue
            if not _parent_unit_matches_query(context, query):
                continue
            top_by_document.setdefault(context.document_id, context)

        if len(top_by_document) <= 1:
            return candidates, {
                "applied": False,
                "reason": "no_relevant_alternative_document",
                "available_documents": document_ids,
                "topic_matched_documents": topic_matched_document_ids,
                "topic_matched_parent_keys": [context.parent_key for context in topic_matched],
            }

        promoted = sorted(
            top_by_document.values(),
            key=lambda context: _metadata_score(context),
            reverse=True,
        )
        max_promoted = min(len(promoted), self.final_context_top_k)
        promoted = promoted[:max_promoted]
        promoted_keys = {context.parent_key for context in promoted}
        remainder = [context for context in candidates if context.parent_key not in promoted_keys]
        reordered = promoted + remainder

        return reordered, {
            "applied": True,
            "reason": "topic_matched_multi_document_context_promoted",
            "promoted_documents": [context.document_id for context in promoted],
            "available_documents": document_ids,
            "topic_matched_documents": topic_matched_document_ids,
            "topic_matched_parent_keys": [context.parent_key for context in topic_matched],
            "relevance_floor": relevance_floor,
        }

    def _apply_limits(self, contexts: list[FinalContext]) -> tuple[list[FinalContext], dict[str, Any]]:
        selected: list[FinalContext] = []
        total_chars = 0
        dropped_by_limit: list[str] = []
        truncated_by_global_limit: list[str] = []
        for context in contexts:
            if len(selected) >= self.final_context_top_k:
                dropped_by_limit.append(context.parent_key)
                continue
            remaining = self.max_total_context_chars - total_chars
            if remaining <= 0:
                dropped_by_limit.append(context.parent_key)
                continue
            if context.context_char_count > remaining:
                if not selected and remaining > 0:
                    context_text, _ = _truncate_context(context.context_text, remaining)
                    metadata = dict(context.metadata)
                    metadata["global_context_truncated"] = True
                    selected.append(
                        replace(
                            context,
                            context_text=context_text,
                            context_char_count=len(context_text),
                            metadata=metadata,
                        )
                    )
                    total_chars += len(context_text)
                    truncated_by_global_limit.append(context.parent_key)
                else:
                    dropped_by_limit.append(context.parent_key)
                continue
            selected.append(context)
            total_chars += context.context_char_count

        return selected, {
            "max_total_context_chars": self.max_total_context_chars,
            "max_context_chars_per_parent": self.max_context_chars_per_parent,
            "dropped_by_limit": dropped_by_limit,
            "truncated_by_global_limit": truncated_by_global_limit,
        }

    @staticmethod
    def _merge_filters(filters: dict[str, Any] | None) -> dict[str, Any]:
        merged = dict(DEFAULT_FILTERS)
        for key, value in (filters or {}).items():
            if value is None:
                continue
            if key in DEFAULT_FILTERS and value != DEFAULT_FILTERS[key]:
                continue
            merged[key] = value
        return merged


def classify_query_intent(query: str) -> str:
    """Classifica pergunta em escopo doutrinário, normativo, misto ou geral."""
    terms = _query_terms(query)
    doctrinal_terms = terms & DOCTRINAL_TERMS
    normative_terms = terms & NORMATIVE_TERMS
    normative_terms_without_scope = normative_terms - DENOMINATIONAL_SCOPE_TERMS
    has_doctrinal = bool(doctrinal_terms)
    has_normative = bool(normative_terms_without_scope)
    if has_doctrinal and has_normative:
        return "mixed"
    if has_normative:
        return "normative"
    if has_doctrinal:
        return "doctrinal"
    if normative_terms:
        return "normative"
    return "general"


def is_doctrinal_query(query: str) -> bool:
    """Compatibilidade para chamadas antigas que esperam booleano."""
    return classify_query_intent(query) in {"doctrinal", "mixed"}


def query_mentions_denominational_scope(query: str) -> bool:
    """Identifica quando a pergunta restringe o escopo à Aliança como denominação."""
    return bool(_query_terms(query) & DENOMINATIONAL_SCOPE_TERMS)


def _query_terms(query: str) -> set[str]:
    normalized = query.lower()
    return set(re.findall(r"[\wÀ-ÿ]+", normalized))


def build_source_map(contexts: list[FinalContext]) -> dict[str, dict[str, Any]]:
    """Monta mapa de fontes rastreáveis para o pacote final."""
    source_map: dict[str, dict[str, Any]] = {}
    for index, context in enumerate(contexts, start=1):
        source_map[f"source_{index}"] = {
            "document": context.document,
            "document_id": context.document_id,
            "document_title": context.metadata.get("document_title") or context.document,
            "document_type": context.metadata.get("document_type"),
            "source_category": context.metadata.get("source_category"),
            "denomination": context.metadata.get("denomination"),
            "tradition": context.metadata.get("tradition"),
            "parent_key": context.parent_key,
            "parent_title": context.parent_title,
            "full_reference": context.metadata.get("full_reference") or _first_included_value(context, "full_reference"),
            "document_structure_type": context.metadata.get("document_structure_type"),
            "content_priority": context.content_priority,
            "pages": _format_pages(context.page_start, context.page_end),
            "anchor_chunk_ids": context.anchor_chunk_ids,
            "included_chunk_ids": context.included_chunk_ids,
            "source_paths": context.source_paths,
        }
    return source_map


def _parent_context_sort_key(context: ParentContext) -> tuple[float, int, int]:
    score = context.anchor_score if context.anchor_score is not None else float("-inf")
    expanded = 1 if context.parent_expansion_status == "expanded" else 0
    doctrinal = 1 if _anchor_chunk_type(context) in DOCTRINAL_CHUNK_TYPES else 0
    return score, expanded, doctrinal


def _content_priority(contexts: list[ParentContext]) -> str:
    chunk_types = {_anchor_chunk_type(context) for context in contexts}
    metadatas = [
        context.anchor_result.metadata
        for context in contexts
        if context.anchor_result is not None
    ]
    document_types = {str(metadata.get("document_type") or "") for metadata in metadatas}
    source_categories = {str(metadata.get("source_category") or "") for metadata in metadatas}
    content_roles = {str(metadata.get("content_role") or "") for metadata in metadatas}
    if (
        chunk_types & DOCTRINAL_CHUNK_TYPES
        or document_types & DOCTRINAL_DOCUMENT_TYPES
        or "doctrinal_document" in source_categories
        or "doctrinal" in content_roles
    ):
        return "doctrinal"
    if (
        document_types & NORMATIVE_DOCUMENT_TYPES
        or "denominational_normative_document" in source_categories
        or "normative" in content_roles
    ):
        return "normative"
    if chunk_types & INTRODUCTORY_CHUNK_TYPES:
        return "introductory"
    return "contextual"


def _included_chunk_metadata(contexts: list[ParentContext]) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    seen: set[str] = set()
    for context in contexts:
        raw_chunks = context.metadata.get("included_chunks")
        if not isinstance(raw_chunks, list):
            continue
        for chunk in raw_chunks:
            if not isinstance(chunk, dict):
                continue
            chunk_id = str(chunk.get("chunk_id") or "")
            if not chunk_id or chunk_id in seen:
                continue
            seen.add(chunk_id)
            chunks.append(dict(chunk))
    return chunks


def _first_included_value(context: FinalContext, key: str) -> Any | None:
    chunks = context.metadata.get("included_chunks")
    if not isinstance(chunks, list):
        return None
    for chunk in chunks:
        if not isinstance(chunk, dict):
            continue
        value = chunk.get(key)
        if value not in (None, ""):
            return value
    return None


def _anchor_chunk_type(context: ParentContext) -> str | None:
    if context.anchor_result is None:
        return None
    return context.anchor_result.chunk_type


def _best_score(contexts: list[ParentContext]) -> float | None:
    scores = [context.anchor_score for context in contexts if context.anchor_score is not None]
    return max(scores) if scores else None


def _ranking_score(
    best_score: float | None,
    content_priority: str,
    context_status: str,
    query_is_doctrinal: bool,
    query_is_normative: bool,
) -> float:
    score = best_score if best_score is not None else 0.0
    if "expanded" in context_status:
        score += 0.75
    if content_priority == "doctrinal":
        score += 0.5
    if content_priority == "normative":
        score += 0.45
    if query_is_normative and content_priority == "normative":
        score += 0.7
    if query_is_doctrinal and content_priority == "doctrinal":
        score += 0.7
    if query_is_doctrinal and content_priority == "introductory":
        score -= 2.0
    if context_status.startswith("anchor_only"):
        score -= 0.5
    return score


def _metadata_score(context: FinalContext) -> float:
    value = context.metadata.get("ranking_score", 0.0)
    return float(value if value is not None else 0.0)


def _diversity_relevance_floor(best_score: float) -> float:
    if best_score <= 0:
        return best_score - 1.0
    return best_score - max(1.5, abs(best_score) * 0.35)


def _query_mentions_specific_document(query: str) -> bool:
    normalized = query.lower()
    terms = set(re.findall(r"[\wÀ-ÿ]+", normalized))
    return bool(terms & SPECIFIC_DOCUMENT_TERMS)


def _parent_unit_matches_query(context: FinalContext, query: str) -> bool:
    query_terms = _topic_terms(query)
    if not query_terms:
        return True
    included_chunks = context.metadata.get("included_chunks")
    included_text = ""
    if isinstance(included_chunks, list):
        included_text = " ".join(
            " ".join(
                str(chunk.get(key) or "")
                for key in (
                    "document_title",
                    "chapter_title",
                    "section_title",
                    "subsection_title",
                    "full_reference",
                    "chunk_type",
                    "text",
                )
            )
            for chunk in included_chunks
            if isinstance(chunk, dict)
        )

    parent_text = " ".join(
        [
            str(context.parent_title or ""),
            str(context.parent_key or ""),
            str(context.document or ""),
            str(context.metadata.get("document_title") or ""),
            str(context.metadata.get("full_reference") or ""),
            str(context.metadata.get("document_type") or ""),
            str(context.metadata.get("source_category") or ""),
            str(context.context_text[:2000] or ""),
            included_text[:4000],
        ]
    )
    parent_terms = _topic_terms(parent_text)
    return bool(query_terms & parent_terms)


def _topic_terms(text: str) -> set[str]:
    normalized = unicodedata.normalize("NFKD", text.lower())
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    terms = set(re.findall(r"[\wÀ-ÿ]+", normalized))
    stopwords = {
        "para",
        "pela",
        "pelo",
        "como",
        "qual",
        "quais",
        "trata",
        "tratar",
        "significa",
        "significado",
        "responda",
        "explique",
        "sobre",
        "tradicao",
        "reformada",
        "reformado",
        "ensina",
        "ensino",
        "alianca",
        "igrejas",
        "igreja",
        "evangelicas",
        "evangelica",
        "brasil",
        "documentos",
        "documento",
        "corpus",
        "pergunta",
        "capitulo",
        "chapter",
        "section",
        "secao",
        "confissao",
        "catecismo",
        "canones",
    }
    return {_simple_stem(term) for term in terms if len(term) >= 4 and term not in stopwords}


def _simple_stem(term: str) -> str:
    if term.endswith("ões"):
        return term[:-3] + "ao"
    if term.endswith("s") and len(term) > 5:
        return term[:-1]
    return term


def _truncate_context(text: str, max_chars: int) -> tuple[str, bool]:
    if max_chars <= 0 or len(text) <= max_chars:
        return text, False
    marker = "\n\n[TRUNCADO POR LIMITE DE CONTEXTO]"
    usable = max(0, max_chars - len(marker))
    return text[:usable].rstrip() + marker, True


def _unique(values) -> list[Any]:
    seen: set[Any] = set()
    result: list[Any] = []
    for value in values:
        if value is None or value == "":
            continue
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _min_nullable(values) -> int | None:
    concrete = [value for value in values if value is not None]
    return min(concrete) if concrete else None


def _max_nullable(values) -> int | None:
    concrete = [value for value in values if value is not None]
    return max(concrete) if concrete else None


def _format_pages(page_start: int | None, page_end: int | None) -> str:
    if page_start is None and page_end is None:
        return "não informado"
    if page_end is None or page_start == page_end:
        return str(page_start)
    return f"{page_start}-{page_end}"
