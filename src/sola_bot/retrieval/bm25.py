"""
Busca lexical BM25 para recuperação de trechos confessionais.

Este módulo deverá preservar precisão terminológica em perguntas doutrinárias
nas próximas etapas do projeto.
"""


def build_bm25_index(chunks: list[str]) -> object:
    """
    Constrói um índice BM25 a partir dos chunks processados.
    """
    raise NotImplementedError("BM25 index build is not implemented yet.")


def search_bm25(query: str, top_k: int = 5) -> list[dict[str, str]]:
    """
    Recupera chunks por busca lexical BM25.
    """
    raise NotImplementedError("BM25 search is not implemented yet.")
