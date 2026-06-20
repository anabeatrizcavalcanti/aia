"""
Reordenação de candidatos por Cross-Encoder.
"""


def rerank_with_cross_encoder(
    query: str,
    candidates: list[dict[str, str]],
    top_k: int = 5,
) -> list[dict[str, str]]:
    """
    Reordena candidatos avaliando conjuntamente pergunta e chunk.
    """
    raise NotImplementedError("Cross-Encoder reranking is not implemented yet.")
