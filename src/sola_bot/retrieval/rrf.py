"""Fusão de rankings por Reciprocal Rank Fusion."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from sola_bot.retrieval.retrieval_result import RetrievalResult


def reciprocal_rank_fusion(
    ranked_lists: list[list[RetrievalResult]],
    k: int = 60,
    top_k: int = 5,
) -> list[RetrievalResult]:
    """
    Combina rankings usando Reciprocal Rank Fusion.

    A fórmula usada é `sum(1 / (k + rank))`, com rankings iniciando em 1.
    Chunks presentes em mais de uma lista acumulam pontuação.
    """
    scores: dict[str, float] = {}
    representatives: dict[str, RetrievalResult] = {}
    ranking_details: dict[str, list[dict[str, Any]]] = {}
    retrieval_sources: dict[str, set[str]] = {}

    for ranking_index, ranking in enumerate(ranked_lists, start=1):
        for rank, result in enumerate(ranking, start=1):
            source = str(result.metadata.get("retrieval_source") or f"ranking_{ranking_index}")
            increment = 1.0 / (k + rank)
            scores[result.chunk_id] = scores.get(result.chunk_id, 0.0) + increment
            representatives.setdefault(result.chunk_id, result)
            retrieval_sources.setdefault(result.chunk_id, set()).add(source)
            ranking_details.setdefault(result.chunk_id, []).append(
                {
                    "source": source,
                    "rank": rank,
                    "original_score": result.score,
                    "distance": result.distance,
                    "rrf_increment": increment,
                }
            )

    fused_ids = sorted(scores, key=scores.get, reverse=True)[:top_k]
    fused_results: list[RetrievalResult] = []
    for chunk_id in fused_ids:
        representative = representatives[chunk_id]
        metadata = dict(representative.metadata)
        metadata["rrf_score"] = scores[chunk_id]
        metadata["source_rankings"] = ranking_details[chunk_id]
        metadata["retrieval_sources"] = sorted(retrieval_sources[chunk_id])
        fused_results.append(
            replace(
                representative,
                score=scores[chunk_id],
                metadata=metadata,
            )
        )
    return fused_results
