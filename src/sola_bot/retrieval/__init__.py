"""Módulos de embeddings, armazenamento vetorial e recuperação."""

from sola_bot.retrieval.final_context import FinalContext, RetrievalContextPackage
from sola_bot.retrieval.hierarchical_retriever import HierarchicalRetriever
from sola_bot.retrieval.parent_context import ParentContext, ParentContextBuilder
from sola_bot.retrieval.retrieval_result import RetrievalResult
from sola_bot.retrieval.retrieval_pipeline import RetrievalPipeline
from sola_bot.retrieval.vector_retriever import VectorRetriever

__all__ = [
    "FinalContext",
    "HierarchicalRetriever",
    "ParentContext",
    "ParentContextBuilder",
    "RetrievalResult",
    "RetrievalContextPackage",
    "RetrievalPipeline",
    "VectorRetriever",
]
