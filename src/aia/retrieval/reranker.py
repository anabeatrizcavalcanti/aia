"""Compatibilidade para imports antigos do reranker.

O caminho atual usa ``cross_encoder_reranker.CrossEncoderReranker`` e
``reranked_retriever.RerankedRetriever``.
"""

from aia.retrieval.cross_encoder_reranker import (
    CrossEncoderReranker,
    CrossEncoderRerankerError,
    build_reranker_text,
)
from aia.retrieval.reranked_retriever import RerankedRetriever

__all__ = [
    "CrossEncoderReranker",
    "CrossEncoderRerankerError",
    "RerankedRetriever",
    "build_reranker_text",
]
