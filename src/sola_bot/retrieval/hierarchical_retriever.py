"""Retriever hierárquico sobre resultados reranqueados."""

from __future__ import annotations

from typing import Any

from sola_bot.retrieval.parent_context import ParentContext, ParentContextBuilder
from sola_bot.retrieval.reranked_retriever import RerankedRetriever


class HierarchicalRetriever:
    """Expande resultados do RerankedRetriever para contexto estrutural."""

    def __init__(
        self,
        reranked_top_k: int = 5,
        parent_context_max_chars: int = 9000,
        sibling_window_before: int = 1,
        sibling_window_after: int = 1,
        include_full_parent_when_small: bool = True,
        full_parent_max_chars: int = 7000,
        include_metadata_header: bool = True,
        preserve_anchor_first: bool = True,
        reranked_retriever: RerankedRetriever | None = None,
        context_builder: ParentContextBuilder | None = None,
    ) -> None:
        self.reranked_top_k = reranked_top_k
        self.parent_context_max_chars = parent_context_max_chars
        self.sibling_window_before = sibling_window_before
        self.sibling_window_after = sibling_window_after
        self.reranked_retriever = reranked_retriever or RerankedRetriever(final_top_k=reranked_top_k)
        self.context_builder = context_builder or ParentContextBuilder(
            parent_context_max_chars=parent_context_max_chars,
            sibling_window_before=sibling_window_before,
            sibling_window_after=sibling_window_after,
            include_full_parent_when_small=include_full_parent_when_small,
            full_parent_max_chars=full_parent_max_chars,
            include_metadata_header=include_metadata_header,
            preserve_anchor_first=preserve_anchor_first,
        )

    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        filters: dict[str, Any] | None = None,
    ) -> list[ParentContext]:
        """Recupera chunks âncora reranqueados e constrói contextos expandidos."""
        anchor_top_k = top_k or self.reranked_top_k
        anchor_results = self.reranked_retriever.retrieve(
            query=query,
            top_k=anchor_top_k,
            filters=filters,
        )
        return self.context_builder.build_contexts(query=query, anchor_results=anchor_results)
