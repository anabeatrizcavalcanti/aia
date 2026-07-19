"""Reranking neural com Cross-Encoder."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

try:
    from sentence_transformers import CrossEncoder
except ImportError:  # pragma: no cover - validado no fluxo de execução
    CrossEncoder = None

from aia.retrieval.retrieval_result import RetrievalResult


DEFAULT_RERANKER_MODEL = "cross-encoder/ms-marco-TinyBERT-L2-v2"
DEFAULT_MAX_TEXT_CHARS = 3500


class CrossEncoderRerankerError(RuntimeError):
    """Erro da camada de reranking neural."""


def build_reranker_text(
    result: RetrievalResult,
    max_chars: int = DEFAULT_MAX_TEXT_CHARS,
    include_metadata: bool = True,
) -> str:
    """Monta o texto enviado ao Cross-Encoder."""
    parts: list[str] = []
    if include_metadata:
        metadata_lines = [
            ("Documento", result.document),
            ("Tipo documental", result.metadata.get("document_type")),
            ("Categoria", result.metadata.get("source_category")),
            ("Referência completa", result.metadata.get("full_reference")),
            ("Capítulo", result.chapter_title or result.chapter_reference),
            ("Seção", result.section_title or result.section_reference),
            ("Referência", result.section_reference),
            ("Artigo", result.metadata.get("article_number")),
            ("Parágrafo", result.metadata.get("paragraph_label") or result.metadata.get("paragraph_number")),
            ("Inciso", result.metadata.get("inciso")),
            ("Tipo", result.chunk_type),
        ]
        parts.extend(f"{label}: {value}" for label, value in metadata_lines if value)
        parts.append("")

    parts.extend(["Texto:", result.text])
    reranker_text = "\n".join(parts).strip()
    if max_chars > 0 and len(reranker_text) > max_chars:
        return reranker_text[:max_chars].rstrip()
    return reranker_text


class CrossEncoderReranker:
    """Pontua pares pergunta/chunk com um Cross-Encoder."""

    def __init__(
        self,
        model_name: str = DEFAULT_RERANKER_MODEL,
        max_text_chars: int = DEFAULT_MAX_TEXT_CHARS,
        include_metadata: bool = True,
        model: Any | None = None,
    ) -> None:
        self.model_name = model_name
        self.max_text_chars = max_text_chars
        self.include_metadata = include_metadata
        if model is not None:
            self.model = model
            return
        if CrossEncoder is None:
            raise CrossEncoderRerankerError(
                "sentence-transformers não está instalado; CrossEncoder indisponível."
            )
        try:
            self.model = CrossEncoder(model_name)
        except Exception as exc:
            raise CrossEncoderRerankerError(
                f"Não foi possível carregar o modelo Cross-Encoder `{model_name}`. Erro original: {exc!r}"
            ) from exc

    def rerank(
        self,
        query: str,
        candidates: list[RetrievalResult],
        top_k: int = 5,
    ) -> list[RetrievalResult]:
        """Reordena candidatos pelo score do Cross-Encoder."""
        if top_k < 1:
            raise CrossEncoderRerankerError("top_k deve ser maior ou igual a 1.")
        unique_candidates = _deduplicate_candidates(candidates)
        if not unique_candidates:
            return []

        pairs = [
            (
                query,
                build_reranker_text(
                    result,
                    max_chars=self.max_text_chars,
                    include_metadata=self.include_metadata,
                ),
            )
            for result in unique_candidates
        ]
        scores = [float(score) for score in self.model.predict(pairs)]
        reranked = [
            self._with_rerank_metadata(result, score, rank)
            for rank, (result, score) in enumerate(zip(unique_candidates, scores, strict=True), start=1)
        ]
        return sorted(reranked, key=lambda result: result.score or 0.0, reverse=True)[:top_k]

    def _with_rerank_metadata(
        self,
        result: RetrievalResult,
        reranker_score: float,
        pre_rerank_rank: int,
    ) -> RetrievalResult:
        """Preserva metadados prévios e registra o score neural."""
        metadata = dict(result.metadata)
        metadata["retrieval_stage"] = "reranked"
        metadata["reranker_provider"] = "sentence_transformers"
        metadata["reranker_model"] = self.model_name
        metadata["reranker_score"] = reranker_score
        metadata["pre_rerank_rank"] = pre_rerank_rank
        metadata["pre_rerank_score"] = result.score
        metadata["pre_rerank_sources"] = _pre_rerank_sources(metadata)
        return replace(result, score=reranker_score, metadata=metadata)


def _deduplicate_candidates(candidates: list[RetrievalResult]) -> list[RetrievalResult]:
    """Remove `chunk_id` duplicado preservando a primeira ocorrência."""
    seen: set[str] = set()
    unique: list[RetrievalResult] = []
    for result in candidates:
        if result.chunk_id in seen:
            continue
        seen.add(result.chunk_id)
        unique.append(result)
    return unique


def _pre_rerank_sources(metadata: dict[str, Any]) -> list[str]:
    """Lê fontes de retrieval anteriores quando registradas."""
    sources = metadata.get("retrieval_sources")
    if isinstance(sources, list):
        return [str(source) for source in sources]
    source = metadata.get("retrieval_source")
    if source:
        return [str(source)]
    return []
