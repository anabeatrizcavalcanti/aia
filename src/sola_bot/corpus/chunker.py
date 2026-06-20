"""
Módulo responsável pela divisão de documentos em chunks auditáveis.
"""


def chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 150) -> list[str]:
    """
    Divide um texto normalizado em chunks.

    A estratégia final de chunking será definida em etapa posterior.
    """
    raise NotImplementedError("Text chunking is not implemented yet.")
