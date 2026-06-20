"""
Estruturas para manifestos de documentos processados.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CorpusDocument:
    """
    Representa um documento controlado do corpus.
    """

    document_id: str
    title: str
    tradition: str
    source_path: Path
