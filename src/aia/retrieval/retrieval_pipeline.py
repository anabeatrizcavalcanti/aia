"""Pipeline final de retrieval do corpus documental da Aliança."""

from __future__ import annotations

import os
from dataclasses import replace
from typing import Any

from aia.retrieval.context_consolidator import (
    ContextConsolidator,
    build_source_map,
    classify_query_intent,
    normative_subject_scope_coverage_query,
    normative_subject_scope_framing_chunk_ids,
    query_mentions_doctrinal_terms,
    query_mentions_denominational_scope,
    query_requests_document_inventory,
    query_requests_institutional_doctrinal_bridge,
)
from aia.retrieval.final_context import RetrievalContextPackage
from aia.retrieval.hierarchical_retriever import HierarchicalRetriever
from aia.retrieval.parent_context import ParentContext
from aia.retrieval.query_scope import QueryDocumentScope, scoped_filters_for_query
from aia.retrieval.reranked_retriever import RerankedRetriever
from aia.retrieval.retrieval_result import RetrievalResult


class RetrievalPipeline:
    """Integra recuperação hierárquica e consolidação final de contexto."""

    alliance_doctrinal_document_ids = ("confissao-fe-congregacional-alianca",)

    def __init__(
        self,
        final_context_top_k: int = 4,
        max_total_context_chars: int = 18000,
        max_context_chars_per_parent: int = 9000,
        hierarchical_retriever: HierarchicalRetriever | None = None,
        context_consolidator: ContextConsolidator | None = None,
    ) -> None:
        self.final_context_top_k = final_context_top_k
        self.max_total_context_chars = max_total_context_chars
        self.max_context_chars_per_parent = max_context_chars_per_parent
        anchor_candidate_k = _int_env("RERANKED_TOP_K", max(30, final_context_top_k * 8))
        hybrid_candidate_k = _int_env("HYBRID_CANDIDATE_K", max(40, final_context_top_k * 10))
        self.hierarchical_retriever = hierarchical_retriever or HierarchicalRetriever(
            reranked_top_k=anchor_candidate_k,
            reranked_retriever=RerankedRetriever(
                hybrid_candidate_k=hybrid_candidate_k,
                final_top_k=anchor_candidate_k,
            ),
        )
        self.context_consolidator = context_consolidator or ContextConsolidator(
            final_context_top_k=final_context_top_k,
            max_total_context_chars=max_total_context_chars,
            max_context_chars_per_parent=max_context_chars_per_parent,
        )

    def retrieve(
        self,
        query: str,
        filters: dict[str, Any] | None = None,
    ) -> RetrievalContextPackage:
        """Executa o fluxo completo até o pacote final de contextos."""
        effective_filters, document_scope = scoped_filters_for_query(query=query, filters=filters)
        parent_contexts = self._retrieve_parent_contexts(query=query, filters=effective_filters)
        parent_contexts, normative_scope_metadata = self._supplement_parent_contexts_for_normative_subject_scope(
            query=query,
            filters=effective_filters,
            parent_contexts=parent_contexts,
        )
        parent_contexts, supplemental_metadata = self._supplement_parent_contexts_for_document_coverage(
            query=query,
            filters=effective_filters,
            parent_contexts=parent_contexts,
        )
        package = self._consolidate(
            query=query,
            parent_contexts=parent_contexts,
            filters=effective_filters,
        )
        package = self._apply_query_document_scope(package, document_scope)
        if document_scope is not None:
            package.metadata["query_document_scope"] = _document_scope_metadata(document_scope)
        if supplemental_metadata["applied"]:
            package.metadata["supplemental_retrieval"] = supplemental_metadata
        if normative_scope_metadata["applied"]:
            package.metadata["normative_subject_scope_supplement"] = normative_scope_metadata
        package = self._retry_when_source_type_is_missing(
            query=query,
            filters=effective_filters,
            package=package,
        )
        package = self._apply_query_document_scope(package, document_scope)
        if document_scope is not None:
            package.metadata["query_document_scope"] = _document_scope_metadata(document_scope)
        if normative_scope_metadata["applied"]:
            package.metadata["normative_subject_scope_supplement"] = normative_scope_metadata
        return package

    def _retrieve_once(
        self,
        query: str,
        filters: dict[str, Any] | None = None,
    ) -> RetrievalContextPackage:
        """Executa uma rodada de retrieval com filtros explícitos."""
        parent_contexts = self._retrieve_parent_contexts(query=query, filters=filters)
        return self._consolidate(query=query, parent_contexts=parent_contexts, filters=filters)

    def _retrieve_parent_contexts(
        self,
        query: str,
        filters: dict[str, Any] | None = None,
    ) -> list[ParentContext]:
        """Recupera contextos hierárquicos antes da consolidação final."""
        return self.hierarchical_retriever.retrieve(query=query, filters=filters)

    def _consolidate(
        self,
        query: str,
        parent_contexts: list[ParentContext],
        filters: dict[str, Any] | None = None,
    ) -> RetrievalContextPackage:
        """Consolida contextos pré-recuperados em pacote final."""
        return self.context_consolidator.consolidate(
            query=query,
            parent_contexts=parent_contexts,
            filters=filters,
        )

    def _supplement_parent_contexts_for_document_coverage(
        self,
        query: str,
        filters: dict[str, Any] | None,
        parent_contexts: list[ParentContext],
    ) -> tuple[list[ParentContext], dict[str, Any]]:
        """Adiciona buscas filtradas quando a pergunta pede cobertura documental ampla."""
        if filters:
            return parent_contexts, {"applied": False, "reason": "explicit_filters_present"}

        supplemental_requests = self._document_coverage_requests(query)
        if not supplemental_requests:
            return parent_contexts, {"applied": False, "reason": "query_does_not_need_document_coverage"}

        combined = list(parent_contexts)
        attempts: list[dict[str, Any]] = []
        for supplemental_query, supplemental_filter in supplemental_requests:
            supplemental_contexts = self._retrieve_parent_contexts(
                query=supplemental_query,
                filters=supplemental_filter,
            )
            attempts.append(
                {
                    "query": supplemental_query,
                    "filters": supplemental_filter,
                    "context_count": len(supplemental_contexts),
                }
            )
            combined.extend(supplemental_contexts)

        deduplicated = _deduplicate_parent_contexts(combined)
        return deduplicated, {
            "applied": True,
            "reason": "document_coverage_query_supplemented",
            "initial_context_count": len(parent_contexts),
            "supplemental_attempts": attempts,
            "combined_context_count": len(combined),
            "deduplicated_context_count": len(deduplicated),
        }

    def _supplement_parent_contexts_for_normative_subject_scope(
        self,
        query: str,
        filters: dict[str, Any] | None,
        parent_contexts: list[ParentContext],
    ) -> tuple[list[ParentContext], dict[str, Any]]:
        """Adiciona unidades de enquadramento para perguntas normativas por sujeito."""
        document_id = str((filters or {}).get("document_id") or "")
        framing_chunk_ids = normative_subject_scope_framing_chunk_ids(
            query=query,
            document_id=document_id or None,
        )
        if not framing_chunk_ids:
            return parent_contexts, {"applied": False, "reason": "no_normative_subject_framing_units"}

        already_present = {
            chunk_id
            for context in parent_contexts
            for chunk_id in [context.anchor_chunk_id, *context.included_chunk_ids]
            if chunk_id
        }
        missing_chunk_ids = [chunk_id for chunk_id in framing_chunk_ids if chunk_id not in already_present]
        if not missing_chunk_ids:
            return parent_contexts, {"applied": False, "reason": "framing_units_already_present"}

        context_builder = getattr(self.hierarchical_retriever, "context_builder", None)
        chunk_index = getattr(context_builder, "chunk_index", None)
        build_contexts = getattr(context_builder, "build_contexts", None)
        if not isinstance(chunk_index, dict) or not callable(build_contexts):
            return parent_contexts, {
                "applied": False,
                "reason": "context_builder_unavailable",
                "requested_chunk_ids": list(framing_chunk_ids),
            }

        anchor_results: list[RetrievalResult] = []
        unavailable_chunk_ids: list[str] = []
        for chunk_id in missing_chunk_ids:
            chunk = chunk_index.get(chunk_id)
            if not isinstance(chunk, dict):
                unavailable_chunk_ids.append(chunk_id)
                continue
            anchor_results.append(
                RetrievalResult.from_chroma(
                    chunk_id=chunk_id,
                    metadata=chunk,
                    text=str(chunk.get("text") or chunk.get("embedding_text") or ""),
                    distance=0.0,
                )
            )

        if not anchor_results:
            return parent_contexts, {
                "applied": False,
                "reason": "framing_chunks_unavailable",
                "requested_chunk_ids": list(framing_chunk_ids),
                "unavailable_chunk_ids": unavailable_chunk_ids,
            }

        coverage_query = normative_subject_scope_coverage_query(query)
        supplemental_contexts = build_contexts(query=coverage_query, anchor_results=anchor_results)
        combined = _deduplicate_parent_contexts([*parent_contexts, *supplemental_contexts])
        return combined, {
            "applied": True,
            "reason": "normative_subject_framing_units_added",
            "requested_chunk_ids": list(framing_chunk_ids),
            "added_chunk_ids": [context.anchor_chunk_id for context in supplemental_contexts],
            "coverage_query": coverage_query,
            "unavailable_chunk_ids": unavailable_chunk_ids,
            "initial_context_count": len(parent_contexts),
            "combined_context_count": len(combined),
        }

    def _document_coverage_requests(self, query: str) -> list[tuple[str, dict[str, Any]]]:
        requests: list[tuple[str, dict[str, Any]]] = []
        if query_requests_document_inventory(query):
            normative_query = (
                f"{query} Constituição Regimento Código de Ética decisões conciliares resoluções "
                "documentos normativos da Aliança"
            )
            doctrinal_query = (
                f"{query} Confissão de Fé Congregacional doutrina igreja governo congregacional "
                "regra de fé e prática"
            )
            requests.append((normative_query, {"source_category": "denominational_normative_document"}))
            requests.extend(
                (doctrinal_query, {"document_id": document_id})
                for document_id in self.alliance_doctrinal_document_ids
            )
        elif query_requests_institutional_doctrinal_bridge(query):
            doctrinal_query = (
                f"{query} Confissão de Fé Congregacional doutrina igreja governo congregacional "
                "ordem espiritual Palavra normas institucionais"
            )
            normative_query = (
                f"{query} Constituição Regimento Código de Ética decisões conciliares resoluções "
                "normas institucionais da Aliança"
            )
            requests.extend(
                (doctrinal_query, {"document_id": document_id})
                for document_id in self.alliance_doctrinal_document_ids
            )
            requests.append((normative_query, {"source_category": "denominational_normative_document"}))
        return requests

    def _retry_when_source_type_is_missing(
        self,
        query: str,
        filters: dict[str, Any] | None,
        package: RetrievalContextPackage,
    ) -> RetrievalContextPackage:
        """Refaz a busca quando a pergunta pede uma natureza documental ausente no pacote final."""
        if filters and filters.get("source_category"):
            return package

        intent = classify_query_intent(query)
        priorities = {context.content_priority for context in package.contexts}
        retry_attempts: list[tuple[dict[str, Any], str]] = []

        if intent in {"normative", "mixed"} and "normative" not in priorities:
            retry_attempts.append(
                (
                    {"source_category": "denominational_normative_document"},
                    "missing_normative_context",
                )
            )
        if (
            intent in {"doctrinal", "mixed"}
            and query_mentions_doctrinal_terms(query)
            and "doctrinal" not in priorities
        ):
            if query_mentions_denominational_scope(query):
                retry_attempts.extend(
                    (
                        {"document_id": document_id},
                        "missing_alliance_doctrinal_context",
                    )
                    for document_id in self.alliance_doctrinal_document_ids
                )
            retry_attempts.append(
                (
                    {"source_category": "doctrinal_document"},
                    "missing_doctrinal_context",
                )
            )

        if not retry_attempts:
            return package

        for retry_filter, retry_reason in retry_attempts:
            retry_filters = dict(filters or {})
            retry_filters.update(retry_filter)
            retry_package = self._retrieve_once(query=query, filters=retry_filters)
            if not retry_package.contexts:
                continue

            retry_package.metadata["fallback_retry"] = {
                "reason": retry_reason,
                "filters": retry_filter,
                "initial_context_count": package.context_count,
                "initial_content_priorities": sorted(priorities),
            }
            return retry_package

        return package

    def _apply_query_document_scope(
        self,
        package: RetrievalContextPackage,
        document_scope: QueryDocumentScope | None,
    ) -> RetrievalContextPackage:
        """Remove contextos fora do documento explicitamente pedido."""
        if document_scope is None:
            return package

        retained = [
            context
            for context in package.contexts
            if context.document_id == document_scope.document_id
        ]
        removed = [
            context
            for context in package.contexts
            if context.document_id != document_scope.document_id
        ]
        if not removed:
            metadata = dict(package.metadata)
            metadata["document_scope_guard"] = {
                "applied": True,
                "document_id": document_scope.document_id,
                "removed_contexts": [],
                "removed_documents": [],
            }
            return replace(package, metadata=metadata)

        ranked_contexts = [
            replace(context, rank=rank)
            for rank, context in enumerate(retained, start=1)
        ]
        metadata = dict(package.metadata)
        metadata["document_scope_guard"] = {
            "applied": True,
            "document_id": document_scope.document_id,
            "removed_contexts": [context.parent_key for context in removed],
            "removed_documents": _unique(context.document_id for context in removed),
        }
        return RetrievalContextPackage(
            query=package.query,
            contexts=ranked_contexts,
            context_count=len(ranked_contexts),
            total_context_chars=sum(context.context_char_count for context in ranked_contexts),
            documents=sorted({context.document_id for context in ranked_contexts}),
            source_map=build_source_map(ranked_contexts),
            retrieval_stages=package.retrieval_stages,
            filters=package.filters,
            metadata=metadata,
        )


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name, "").strip()
    if not value:
        return default
    try:
        parsed = int(value)
    except ValueError:
        return default
    return max(1, parsed)


def _deduplicate_parent_contexts(contexts: list[ParentContext]) -> list[ParentContext]:
    """Remove contextos repetidos vindos de buscas suplementares."""
    seen: set[tuple[str, str]] = set()
    deduplicated: list[ParentContext] = []
    for context in contexts:
        key = (context.parent_key, context.anchor_chunk_id)
        if key in seen:
            continue
        seen.add(key)
        deduplicated.append(context)
    return deduplicated


def _document_scope_metadata(document_scope: QueryDocumentScope) -> dict[str, Any]:
    return {
        "applied": True,
        "document_id": document_scope.document_id,
        "document_label": document_scope.document_label,
        "matched_alias": document_scope.matched_alias,
        "match_type": document_scope.match_type,
        "policy": "exclusive_document_scope",
    }


def _unique(values) -> list[Any]:
    seen: set[Any] = set()
    result: list[Any] = []
    for value in values:
        if value is None or value == "" or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
