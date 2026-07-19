"""
Módulo responsável pela recuperação de chunks relevantes.
"""


def retrieve_relevant_chunks(query: str, corpus_id: str, top_k: int = 5) -> list[dict[str, str]]:
    """
    Recupera chunks relevantes para uma pergunta, respeitando filtros de corpus.

    Esta função será conectada ao ChromaDB em etapa futura.
    """
    raise NotImplementedError("Retriever is not implemented yet.")
