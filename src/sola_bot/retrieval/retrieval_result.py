"""Estruturas de dados para resultados de recuperação documental."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class RetrievalResult:
    """Resultado estruturado retornado pelo retriever vetorial."""

    chunk_id: str
    document_id: str
    document: str
    chunk_type: str
    content_role: str | None
    section_title: str | None
    section_reference: str | None
    chapter_title: str | None
    chapter_reference: str | None
    page_start: int | None
    page_end: int | None
    source_path: str
    text_hash: str
    score: float | None
    distance: float | None
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_chroma(
        cls,
        chunk_id: str,
        metadata: dict[str, Any],
        text: str,
        distance: float | None,
    ) -> "RetrievalResult":
        """
        Constrói um resultado a partir da saída do ChromaDB.

        Nesta etapa, `score` recebe o mesmo valor de `distance`, pois o ChromaDB
        retorna distância. Valores menores indicam maior proximidade vetorial.
        """
        return cls(
            chunk_id=chunk_id,
            document_id=str(metadata.get("document_id", "")),
            document=str(metadata.get("document", "")),
            chunk_type=str(metadata.get("chunk_type", "")),
            content_role=_nullable_string(metadata.get("content_role")),
            section_title=_nullable_string(metadata.get("section_title")),
            section_reference=_nullable_string(metadata.get("section_reference")),
            chapter_title=_nullable_string(metadata.get("chapter_title")),
            chapter_reference=_nullable_string(metadata.get("chapter_reference")),
            page_start=_nullable_int(metadata.get("page_start")),
            page_end=_nullable_int(metadata.get("page_end")),
            source_path=str(metadata.get("source_path", "")),
            text_hash=str(metadata.get("text_hash", "")),
            score=distance,
            distance=distance,
            text=text,
            metadata=dict(metadata),
        )

    def to_dict(self) -> dict[str, Any]:
        """Converte o resultado para dicionário serializável."""
        return asdict(self)


def _nullable_string(value: Any) -> str | None:
    """Converte valores vazios ou nulos para `None`."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _nullable_int(value: Any) -> int | None:
    """Converte valores numéricos vindos de metadados para inteiro."""
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
