"""Extrai texto dos PDFs do corpus reformado usando PyMuPDF.

Esta etapa preserva texto por pagina e metadados documentais. Ela nao gera
chunks, embeddings, indice vetorial nem chama servicos externos.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT_DIR / "corpus" / "raw" / "reformed_manifest.json"
DEFAULT_OUTPUT_DIR = ROOT_DIR / "corpus" / "processed" / "extracted" / "reformed"
DEFAULT_REPORT_DIR = ROOT_DIR / "corpus" / "reports" / "extraction"
EXPECTED_DOCUMENT_IDS = {
    "confissao-fe-westminster",
    "canones-de-dort",
    "catecismo-heidelberg",
    "confissao-batista-londres-1689",
}


def relative_path(path: Path) -> str:
    """Retorna um caminho relativo ao repositorio em formato POSIX."""
    return path.relative_to(ROOT_DIR).as_posix()


def load_manifest(path: Path) -> dict[str, Any]:
    """Carrega o manifesto reformado validado."""
    if not path.exists():
        raise FileNotFoundError(f"Manifesto nao encontrado: {relative_path(path)}")
    return json.loads(path.read_text(encoding="utf-8"))


def validate_manifest(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    """Valida os documentos esperados e os caminhos dos PDFs brutos."""
    documents = manifest.get("documents", [])
    if not isinstance(documents, list):
        raise ValueError("O manifesto nao contem uma lista valida em `documents`.")

    document_ids = {document.get("document_id") for document in documents}
    missing = EXPECTED_DOCUMENT_IDS - document_ids
    unexpected = document_ids - EXPECTED_DOCUMENT_IDS
    if missing:
        raise ValueError(f"Documentos esperados ausentes no manifesto: {sorted(missing)}")
    if unexpected:
        raise ValueError(f"Documentos inesperados no manifesto reformado: {sorted(unexpected)}")

    for document in documents:
        raw_path_value = document.get("raw_path")
        if not isinstance(raw_path_value, str):
            raise ValueError(f"`raw_path` invalido para {document.get('document_id')}.")
        if not raw_path_value.startswith("corpus/raw/reformed/"):
            raise ValueError(f"Fonte fora do corpus reformado: {raw_path_value}")
        raw_path = ROOT_DIR / raw_path_value
        if not raw_path.exists():
            raise FileNotFoundError(f"PDF nao encontrado: {raw_path_value}")
        if raw_path.suffix.lower() != ".pdf":
            raise ValueError(f"Arquivo bruto nao e PDF: {raw_path_value}")

    return sorted(documents, key=lambda item: item["document_id"])


def extract_pdf_pages(pdf_path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """Extrai o texto de cada pagina de um PDF."""
    try:
        import fitz  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError("PyMuPDF nao esta instalado; nao foi possivel extrair os PDFs.") from exc

    pages: list[dict[str, Any]] = []
    warnings: list[str] = []
    with fitz.open(pdf_path) as pdf:
        for page_index, page in enumerate(pdf, start=1):
            text = page.get_text("text")
            char_count = len(text)
            is_empty = not text.strip()
            page_warnings: list[str] = []
            if is_empty:
                page_warnings.append("empty_page_text")
                warnings.append(f"Pagina {page_index} nao retornou texto extraivel.")

            pages.append(
                {
                    "page_number": page_index,
                    "text": text,
                    "char_count": char_count,
                    "is_empty": is_empty,
                    "warnings": page_warnings,
                }
            )

    return pages, warnings


def build_extracted_document(manifest: dict[str, Any], document: dict[str, Any]) -> dict[str, Any]:
    """Monta o documento extraido com metadados e paginas."""
    raw_path = ROOT_DIR / document["raw_path"]
    pages, warnings = extract_pdf_pages(raw_path)

    return {
        "document_id": document["document_id"],
        "title": document["title"],
        "corpus_id": manifest["corpus_id"],
        "tradition_family": document["tradition_family"],
        "tradition_branch": document["tradition_branch"],
        "document_type": document["document_type"],
        "language": document.get("language", "pt"),
        "raw_path": document["raw_path"],
        "extraction_backend": "pymupdf",
        "pages_count": len(pages),
        "pages": pages,
        "warnings": warnings,
    }


def write_extracted_document(document_data: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
    """Grava o JSON e o TXT legivel de um documento extraido."""
    output_dir.mkdir(parents=True, exist_ok=True)
    document_id = document_data["document_id"]
    json_path = output_dir / f"{document_id}.extracted.json"
    txt_path = output_dir / f"{document_id}.extracted.txt"

    json_path.write_text(json.dumps(document_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    txt_parts: list[str] = []
    for page in document_data["pages"]:
        txt_parts.append(f"===== PAGE {page['page_number']} =====")
        txt_parts.append(page["text"].rstrip())
        txt_parts.append("")
    txt_path.write_text("\n".join(txt_parts).rstrip() + "\n", encoding="utf-8")

    return json_path, txt_path


def summarize_document(document_data: dict[str, Any], json_path: Path, txt_path: Path) -> dict[str, Any]:
    """Cria um resumo de extracao para relatorios."""
    pages = document_data["pages"]
    empty_pages = [page["page_number"] for page in pages if page["is_empty"]]
    very_short_pages = [
        page["page_number"]
        for page in pages
        if page["char_count"] < 100 and not page["is_empty"]
    ]
    total_chars = sum(page["char_count"] for page in pages)

    return {
        "document_id": document_data["document_id"],
        "title": document_data["title"],
        "raw_path": document_data["raw_path"],
        "pages_count": document_data["pages_count"],
        "total_chars": total_chars,
        "empty_pages": empty_pages,
        "very_short_pages": very_short_pages,
        "warnings": document_data["warnings"],
        "json_path": relative_path(json_path),
        "txt_path": relative_path(txt_path),
    }


def build_extraction_report(
    manifest_path: Path,
    output_dir: Path,
    summaries: list[dict[str, Any]],
) -> dict[str, Any]:
    """Monta o relatorio geral de extracao."""
    status = "PASS"
    if any(summary["empty_pages"] or summary["warnings"] for summary in summaries):
        status = "PARTIAL"
    if len(summaries) != len(EXPECTED_DOCUMENT_IDS):
        status = "FAIL"

    return {
        "status": status,
        "corpus_id": "reformed",
        "manifest_path": relative_path(manifest_path),
        "output_dir": relative_path(output_dir),
        "documents_processed": len(summaries),
        "documents": summaries,
        "scope_not_executed": [
            "chunks_final",
            "embeddings",
            "vector_index",
            "chatbot",
            "ocr",
            "openai_api_call",
            "manual_doctrinal_editing",
        ],
    }


def write_extraction_reports(report: dict[str, Any], report_dir: Path) -> tuple[Path, Path]:
    """Grava relatorios de extracao em JSON e Markdown."""
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / "extraction_report.json"
    md_path = report_dir / "extraction_report.md"

    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Relatorio de extracao do corpus reformado",
        "",
        "## Status",
        "",
        report["status"],
        "",
        "## Sintese",
        "",
        (
            f"A extracao processou {report['documents_processed']} documentos do corpus reformado "
            "a partir do manifesto validado. O texto foi preservado por pagina, com caminho bruto, "
            "identificador documental e metadados confessionais."
        ),
        "",
        "## Documentos processados",
        "",
    ]

    for document in report["documents"]:
        lines.extend(
            [
                f"### {document['title']}",
                "",
                f"- `document_id`: `{document['document_id']}`",
                f"- PDF bruto: `{document['raw_path']}`",
                f"- Paginas extraidas: {document['pages_count']}",
                f"- Caracteres extraidos: {document['total_chars']}",
                f"- Paginas vazias: {document['empty_pages'] or 'nenhuma ocorrencia'}",
                f"- Paginas muito curtas: {document['very_short_pages'] or 'nenhuma ocorrencia'}",
                f"- JSON: `{document['json_path']}`",
                f"- TXT: `{document['txt_path']}`",
                "",
            ]
        )

    lines.extend(
        [
            "## Escopo mantido fora desta etapa",
            "",
            "- Nao foram gerados chunks finais.",
            "- Nao foram gerados embeddings.",
            "- Nao foi criado indice vetorial.",
            "- Nao houve chamada a OpenAI.",
            "- Nao houve OCR.",
            "- Nao houve alteracao manual de conteudo doutrinario.",
        ]
    )

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


def run_extraction(manifest_path: Path, output_dir: Path, report_dir: Path, dry_run: bool) -> dict[str, Any]:
    """Executa a extracao textual do corpus reformado."""
    manifest = load_manifest(manifest_path)
    documents = validate_manifest(manifest)
    summaries: list[dict[str, Any]] = []

    for document in documents:
        if dry_run:
            print(f"Extracao planejada para {document['document_id']} a partir de {document['raw_path']}.")
            continue
        document_data = build_extracted_document(manifest, document)
        json_path, txt_path = write_extracted_document(document_data, output_dir)
        summaries.append(summarize_document(document_data, json_path, txt_path))

    report = build_extraction_report(manifest_path, output_dir, summaries)
    if not dry_run:
        write_extraction_reports(report, report_dir)
    return report


def build_parser() -> argparse.ArgumentParser:
    """Cria o parser de linha de comando."""
    parser = argparse.ArgumentParser(description="Extrai texto por pagina dos PDFs do corpus reformado.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--dry-run", action="store_true", help="Mostra o plano sem gravar arquivos.")
    return parser


def main() -> int:
    """Ponto de entrada do script de extracao."""
    args = build_parser().parse_args()
    try:
        report = run_extraction(args.manifest, args.output_dir, args.report_dir, args.dry_run)
    except Exception as exc:
        print(f"A extracao falhou: {exc}", file=sys.stderr)
        return 1

    if not args.dry_run:
        print(f"A extracao processou {report['documents_processed']} documentos do corpus reformado.")
        print(f"Status da extracao: {report['status']}.")
    return 0 if report["status"] in {"PASS", "PARTIAL"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
