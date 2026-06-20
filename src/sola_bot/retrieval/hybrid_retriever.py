"""
Recuperação híbrida combinando busca vetorial e busca lexical.

A estratégia principal deverá combinar dense retrieval, BM25, RRF,
reranking e filtros por metadados.
"""


def hybrid_retrieve(query: str, corpus_id: str, top_k: int = 5) -> list[dict[str, str]]:
    """
    Recupera candidatos usando uma estratégia híbrida.
    """
    raise NotImplementedError("Hybrid retrieval is not implemented yet.")
