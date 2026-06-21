"""Script-base para chunking estrutural do corpus reformado."""

from __future__ import annotations

import argparse
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_INPUT_DIR = ROOT_DIR / "corpus" / "processed" / "normalized"
DEFAULT_OUTPUT_DIR = ROOT_DIR / "corpus" / "processed" / "chunks"

CHUNK_METADATA_FIELDS = (
    "chunk_id",
    "document_id",
    "document",
    "corpus_id",
    "tradition_family",
    "tradition_branch",
    "document_type",
    "section_title",
    "section_reference",
    "chunk_type",
    "page_start",
    "page_end",
    "text",
    "embedding_text",
    "source_path",
    "retrieval_namespace",
)


def get_chunking_strategy(document_id: str) -> str:
    """Retorna a estratégia estrutural prevista para um documento reformado."""
    strategies = {
        "confissao-fe-westminster": "documento -> zona documental -> capítulo -> seção",
        "canones-de-dort": "documento -> capítulo doutrinário -> artigo ou erro/refutação",
        "catecismo-heidelberg": "documento -> parte -> Dia do Senhor -> pergunta e resposta",
        "confissao-batista-londres-1689": "documento -> capítulo -> parágrafo/seção numerada",
    }
    return strategies[document_id]


def chunk_document(document_id: str) -> list[dict[str, str]]:
    """Gera chunks estruturais para um documento.

    A implementação definitiva dependerá da revisão dos relatórios de análise
    estrutural produzidos nesta SPEC.
    """
    raise NotImplementedError(f"Chunking estrutural ainda não implementado para {document_id}.")


def build_parser() -> argparse.ArgumentParser:
    """Cria o parser de linha de comando."""
    parser = argparse.ArgumentParser(description="Prepara chunking estrutural do corpus reformado.")
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--document-id", choices=list({
        "confissao-fe-westminster",
        "canones-de-dort",
        "catecismo-heidelberg",
        "confissao-batista-londres-1689",
    }))
    parser.add_argument("--show-fields", action="store_true", help="Mostra os campos previstos para os chunks.")
    return parser


def main() -> int:
    """Ponto de entrada do script de chunking estrutural."""
    args = build_parser().parse_args()
    if args.show_fields:
        for field in CHUNK_METADATA_FIELDS:
            print(field)
        return 0
    if args.document_id:
        print(get_chunking_strategy(args.document_id))
        chunk_document(args.document_id)
    print("Informe --document-id para preparar uma estratégia específica ou --show-fields para ver os metadados.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
