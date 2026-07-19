"""
Modelos e utilitários para metadados dos documentos e chunks.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ChunkMetadata:
    """
    Metadados mínimos associados a um chunk documental.
    """

    corpus_id: str
    document_id: str
    document_title: str
    tradition: str
    chunk_id: str


def build_chunk_metadata(
    corpus_id: str,
    document_id: str,
    document_title: str,
    tradition: str,
    chunk_id: str,
) -> ChunkMetadata:
    """
    Cria metadados para um chunk do corpus.
    """
    return ChunkMetadata(
        corpus_id=corpus_id,
        document_id=document_id,
        document_title=document_title,
        tradition=tradition,
        chunk_id=chunk_id,
    )
