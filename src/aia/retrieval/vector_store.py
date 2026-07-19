"""
Integração planejada com o banco vetorial ChromaDB.
"""

from pathlib import Path


def build_vector_store(chunks_path: Path, persist_directory: Path) -> None:
    """
    Cria ou atualiza o índice vetorial a partir dos chunks processados.
    """
    raise NotImplementedError("Vector store integration is not implemented yet.")
