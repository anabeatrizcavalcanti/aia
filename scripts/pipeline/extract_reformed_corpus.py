"""Script-base para extração textual do corpus reformado com PyMuPDF."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT_DIR / "corpus" / "raw" / "reformed_manifest.json"
DEFAULT_OUTPUT_DIR = ROOT_DIR / "corpus" / "processed" / "extracted"


def load_manifest(path: Path) -> dict[str, Any]:
    """Carrega o manifesto reformado validado."""
    return json.loads(path.read_text(encoding="utf-8"))


def extract_pages_from_pdf(pdf_path: Path, document_id: str) -> list[dict[str, Any]]:
    """Extrai texto por página de um PDF, preservando metadados mínimos."""
    try:
        import fitz  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError("PyMuPDF não está instalado.") from exc

    pages: list[dict[str, Any]] = []
    with fitz.open(pdf_path) as pdf:
        for index, page in enumerate(pdf, start=1):
            pages.append(
                {
                    "document_id": document_id,
                    "raw_path": pdf_path.as_posix(),
                    "page_number": index,
                    "text": page.get_text("text"),
                }
            )
    return pages


def write_extracted_pages(document_id: str, pages: list[dict[str, Any]], output_dir: Path) -> Path:
    """Grava páginas extraídas em JSONL."""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{document_id}.pages.jsonl"
    with output_path.open("w", encoding="utf-8") as file:
        for page in pages:
            file.write(json.dumps(page, ensure_ascii=False) + "\n")
    return output_path


def run_extraction(manifest_path: Path, output_dir: Path, dry_run: bool) -> list[Path]:
    """Executa a extração textual prevista para o corpus reformado."""
    manifest = load_manifest(manifest_path)
    created_files: list[Path] = []

    for document in manifest["documents"]:
        raw_path = ROOT_DIR / document["raw_path"]
        if dry_run:
            print(f"Extração planejada para `{document['document_id']}` a partir de `{document['raw_path']}`.")
            continue
        pages = extract_pages_from_pdf(raw_path, document["document_id"])
        created_files.append(write_extracted_pages(document["document_id"], pages, output_dir))

    return created_files


def build_parser() -> argparse.ArgumentParser:
    """Cria o parser de linha de comando."""
    parser = argparse.ArgumentParser(description="Extrai texto por página dos PDFs do corpus reformado.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--dry-run", action="store_true", help="Mostra o plano de extração sem gravar arquivos.")
    return parser


def main() -> int:
    """Ponto de entrada do script de extração."""
    args = build_parser().parse_args()
    run_extraction(args.manifest, args.output_dir, args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
