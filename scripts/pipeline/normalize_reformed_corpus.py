"""Normaliza mecanicamente os textos extraidos do corpus reformado.

A normalizacao desta SPEC e conservadora: preserva paginas, marcadores
estruturais, referencias biblicas e metadados. Ela nao gera chunks finais.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_INPUT_DIR = ROOT_DIR / "corpus" / "processed" / "extracted" / "reformed"
DEFAULT_OUTPUT_DIR = ROOT_DIR / "corpus" / "processed" / "normalized" / "reformed"
DEFAULT_REPORT_DIR = ROOT_DIR / "corpus" / "reports" / "normalization"
STRUCTURE_REPORT_DIR = ROOT_DIR / "corpus" / "reports" / "structure_analysis"
EXPECTED_DOCUMENT_IDS = {
    "confissao-fe-westminster",
    "canones-de-dort",
    "catecismo-heidelberg",
    "confissao-batista-londres-1689",
}
NORMALIZATION_STRATEGY = "mechanical_safe_normalization_v001"
STRUCTURAL_MARKERS = {
    "confissao-fe-westminster": ["CAPÍTULO", "DA ESCRITURA SAGRADA", "I."],
    "canones-de-dort": ["Capítulo da Doutrina", "Artigo", "Rejeição de Erros", "Refutação"],
    "catecismo-heidelberg": ["Dia do Senhor", "P.", "R."],
    "confissao-batista-londres-1689": ["CAPÍTULO", "AS SAGRADAS ESCRITURAS", "1."],
}


def relative_path(path: Path) -> str:
    """Retorna um caminho relativo ao repositorio em formato POSIX."""
    return path.relative_to(ROOT_DIR).as_posix()


def normalize_for_search(text: str) -> str:
    """Normaliza texto para buscas simples sem remover o texto original."""
    decomposed = unicodedata.normalize("NFKD", text)
    ascii_text = decomposed.encode("ascii", "ignore").decode("ascii")
    return ascii_text.lower()


def load_json(path: Path) -> dict[str, Any]:
    """Carrega um arquivo JSON."""
    return json.loads(path.read_text(encoding="utf-8"))


def load_structure_reports() -> dict[str, dict[str, Any]]:
    """Carrega os relatorios estruturais JSON disponiveis."""
    reports: dict[str, dict[str, Any]] = {}
    if not STRUCTURE_REPORT_DIR.exists():
        return reports
    for path in STRUCTURE_REPORT_DIR.glob("*.structure.json"):
        data = load_json(path)
        reports[data["document_id"]] = data
    return reports


def remove_control_characters(text: str) -> str:
    """Remove caracteres de controle, preservando quebras de linha e tabulacoes."""
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)


def recompose_safe_hyphenation(text: str) -> str:
    """Recompoe quebras por hifenizacao apenas em palavras alfabeticas."""
    return re.sub(r"(?<=[A-Za-zÀ-ÿ])-\n\s*(?=[a-zà-ÿ])", "", text)


def normalize_text(text: str) -> tuple[str, list[str]]:
    """Aplica normalizacoes mecanicas seguras e registra as acoes usadas."""
    actions: list[str] = []
    normalized = text

    updated = normalized.replace("\r\n", "\n").replace("\r", "\n")
    if updated != normalized:
        actions.append("normalized_line_endings")
    normalized = updated

    updated = normalized.replace("\u00a0", " ")
    if updated != normalized:
        actions.append("normalized_nbsp")
    normalized = updated

    updated = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", normalized)
    if updated != normalized:
        actions.append("removed_invisible_characters")
    normalized = updated

    updated = remove_control_characters(normalized)
    if updated != normalized:
        actions.append("removed_control_characters")
    normalized = updated

    updated = recompose_safe_hyphenation(normalized)
    if updated != normalized:
        actions.append("recomposed_safe_hyphenation")
    normalized = updated

    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in normalized.split("\n")]
    updated = "\n".join(lines)
    if updated != normalized:
        actions.append("normalized_whitespace")
    normalized = updated

    updated = re.sub(r"\n{3,}", "\n\n", normalized).strip()
    if updated != normalized:
        actions.append("normalized_excess_blank_lines")
    normalized = updated

    if not actions:
        actions.append("no_changes")
    return normalized, actions


def page_contains_marker(text: str, marker: str) -> bool:
    """Verifica marcador estrutural sem depender de acento ou caixa."""
    return normalize_for_search(marker) in normalize_for_search(text)


def classify_page_zone(
    document_id: str,
    page_number: int,
    text: str,
    structure_report: dict[str, Any] | None,
) -> tuple[str, list[str]]:
    """Classifica preliminarmente a zona documental de uma pagina."""
    warnings: list[str] = []
    introductory_pages = set(structure_report.get("introductory_pages", []) if structure_report else [])
    special_layout_pages = set(structure_report.get("special_layout_pages", []) if structure_report else [])
    searchable = normalize_for_search(text)

    if page_number in special_layout_pages:
        return "special_layout", warnings
    if page_number <= 5 and ("sumario" in searchable or "indice" in searchable):
        return "table_of_contents", warnings
    if page_number in introductory_pages:
        return "introductory_material", warnings
    if looks_like_reference_page(text):
        return "references_or_notes", warnings
    if any(page_contains_marker(text, marker) for marker in STRUCTURAL_MARKERS.get(document_id, [])):
        return "confessional_body", warnings

    return "unknown", warnings


def looks_like_reference_page(text: str) -> bool:
    """Identifica paginas dominadas por notas ou referencias numeradas."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) < 8:
        return False
    reference_like = sum(1 for line in lines if re.match(r"^(?:\[[0-9]+\]|[0-9]{1,2}[. ])", line))
    return reference_like / len(lines) > 0.7


def validate_extracted_files(input_dir: Path) -> list[Path]:
    """Valida a presenca dos quatro arquivos extraidos esperados."""
    if not input_dir.exists():
        raise FileNotFoundError(f"Diretorio de entrada nao encontrado: {relative_path(input_dir)}")
    files = sorted(input_dir.glob("*.extracted.json"))
    document_ids = {path.name.replace(".extracted.json", "") for path in files}
    missing = EXPECTED_DOCUMENT_IDS - document_ids
    unexpected = document_ids - EXPECTED_DOCUMENT_IDS
    if missing:
        raise FileNotFoundError(f"Arquivos extraidos ausentes: {sorted(missing)}")
    if unexpected:
        raise ValueError(f"Arquivos extraidos inesperados: {sorted(unexpected)}")
    return sorted(files)


def normalize_document(
    extracted_path: Path,
    output_dir: Path,
    structure_reports: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any], Path, Path]:
    """Normaliza um documento extraido e grava JSON/TXT normalizados."""
    extracted = load_json(extracted_path)
    document_id = extracted["document_id"]
    structure_report = structure_reports.get(document_id)
    pages: list[dict[str, Any]] = []
    document_warnings: list[str] = []

    for page in extracted["pages"]:
        normalized_text, actions = normalize_text(page.get("text", ""))
        zone, zone_warnings = classify_page_zone(
            document_id=document_id,
            page_number=page["page_number"],
            text=normalized_text,
            structure_report=structure_report,
        )
        page_warnings = list(page.get("warnings", [])) + zone_warnings

        pages.append(
            {
                "page_number": page["page_number"],
                "text": normalized_text,
                "char_count": len(normalized_text),
                "source_char_count": page.get("char_count", len(page.get("text", ""))),
                "page_zone": zone,
                "normalization_actions": actions,
                "warnings": page_warnings,
            }
        )

    marker_validation = validate_structural_markers(document_id, pages)
    missing_markers = [
        marker
        for marker, present in marker_validation.items()
        if not present
    ]
    if missing_markers:
        document_warnings.append(f"Marcadores estruturais nao encontrados: {missing_markers}")

    normalized = {
        "document_id": document_id,
        "title": extracted["title"],
        "corpus_id": extracted["corpus_id"],
        "tradition_family": extracted["tradition_family"],
        "tradition_branch": extracted["tradition_branch"],
        "document_type": extracted["document_type"],
        "language": extracted.get("language", "pt"),
        "raw_path": extracted["raw_path"],
        "input_extraction_file": relative_path(extracted_path),
        "structure_report_file": (
            relative_path(STRUCTURE_REPORT_DIR / f"{document_id}.structure.json")
            if (STRUCTURE_REPORT_DIR / f"{document_id}.structure.json").exists()
            else None
        ),
        "normalization_strategy": NORMALIZATION_STRATEGY,
        "pages_count": len(pages),
        "pages": pages,
        "marker_validation": marker_validation,
        "document_warnings": document_warnings,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{document_id}.normalized.json"
    txt_path = output_dir / f"{document_id}.normalized.txt"
    json_path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    txt_path.write_text(build_normalized_txt(pages), encoding="utf-8")
    return normalized, json_path, txt_path


def build_normalized_txt(pages: list[dict[str, Any]]) -> str:
    """Cria a versao TXT normalizada com separacao por pagina."""
    parts: list[str] = []
    for page in pages:
        parts.append(f"===== PAGE {page['page_number']} =====")
        parts.append(page["text"].rstrip())
        parts.append("")
    return "\n".join(parts).rstrip() + "\n"


def validate_structural_markers(document_id: str, pages: list[dict[str, Any]]) -> dict[str, bool]:
    """Valida se marcadores estruturais minimos permanecem no texto normalizado."""
    full_text = "\n".join(page["text"] for page in pages)
    return {
        marker: page_contains_marker(full_text, marker)
        for marker in STRUCTURAL_MARKERS[document_id]
    }


def summarize_document(normalized: dict[str, Any], json_path: Path, txt_path: Path) -> dict[str, Any]:
    """Cria resumo de normalizacao para relatorios."""
    action_counts: Counter[str] = Counter()
    zone_counts: Counter[str] = Counter()
    pages_with_warnings: list[int] = []
    for page in normalized["pages"]:
        action_counts.update(page["normalization_actions"])
        zone_counts.update([page["page_zone"]])
        if page["warnings"]:
            pages_with_warnings.append(page["page_number"])

    return {
        "document_id": normalized["document_id"],
        "title": normalized["title"],
        "raw_path": normalized["raw_path"],
        "input_extraction_file": normalized["input_extraction_file"],
        "pages_count": normalized["pages_count"],
        "total_chars": sum(page["char_count"] for page in normalized["pages"]),
        "normalization_actions": dict(sorted(action_counts.items())),
        "page_zones": dict(sorted(zone_counts.items())),
        "pages_with_warnings": pages_with_warnings,
        "marker_validation": normalized["marker_validation"],
        "document_warnings": normalized["document_warnings"],
        "json_path": relative_path(json_path),
        "txt_path": relative_path(txt_path),
    }


def build_normalization_report(input_dir: Path, output_dir: Path, summaries: list[dict[str, Any]]) -> dict[str, Any]:
    """Monta o relatorio geral de normalizacao."""
    status = "PASS"
    if any(summary["document_warnings"] for summary in summaries):
        status = "PARTIAL"
    if len(summaries) != len(EXPECTED_DOCUMENT_IDS):
        status = "FAIL"

    return {
        "status": status,
        "corpus_id": "reformed",
        "input_dir": relative_path(input_dir),
        "output_dir": relative_path(output_dir),
        "normalization_strategy": NORMALIZATION_STRATEGY,
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


def write_normalization_reports(report: dict[str, Any], report_dir: Path) -> tuple[Path, Path]:
    """Grava relatorios de normalizacao em JSON e Markdown."""
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / "normalization_report.json"
    md_path = report_dir / "normalization_report.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Relatorio de normalizacao do corpus reformado",
        "",
        "## Status",
        "",
        report["status"],
        "",
        "## Sintese",
        "",
        (
            f"A normalizacao processou {report['documents_processed']} documentos extraidos. "
            "As paginas foram preservadas como unidade de rastreabilidade, e as acoes aplicadas "
            "foram registradas pagina a pagina."
        ),
        "",
        "## Documentos normalizados",
        "",
    ]

    for document in report["documents"]:
        lines.extend(
            [
                f"### {document['title']}",
                "",
                f"- `document_id`: `{document['document_id']}`",
                f"- Paginas normalizadas: {document['pages_count']}",
                f"- Caracteres normalizados: {document['total_chars']}",
                f"- Acoes aplicadas: {document['normalization_actions']}",
                f"- Zonas preliminares: {document['page_zones']}",
                f"- Marcadores estruturais preservados: {document['marker_validation']}",
                f"- Paginas com avisos: {document['pages_with_warnings'] or 'nenhuma ocorrencia'}",
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


def run_normalization(input_dir: Path, output_dir: Path, report_dir: Path, dry_run: bool) -> dict[str, Any]:
    """Executa a normalizacao dos documentos extraidos."""
    input_files = validate_extracted_files(input_dir)
    structure_reports = load_structure_reports()
    summaries: list[dict[str, Any]] = []

    for input_path in input_files:
        if dry_run:
            print(f"Normalizacao planejada para {relative_path(input_path)}.")
            continue
        normalized, json_path, txt_path = normalize_document(input_path, output_dir, structure_reports)
        summaries.append(summarize_document(normalized, json_path, txt_path))

    report = build_normalization_report(input_dir, output_dir, summaries)
    if not dry_run:
        write_normalization_reports(report, report_dir)
    return report


def build_parser() -> argparse.ArgumentParser:
    """Cria o parser de linha de comando."""
    parser = argparse.ArgumentParser(description="Normaliza textos extraidos do corpus reformado.")
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--dry-run", action="store_true", help="Mostra o plano sem gravar arquivos.")
    return parser


def main() -> int:
    """Ponto de entrada do script de normalizacao."""
    args = build_parser().parse_args()
    try:
        report = run_normalization(args.input_dir, args.output_dir, args.report_dir, args.dry_run)
    except Exception as exc:
        print(f"A normalizacao falhou: {exc}", file=sys.stderr)
        return 1

    if not args.dry_run:
        print(f"A normalizacao processou {report['documents_processed']} documentos do corpus reformado.")
        print(f"Status da normalizacao: {report['status']}.")
    return 0 if report["status"] in {"PASS", "PARTIAL"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
