"""Pipeline helpers for congregational normative documents.

The functions in this module mirror the existing reformed corpus pipeline:
extract PDF pages, normalize extracted text, create structural JSONL chunks,
consolidate document JSONL files, and audit the generated artifacts.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT_DIR / "corpus" / "raw" / "normative_manifest.json"
DEFAULT_EXTRACTED_DIR = ROOT_DIR / "corpus" / "processed" / "extracted" / "normative"
DEFAULT_NORMALIZED_DIR = ROOT_DIR / "corpus" / "processed" / "normalized" / "normative"
DEFAULT_CHUNKS_DIR = ROOT_DIR / "corpus" / "processed" / "chunks" / "normative"
DEFAULT_REPORT_DIR = ROOT_DIR / "corpus" / "reports" / "normative"
DEFAULT_TOPIC_MAP = ROOT_DIR / "config" / "normative_topic_map.json"
DEFAULT_TAXONOMY = ROOT_DIR / "config" / "normative_taxonomy.json"

EXPECTED_DOCUMENT_IDS = {
    "codigo-etica-ministro-alianca",
    "confissao-fe-congregacional-alianca",
    "constituicao-alianca-2022",
    "resolucao-alianca-01-2020",
    "regimento-interno-alianca-2022",
}
SCHEMA_VERSION = "normative-structural-chunk-v1"
RETRIEVAL_NAMESPACE = "congregational_normative"
NORMALIZATION_STRATEGY = "normative_mechanical_safe_normalization_v001"
MAX_CHUNK_CHARS = 3200
CONSOLIDATED_CHUNKS_FILE = "all_chunks.jsonl"

DOCUMENT_REFERENCE_LABELS = {
    "codigo-etica-ministro-alianca": "Código de Ética",
    "confissao-fe-congregacional-alianca": "Confissão de Fé Congregacional",
    "constituicao-alianca-2022": "Constituição da Aliança",
    "resolucao-alianca-01-2020": "Resolução Aliança nº 01/2020",
    "regimento-interno-alianca-2022": "Regimento Interno",
}

STRUCTURAL_MARKERS = {
    "codigo-etica-ministro-alianca": ["PREÂMBULO", "DAS DISPOSIÇÕES PRELIMINARES", "Art. 1º"],
    "confissao-fe-congregacional-alianca": [
        "CONFISSÃO DE FÉ CONGREGACIONAL",
        "CAPÍTULO I",
        "A INSTITUIÇÃO DAS IGREJAS",
    ],
    "constituicao-alianca-2022": ["PREÂMBULO", "CAPÍTULO I", "Art. 1º"],
    "resolucao-alianca-01-2020": ["RESOLUÇÃO ALIANÇA Nº 01", "CONSIDERANDO", "RESOLVE:"],
    "regimento-interno-alianca-2022": ["CAPÍTULO I", "SEÇÃO I", "Art. 1º"],
}

REQUIRED_NORMATIVE_FIELDS = {
    "chunk_id",
    "schema_version",
    "corpus_id",
    "retrieval_namespace",
    "doc_id",
    "document_id",
    "document_title",
    "denomination",
    "tradition",
    "document_type",
    "source_category",
    "resolution_number",
    "resolution_date",
    "page_start",
    "page_end",
    "text",
    "normalized_text",
    "full_reference",
    "document_structure_type",
    "paragraph_label",
    "paragraph_number_roman",
    "footnote_markers",
    "topic",
    "subtopic",
}

CHAPTER_RE = re.compile(r"^CAP[ÍI]TULO\s+([IVXLCDM]+|[0-9]+)\b(?:\s*(.*))?$", re.IGNORECASE)
SECTION_RE = re.compile(r"^SE[ÇC][ÃA]O\s+([IVXLCDM]+|[0-9]+)\b(?:\s*(.*))?$", re.IGNORECASE)
ARTICLE_RE = re.compile(r"^Art\.?\s*([0-9]+)([º°]?)(?:\.|\s*[–—-]|\s+(?=[A-ZÁÉÍÓÚÂÊÔÃÕ]))\s*(.*)$")
PARAGRAPH_RE = re.compile(r"^§\s*([0-9]+)([º°]?)\.?\s*(?:[–—-]\s*)?(.*)$", re.IGNORECASE)
PARAGRAFO_UNICO_RE = re.compile(r"^Par[aá]grafo\s+[úu]nico\.?\s*(?:[–—-]\s*)?(.*)$", re.IGNORECASE)
INCISO_RE = re.compile(r"^([IVXLCDM]{1,8})\s*(?:[.\-–—])\s*(.*)$", re.IGNORECASE)
ALINEA_RE = re.compile(r"^([a-z])\)\s*(.*)$")
CONFESSION_ROMAN_PARAGRAPH_RE = re.compile(
    r"^([IVXLCDM]{1,8})(?:\.?\s*[-–—]|\s+(?=[A-ZÁÉÍÓÚÂÊÔÃÕ]))\s*(.*)$"
)
FOOTNOTE_REFERENCE_RE = re.compile(r"^([0-9]{1,3})\.\s*(?=.*[A-Za-zÀ-ÿ])(.*)$")
CONFESSION_NUMBERED_POINT_RE = re.compile(r"^([0-9]{1,2})\s*(?:[-–—.]|$)\s*(.*)$")

BIBLE_BOOK_PATTERN = (
    r"(?:[1-3]\s*)?(?:gn|g[eê]n(?:esis)?|ex|[eê]x(?:odo)?|lv|lev[ií]tico|nm|"
    r"n[uú]m(?:eros)?|dt|js|jz|rt|sm|rs|reis|cr|ed|ne|et|j[oó]|sl|pv|ec|ct|is|"
    r"jr|lm|ez|dn|os|jl|am|ob|jn|mq|na|hc|sf|ag|zc|ml|mt|mateus|mc|marcos|"
    r"lc|lucas|jo|jo[aã]o|at|atos|rm|romanos|co|cor[ií]ntios|gl|g[aá]latas|"
    r"ef|ef[eé]sios|fl|fp|filipenses|cl|colossenses|ts|tessalonicenses|tm|"
    r"tim[oó]teo|tt|tito|fm|filemom|hb|hebreus|tg|tiago|pe|pd|pedro|jd|judas|"
    r"ap|apocalipse)"
)
BIBLE_REF_RE = re.compile(
    rf"\b{BIBLE_BOOK_PATTERN}\.?\s*[0-9]+(?:[:.][0-9]+)?(?:[-–][0-9]+)?",
    re.IGNORECASE,
)
BIBLE_REFERENCE_START_RE = re.compile(rf"^{BIBLE_BOOK_PATTERN}\.?\s*[0-9]", re.IGNORECASE)
INLINE_FOOTNOTE_REFERENCE_START_RE = re.compile(
    rf"\s+([0-9]{{1,3}})\.\s*(?={BIBLE_BOOK_PATTERN}\.?\s*[0-9])",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class TextLine:
    """A non-empty normalized line with page traceability."""

    page: int
    index: int
    text: str


def relative_path(path: Path) -> str:
    """Return a repository-relative POSIX path."""
    return path.relative_to(ROOT_DIR).as_posix()


def load_json(path: Path) -> dict[str, Any]:
    """Load a JSON file."""
    if not path.exists():
        raise FileNotFoundError(f"Arquivo nao encontrado: {relative_path(path)}")
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    """Write a formatted JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    """Write JSONL rows."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")


def normalize_for_search(text: str) -> str:
    """Lowercase text without accents for conservative matching."""
    decomposed = unicodedata.normalize("NFKD", text)
    ascii_text = decomposed.encode("ascii", "ignore").decode("ascii")
    return ascii_text.lower()


def slugify(value: str) -> str:
    """Create a stable slug fragment for chunk IDs."""
    ascii_text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_text.lower()).strip("-")
    return slug or "sem-referencia"


def roman_to_int(value: str) -> int:
    """Convert a roman numeral to an integer for sorting."""
    values = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    total = 0
    previous = 0
    for char in reversed(value.upper()):
        current = values.get(char, 0)
        if current < previous:
            total -= current
        else:
            total += current
            previous = current
    return total


def roman_sort_key(value: str) -> int:
    """Sort roman numerals before falling back to integers."""
    if re.fullmatch(r"[IVXLCDM]+", value.upper()):
        return roman_to_int(value)
    if value.isdigit():
        return int(value)
    return 10_000


def text_hash(text: str) -> str:
    """Return the SHA-256 hash for a chunk text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_manifest(path: Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    """Load and validate the normative manifest."""
    manifest = load_json(path)
    documents = manifest.get("documents", [])
    if not isinstance(documents, list):
        raise ValueError("O manifesto normativo nao contem uma lista valida em `documents`.")

    document_ids = {document.get("document_id") for document in documents}
    missing = EXPECTED_DOCUMENT_IDS - document_ids
    unexpected = document_ids - EXPECTED_DOCUMENT_IDS
    if missing:
        raise ValueError(f"Documentos normativos ausentes no manifesto: {sorted(missing)}")
    if unexpected:
        raise ValueError(f"Documentos normativos inesperados no manifesto: {sorted(unexpected)}")

    for document in documents:
        raw_path_value = document.get("raw_path")
        if not isinstance(raw_path_value, str):
            raise ValueError(f"`raw_path` invalido para {document.get('document_id')}.")
        if not raw_path_value.startswith("corpus/raw/normative/"):
            raise ValueError(f"Fonte fora do corpus normativo: {raw_path_value}")
        raw_path = ROOT_DIR / raw_path_value
        if not raw_path.exists():
            raise FileNotFoundError(f"PDF nao encontrado: {raw_path_value}")
        if raw_path.suffix.lower() != ".pdf":
            raise ValueError(f"Arquivo bruto nao e PDF: {raw_path_value}")
        if document.get("doc_id") != document.get("document_id"):
            raise ValueError(f"`doc_id` deve acompanhar `document_id` em {document.get('document_id')}.")

    return manifest


def manifest_documents_by_id(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Index manifest documents by document ID."""
    return {document["document_id"]: document for document in manifest["documents"]}


def extract_pdf_pages(pdf_path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """Extract text from every page of a PDF."""
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
    """Build extracted document data with page-level traceability."""
    raw_path = ROOT_DIR / document["raw_path"]
    pages, warnings = extract_pdf_pages(raw_path)
    return {
        "document_id": document["document_id"],
        "doc_id": document["doc_id"],
        "title": document["title"],
        "subtitle": document.get("subtitle"),
        "document_title": document["title"],
        "corpus_id": manifest["corpus_id"],
        "denomination": document["denomination"],
        "tradition": document["tradition"],
        "tradition_family": document["tradition_family"],
        "tradition_branch": document["tradition_branch"],
        "document_type": document["document_type"],
        "source_category": document["source_category"],
        "year": document.get("year"),
        "resolution_number": document.get("resolution_number"),
        "resolution_date": document.get("resolution_date"),
        "language": document.get("language", "pt"),
        "raw_path": document["raw_path"],
        "extraction_backend": "pymupdf",
        "pages_count": len(pages),
        "pages": pages,
        "warnings": warnings,
    }


def write_extracted_document(document_data: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
    """Write extracted JSON and TXT files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    document_id = document_data["document_id"]
    json_path = output_dir / f"{document_id}.extracted.json"
    txt_path = output_dir / f"{document_id}.extracted.txt"
    write_json(json_path, document_data)

    parts: list[str] = []
    for page in document_data["pages"]:
        parts.append(f"===== PAGE {page['page_number']} =====")
        parts.append(page["text"].rstrip())
        parts.append("")
    txt_path.write_text("\n".join(parts).rstrip() + "\n", encoding="utf-8")
    return json_path, txt_path


def summarize_extraction(document_data: dict[str, Any], json_path: Path, txt_path: Path) -> dict[str, Any]:
    """Summarize extracted document data for reports."""
    pages = document_data["pages"]
    return {
        "document_id": document_data["document_id"],
        "title": document_data["title"],
        "raw_path": document_data["raw_path"],
        "pages_count": document_data["pages_count"],
        "total_chars": sum(page["char_count"] for page in pages),
        "empty_pages": [page["page_number"] for page in pages if page["is_empty"]],
        "very_short_pages": [
            page["page_number"]
            for page in pages
            if page["char_count"] < 100 and not page["is_empty"]
        ],
        "warnings": document_data["warnings"],
        "json_path": relative_path(json_path),
        "txt_path": relative_path(txt_path),
    }


def run_extraction(
    manifest_path: Path = DEFAULT_MANIFEST,
    output_dir: Path = DEFAULT_EXTRACTED_DIR,
    report_dir: Path = DEFAULT_REPORT_DIR,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Run the extraction stage for normative documents."""
    manifest = load_manifest(manifest_path)
    summaries: list[dict[str, Any]] = []
    for document in sorted(manifest["documents"], key=lambda item: item["document_id"]):
        if dry_run:
            print(f"Extracao planejada para {document['document_id']} a partir de {document['raw_path']}.")
            continue
        extracted = build_extracted_document(manifest, document)
        json_path, txt_path = write_extracted_document(extracted, output_dir)
        summaries.append(summarize_extraction(extracted, json_path, txt_path))

    report = build_extraction_report(manifest_path, output_dir, summaries)
    if not dry_run:
        write_extraction_report(report, report_dir)
    return report


def build_extraction_report(manifest_path: Path, output_dir: Path, summaries: list[dict[str, Any]]) -> dict[str, Any]:
    """Build the extraction report."""
    status = "PASS"
    if any(summary["empty_pages"] or summary["warnings"] for summary in summaries):
        status = "PARTIAL"
    if {summary["document_id"] for summary in summaries} != EXPECTED_DOCUMENT_IDS:
        status = "FAIL"
    return {
        "status": status,
        "corpus_id": "congregational_normative",
        "manifest_path": relative_path(manifest_path),
        "output_dir": relative_path(output_dir),
        "documents_processed": len(summaries),
        "documents": summaries,
        "scope_not_executed": [
            "embeddings",
            "vector_index",
            "chatbot",
            "ocr",
            "openai_api_call",
            "manual_normative_editing",
        ],
    }


def write_extraction_report(report: dict[str, Any], report_dir: Path) -> tuple[Path, Path]:
    """Write extraction report files."""
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / "normative-extraction-report.json"
    md_path = report_dir / "normative-extraction-report.md"
    write_json(json_path, report)

    lines = [
        "# Relatório de extração do corpus normativo congregacional",
        "",
        "## Status",
        "",
        report["status"],
        "",
        "## Documentos extraídos",
        "",
    ]
    for document in report["documents"]:
        lines.extend(
            [
                f"### {document['title']}",
                "",
                f"- `document_id`: `{document['document_id']}`",
                f"- PDF bruto: `{document['raw_path']}`",
                f"- Páginas extraídas: {document['pages_count']}",
                f"- Caracteres extraídos: {document['total_chars']}",
                f"- Páginas sem texto: {document['empty_pages'] or 'nenhuma ocorrência'}",
                f"- Páginas muito curtas: {document['very_short_pages'] or 'nenhuma ocorrência'}",
                f"- JSON: `{document['json_path']}`",
                f"- TXT: `{document['txt_path']}`",
                "",
            ]
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


def remove_control_characters(text: str) -> str:
    """Remove control characters while preserving newlines and tabs."""
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)


def recompose_safe_hyphenation(text: str) -> str:
    """Recompose line-break hyphenation only for alphabetic words."""
    return re.sub(r"(?<=[A-Za-zÀ-ÿ])-\n\s*(?=[a-zà-ÿ])", "", text)


def strip_isolated_page_numbers(text: str) -> tuple[str, bool]:
    """Remove isolated numeric page labels at the beginning or end of a page."""
    lines = text.split("\n")
    changed = False
    while lines and re.fullmatch(r"\s*[0-9]{1,3}\s*", lines[0]):
        lines.pop(0)
        changed = True
    while lines and re.fullmatch(r"\s*[0-9]{1,3}\s*", lines[-1]):
        lines.pop()
        changed = True
    return "\n".join(lines), changed


def normalize_text(text: str) -> tuple[str, list[str], list[str]]:
    """Apply conservative mechanical normalization."""
    actions: list[str] = []
    warnings: list[str] = []
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

    updated, removed_page_number = strip_isolated_page_numbers(normalized)
    if removed_page_number:
        actions.append("removed_isolated_page_number")
    normalized = updated

    updated = re.sub(r"\n{3,}", "\n\n", normalized).strip()
    if updated != normalized:
        actions.append("normalized_excess_blank_lines")
    normalized = updated

    if not normalized.strip():
        warnings.append("empty_after_normalization")
    if not actions:
        actions.append("no_changes")
    return normalized, actions, warnings


def page_contains_marker(text: str, marker: str) -> bool:
    """Check a marker without accent/case sensitivity."""
    return normalize_for_search(marker) in normalize_for_search(text)


def classify_page_zone(document_id: str, page_number: int, text: str) -> str:
    """Classify page zone for traceability."""
    if not text.strip():
        return "empty"
    searchable = normalize_for_search(text)
    if document_id == "constituicao-alianca-2022" and page_number <= 2 and "indice" in searchable:
        return "table_of_contents"
    if document_id == "confissao-fe-congregacional-alianca" and (
        "confissao de fe congregacional" in searchable or "capitulo" in searchable
    ):
        return "confessional_body"
    if document_id == "resolucao-alianca-01-2020" and (
        "resolucao alianca" in searchable or "considerando" in searchable or "resolve" in searchable
    ):
        return "resolution_body"
    if "preambulo" in searchable:
        return "preamble_or_body"
    if (
        CHAPTER_RE.search(text)
        or SECTION_RE.search(text)
        or ARTICLE_RE.search(text)
        or "das disposicoes" in searchable
        or "dos principios" in searchable
    ):
        return "normative_body"
    return "unknown"


def build_normalized_txt(pages: list[dict[str, Any]]) -> str:
    """Build a human-readable normalized TXT file."""
    parts: list[str] = []
    for page in pages:
        parts.append(f"===== PAGE {page['page_number']} =====")
        parts.append(page["text"].rstrip())
        parts.append("")
    return "\n".join(parts).rstrip() + "\n"


def validate_structural_markers(document_id: str, pages: list[dict[str, Any]]) -> dict[str, bool]:
    """Validate minimum structural markers in normalized text."""
    full_text = "\n".join(page["text"] for page in pages)
    return {marker: page_contains_marker(full_text, marker) for marker in STRUCTURAL_MARKERS[document_id]}


def normalize_document(extracted_path: Path, output_dir: Path) -> tuple[dict[str, Any], Path, Path]:
    """Normalize an extracted document and write JSON/TXT outputs."""
    extracted = load_json(extracted_path)
    document_id = extracted["document_id"]
    pages: list[dict[str, Any]] = []
    document_warnings: list[str] = []

    for page in extracted["pages"]:
        normalized_text, actions, warnings = normalize_text(page.get("text", ""))
        zone = classify_page_zone(document_id, page["page_number"], normalized_text)
        page_warnings = list(page.get("warnings", [])) + warnings
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
    missing_markers = [marker for marker, present in marker_validation.items() if not present]
    if missing_markers:
        document_warnings.append(f"Marcadores estruturais nao encontrados: {missing_markers}")

    normalized = {
        "document_id": document_id,
        "doc_id": extracted["doc_id"],
        "title": extracted["title"],
        "subtitle": extracted.get("subtitle"),
        "document_title": extracted["document_title"],
        "corpus_id": extracted["corpus_id"],
        "denomination": extracted["denomination"],
        "tradition": extracted["tradition"],
        "tradition_family": extracted["tradition_family"],
        "tradition_branch": extracted["tradition_branch"],
        "document_type": extracted["document_type"],
        "source_category": extracted["source_category"],
        "year": extracted.get("year"),
        "resolution_number": extracted.get("resolution_number"),
        "resolution_date": extracted.get("resolution_date"),
        "language": extracted.get("language", "pt"),
        "raw_path": extracted["raw_path"],
        "input_extraction_file": relative_path(extracted_path),
        "normalization_strategy": NORMALIZATION_STRATEGY,
        "pages_count": len(pages),
        "pages": pages,
        "marker_validation": marker_validation,
        "document_warnings": document_warnings,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{document_id}.normalized.json"
    txt_path = output_dir / f"{document_id}.normalized.txt"
    write_json(json_path, normalized)
    txt_path.write_text(build_normalized_txt(pages), encoding="utf-8")
    return normalized, json_path, txt_path


def summarize_normalization(normalized: dict[str, Any], json_path: Path, txt_path: Path) -> dict[str, Any]:
    """Summarize normalization for reports."""
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


def run_normalization(
    input_dir: Path = DEFAULT_EXTRACTED_DIR,
    output_dir: Path = DEFAULT_NORMALIZED_DIR,
    report_dir: Path = DEFAULT_REPORT_DIR,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Run the normalization stage for normative documents."""
    if not input_dir.exists():
        raise FileNotFoundError(f"Diretorio de entrada nao encontrado: {relative_path(input_dir)}")
    input_files = sorted(input_dir.glob("*.extracted.json"))
    document_ids = {path.name.replace(".extracted.json", "") for path in input_files}
    if document_ids != EXPECTED_DOCUMENT_IDS:
        raise FileNotFoundError(f"Arquivos extraidos normativos invalidos: {sorted(document_ids)}")

    summaries: list[dict[str, Any]] = []
    for input_path in input_files:
        if dry_run:
            print(f"Normalizacao planejada para {relative_path(input_path)}.")
            continue
        normalized, json_path, txt_path = normalize_document(input_path, output_dir)
        summaries.append(summarize_normalization(normalized, json_path, txt_path))

    report = build_normalization_report(input_dir, output_dir, summaries)
    if not dry_run:
        write_normalization_report(report, report_dir)
    return report


def build_normalization_report(input_dir: Path, output_dir: Path, summaries: list[dict[str, Any]]) -> dict[str, Any]:
    """Build the normalization report."""
    status = "PASS"
    if any(summary["document_warnings"] for summary in summaries):
        status = "PARTIAL"
    if {summary["document_id"] for summary in summaries} != EXPECTED_DOCUMENT_IDS:
        status = "FAIL"
    return {
        "status": status,
        "corpus_id": "congregational_normative",
        "input_dir": relative_path(input_dir),
        "output_dir": relative_path(output_dir),
        "normalization_strategy": NORMALIZATION_STRATEGY,
        "documents_processed": len(summaries),
        "documents": summaries,
    }


def write_normalization_report(report: dict[str, Any], report_dir: Path) -> tuple[Path, Path]:
    """Write normalization report files."""
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / "normative-normalization-report.json"
    md_path = report_dir / "normative-normalization-report.md"
    write_json(json_path, report)
    lines = [
        "# Relatório de normalização do corpus normativo congregacional",
        "",
        "## Status",
        "",
        report["status"],
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
                f"- Páginas normalizadas: {document['pages_count']}",
                f"- Caracteres normalizados: {document['total_chars']}",
                f"- Ações aplicadas: {document['normalization_actions']}",
                f"- Zonas preliminares: {document['page_zones']}",
                f"- Marcadores estruturais preservados: {document['marker_validation']}",
                f"- Páginas com avisos: {document['pages_with_warnings'] or 'nenhuma ocorrência'}",
                f"- JSON: `{document['json_path']}`",
                f"- TXT: `{document['txt_path']}`",
                "",
            ]
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


def load_topic_map(path: Path = DEFAULT_TOPIC_MAP) -> dict[str, Any]:
    """Load the normative topic map."""
    return load_json(path)


def is_upper_heading(line: str) -> bool:
    """Return True when a line looks like an all-caps structural heading."""
    stripped = line.strip()
    if len(stripped) < 4 or len(stripped) > 140:
        return False
    if ARTICLE_RE.match(stripped) or CHAPTER_RE.match(stripped) or SECTION_RE.match(stripped):
        return False
    letters = [char for char in stripped if char.isalpha()]
    return len(letters) >= 4 and stripped.isupper()


def is_document_cover_line(line: str) -> bool:
    """Detect cover/header lines that are not structural boundaries."""
    normalized = normalize_for_search(line)
    cover_fragments = {
        "alianca das igrejas evangelicas congregacionais do brasil",
        "confissao de fe congregacional",
        "declaracao de fe da alianca das igrejas evangelicas congregacionais do brasil",
        "constituicao da alianca",
        "constituicao da alianca das igrejas evangelicas",
        "congregacionais do brasil",
        "regimento interno da alianca das igrejas evangelicas",
        "codigo de etica",
        "marco de 2022",
        "resolucao alianca no 01, de 23 de novembro de 2020.",
    }
    normalized = normalized.strip("()")
    return normalized in cover_fragments


def is_ethics_section_line(document_id: str, line: str) -> bool:
    """Detect top-level section titles in the ethics code."""
    if document_id != "codigo-etica-ministro-alianca":
        return False
    stripped = line.strip()
    normalized = normalize_for_search(stripped)
    if is_document_cover_line(stripped) or normalized == "preambulo":
        return False
    if normalized.startswith("o ministro"):
        return False
    return is_upper_heading(stripped) and normalized.startswith(("das ", "dos ", "da ", "do "))


def is_ethics_subsection_line(document_id: str, line: str) -> bool:
    """Detect internal all-caps subsections in the ethics code."""
    if document_id != "codigo-etica-ministro-alianca":
        return False
    stripped = line.strip()
    normalized = normalize_for_search(stripped)
    return is_upper_heading(stripped) and normalized.startswith("o ministro")


def is_boundary_line(document_id: str, line: str) -> bool:
    """Detect boundaries that end preambles or article segments."""
    stripped = line.strip()
    normalized = normalize_for_search(stripped)
    return (
        normalized == "preambulo"
        or bool(CHAPTER_RE.match(stripped))
        or bool(SECTION_RE.match(stripped))
        or bool(ARTICLE_RE.match(stripped))
        or is_ethics_section_line(document_id, stripped)
        or is_ethics_subsection_line(document_id, stripped)
    )


def merge_split_paragraph_markers(lines: list[TextLine]) -> list[TextLine]:
    """Merge PDF extraction artifacts such as a line with only `§`."""
    merged: list[TextLine] = []
    index = 0
    while index < len(lines):
        current = lines[index]
        next_line = lines[index + 1] if index + 1 < len(lines) else None
        if current.text.strip() == "§" and next_line and re.match(r"^[0-9]+[º°]?\.", next_line.text.strip()):
            merged.append(TextLine(page=current.page, index=current.index, text=f"§ {next_line.text.strip()}"))
            index += 2
            continue
        if next_line and re.fullmatch(r"[IVXLCDM]{1,8}\s*[-–—]", current.text.strip()):
            merged.append(TextLine(page=current.page, index=current.index, text=f"{current.text.strip()} {next_line.text.strip()}"))
            index += 2
            continue
        merged.append(current)
        index += 1
    return merged


def get_parsing_lines(normalized_document: dict[str, Any]) -> list[TextLine]:
    """Return non-empty lines used by the structural parser."""
    lines: list[TextLine] = []
    for page in normalized_document["pages"]:
        if page.get("page_zone") == "table_of_contents":
            continue
        for line_index, raw_line in enumerate(page.get("text", "").splitlines(), start=1):
            line = raw_line.strip()
            if not line:
                continue
            if re.fullmatch(r"[0-9]{1,3}", line):
                continue
            lines.append(TextLine(page=page["page_number"], index=line_index, text=line))
    return merge_split_paragraph_markers(lines)


def collect_heading_after_marker(
    lines: list[TextLine],
    marker_index: int,
    inline_title: str | None,
    document_id: str,
) -> tuple[str | None, int]:
    """Collect an uppercase title immediately following a chapter/section marker."""
    title_parts: list[str] = []
    if inline_title and inline_title.strip():
        title_parts.append(inline_title.strip())

    cursor = marker_index + 1
    last_consumed = marker_index
    while cursor < len(lines) and len(title_parts) < 3:
        candidate = lines[cursor].text.strip()
        if is_boundary_line(document_id, candidate):
            break
        if not is_upper_heading(candidate) or is_document_cover_line(candidate):
            break
        title_parts.append(candidate)
        last_consumed = cursor
        cursor += 1
    return (" ".join(title_parts).strip() or None), last_consumed


def parse_article_heading(line: str) -> dict[str, Any]:
    """Parse an article heading line."""
    match = ARTICLE_RE.match(line.strip())
    if not match:
        raise ValueError(f"Linha de artigo invalida: {line}")
    number, suffix, remainder = match.groups()
    return {
        "article_number": number,
        "article_display": f"Art. {number}{suffix or ''}",
        "article_remainder": remainder.strip(),
    }


def parse_item_marker(line: str) -> dict[str, Any] | None:
    """Parse paragraph, inciso, or alinea markers at the start of a line."""
    stripped = line.strip()
    unique = PARAGRAFO_UNICO_RE.match(stripped)
    if unique:
        return {
            "type": "paragraph",
            "paragraph_number": "único",
            "paragraph_label": "Parágrafo único",
            "item_label": "Parágrafo único",
        }
    paragraph = PARAGRAPH_RE.match(stripped)
    if paragraph:
        number, suffix, _ = paragraph.groups()
        label = f"§ {number}{suffix or 'º'}"
        return {
            "type": "paragraph",
            "paragraph_number": f"{number}{suffix or 'º'}",
            "paragraph_label": label,
            "item_label": label,
        }
    alinea = ALINEA_RE.match(stripped)
    if alinea:
        letter = alinea.group(1).lower()
        return {"type": "alinea", "alinea": letter, "item_label": f"alínea {letter}"}
    inciso = INCISO_RE.match(stripped)
    if inciso and not CHAPTER_RE.match(stripped):
        roman = inciso.group(1).upper()
        if roman in {"I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII", "XIV", "XV"}:
            return {"type": "inciso", "inciso": roman, "item_label": f"inciso {roman}"}
    return None


def title_for_reference(title: str | None) -> str | None:
    """Format an extracted all-caps heading for references without changing metadata."""
    if not title:
        return None
    lowered = title.strip().lower()
    words = lowered.split()
    keep_lower = {"a", "as", "o", "os", "e", "da", "das", "de", "do", "dos", "em", "na", "no"}
    formatted = []
    for index, word in enumerate(words):
        formatted.append(word if index > 0 and word in keep_lower else word[:1].upper() + word[1:])
    return " ".join(formatted)


def make_full_reference(
    document_id: str,
    context: dict[str, Any],
    article_display: str | None = None,
    paragraph_number: str | None = None,
    inciso: str | None = None,
    alinea: str | None = None,
    document_structure_type: str | None = None,
) -> str:
    """Build a human-readable structural reference."""
    parts = [DOCUMENT_REFERENCE_LABELS[document_id]]
    if document_structure_type == "preamble":
        parts.append("PREÂMBULO")
        return ", ".join(parts)

    if document_id == "confissao-fe-congregacional-alianca":
        if document_structure_type == "canon_books_table":
            if context.get("chapter_number"):
                parts.append(f"Capítulo {context['chapter_number']}")
            if context.get("chapter_title"):
                parts.append(title_for_reference(context.get("chapter_title")))
            parts.append("Livros do Antigo e Novo Testamento")
            return ", ".join(part for part in parts if part)
        if document_structure_type == "numbered_doctrinal_point":
            parts.append("A Instituição das Igrejas e a Ordem Apontada nelas por Jesus Cristo")
            if context.get("numbered_point"):
                parts.append(f"ponto {context['numbered_point']}")
            return ", ".join(parts)
        if context.get("chapter_number"):
            parts.append(f"Capítulo {context['chapter_number']}")
        if context.get("chapter_title"):
            parts.append(title_for_reference(context.get("chapter_title")))
        if context.get("paragraph_number_roman"):
            parts.append(f"parágrafo {context['paragraph_number_roman']}")
        return ", ".join(part for part in parts if part)

    if document_id == "resolucao-alianca-01-2020":
        if document_structure_type == "resolution_heading":
            parts.append("Cabeçalho")
            return ", ".join(parts)
        if document_structure_type == "resolution_ementa":
            parts.append("Ementa")
            return ", ".join(parts)
        if document_structure_type == "resolution_intro":
            parts.append("Texto introdutório")
            return ", ".join(parts)
        if document_structure_type == "resolution_considerando":
            parts.append(f"Considerando {context.get('considerando_number')}")
            return ", ".join(parts)
        if document_structure_type == "signature":
            parts.append("Assinatura")
            return ", ".join(parts)
        if context.get("chapter_number"):
            parts.append(f"Capítulo {context['chapter_number']}")
        if article_display:
            parts.append(article_display)
        if paragraph_number:
            parts.append(f"§ {paragraph_number}")
        if inciso:
            parts.append(f"inciso {inciso}")
        return ", ".join(part for part in parts if part)

    if document_id == "codigo-etica-ministro-alianca":
        section = title_for_reference(context.get("section_title"))
        subsection = title_for_reference(context.get("subsection_title"))
        if section:
            parts.append(section)
        if subsection:
            parts.append(subsection)
    else:
        if context.get("chapter_number"):
            parts.append(f"Capítulo {context['chapter_number']}")
        if context.get("section_number"):
            parts.append(f"Seção {context['section_number']}")

    if article_display:
        parts.append(article_display)
    if paragraph_number:
        parts.append("Parágrafo único" if paragraph_number == "único" else f"§ {paragraph_number}")
    if inciso:
        parts.append(f"inciso {inciso}")
    if alinea:
        parts.append(f"alínea {alinea}")
    return ", ".join(parts)


def join_structural_text(lines: list[TextLine]) -> str:
    """Join PDF-extracted lines while preserving legal/eccesiastical markers."""
    paragraphs: list[str] = []
    current = ""
    for line in lines:
        text = line.text.strip()
        starts_block = bool(ARTICLE_RE.match(text) or parse_item_marker(text))
        if starts_block and current:
            paragraphs.append(current.strip())
            current = text
            continue
        if not current:
            current = text
        elif current.endswith("-"):
            current = current[:-1] + text
        else:
            current = f"{current} {text}"
    if current:
        paragraphs.append(current.strip())
    return "\n\n".join(paragraphs).strip()


def extract_biblical_references(text: str) -> list[str]:
    """Extract parenthetical biblical references without removing them from text."""
    references: list[str] = []
    for match in re.finditer(r"\(([^)]*)\)", text):
        content = match.group(1).strip()
        if BIBLE_REF_RE.search(content):
            references.append(content)
    return references


def infer_topic(
    document: dict[str, Any],
    context: dict[str, Any],
    text: str,
    topic_map: dict[str, Any],
) -> tuple[str, str]:
    """Infer topic/subtopic using the configured topic map."""
    document_id = document["document_id"]
    default = topic_map.get("document_defaults", {}).get(document_id, topic_map.get("default", {}))
    selected = {
        "topic": default.get("topic", "denominational_governance"),
        "subtopic": default.get("subtopic", "general_governance"),
    }
    haystack = normalize_for_search(
        " ".join(
            [
                context.get("chapter_title") or "",
                context.get("section_title") or "",
                context.get("subsection_title") or "",
                text,
            ]
        )
    )
    for rule in topic_map.get("keyword_rules", []):
        keywords = [normalize_for_search(keyword) for keyword in rule.get("keywords", [])]
        if any(keyword and keyword in haystack for keyword in keywords):
            selected = {"topic": rule["topic"], "subtopic": rule["subtopic"]}
            break
    return selected["topic"], selected["subtopic"]


def build_embedding_text(chunk: dict[str, Any]) -> str:
    """Build enriched embedding text while preserving `text`."""
    parts = [
        f"Documento: {chunk['document_title']}",
        "Corpus: Normativo Congregacional",
        f"Tipo documental: {chunk['document_type']}",
        f"Referência: {chunk['full_reference']}",
        f"Tópico: {chunk['topic']} / {chunk['subtopic']}",
        f"Texto: {chunk['text']}",
    ]
    return "\n".join(parts)


def build_chunk(
    document: dict[str, Any],
    normalized_document: dict[str, Any],
    chunk_id: str,
    text: str,
    page_start: int,
    page_end: int,
    context: dict[str, Any],
    document_structure_type: str,
    topic_map: dict[str, Any],
    article_number: str | None = None,
    article_display: str | None = None,
    paragraph_number: str | None = None,
    paragraph_label: str | None = None,
    paragraph_number_roman: str | None = None,
    inciso: str | None = None,
    alinea: str | None = None,
    item_label: str | None = None,
    footnote_markers: list[str] | None = None,
    biblical_references: list[Any] | None = None,
    extra_metadata: dict[str, Any] | None = None,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    """Build a normative chunk."""
    full_reference = make_full_reference(
        document_id=document["document_id"],
        context=context,
        article_display=article_display,
        paragraph_number=paragraph_number,
        inciso=inciso,
        alinea=alinea,
        document_structure_type=document_structure_type,
    )
    topic, subtopic = infer_topic(document, context, text, topic_map)
    chunk_type = document_structure_type
    chunk = {
        "chunk_id": chunk_id,
        "schema_version": SCHEMA_VERSION,
        "corpus_id": normalized_document["corpus_id"],
        "retrieval_namespace": RETRIEVAL_NAMESPACE,
        "doc_id": document["document_id"],
        "document_id": document["document_id"],
        "document": document["title"],
        "document_title": document["title"],
        "denomination": document["denomination"],
        "tradition": document["tradition"],
        "tradition_family": document["tradition_family"],
        "tradition_branch": document["tradition_branch"],
        "document_type": document["document_type"],
        "source_category": document["source_category"],
        "year": document.get("year"),
        "resolution_number": document.get("resolution_number"),
        "resolution_date": document.get("resolution_date"),
        "language": document.get("language", "pt"),
        "chunk_type": chunk_type,
        "content_role": "normative",
        "is_doctrinal": False,
        "document_structure_type": document_structure_type,
        "chapter_number": context.get("chapter_number"),
        "chapter_title": context.get("chapter_title"),
        "chapter_reference": f"Capítulo {context['chapter_number']}" if context.get("chapter_number") else None,
        "section_number": context.get("section_number"),
        "section_title": context.get("section_title"),
        "subsection_title": context.get("subsection_title"),
        "section_reference": full_reference,
        "article_number": article_number,
        "article_label": article_display,
        "paragraph_number": paragraph_number,
        "paragraph_label": paragraph_label,
        "paragraph_number_roman": paragraph_number_roman,
        "inciso": inciso,
        "alinea": alinea,
        "item_label": item_label,
        "full_reference": full_reference,
        "page_start": page_start,
        "page_end": page_end,
        "text": text.strip(),
        "normalized_text": text.strip(),
        "embedding_text": "",
        "source_path": document["raw_path"],
        "normalized_source": f"corpus/processed/normalized/normative/{document['document_id']}.normalized.json",
        "text_hash": "",
        "footnote_markers": footnote_markers or [],
        "biblical_references": biblical_references if biblical_references is not None else extract_biblical_references(text),
        "topic": topic,
        "subtopic": subtopic,
        "warnings": warnings or [],
    }
    if extra_metadata:
        chunk.update(extra_metadata)
    chunk["embedding_text"] = build_embedding_text(chunk)
    chunk["text_hash"] = text_hash(chunk["text"])
    return chunk


def next_boundary_index(lines: list[TextLine], start_index: int, document_id: str) -> int:
    """Find the next top-level structural boundary."""
    for index in range(start_index, len(lines)):
        if is_boundary_line(document_id, lines[index].text):
            return index
    return len(lines)


def parse_document_segments(normalized_document: dict[str, Any]) -> dict[str, Any]:
    """Parse preamble and article segments with current structural context."""
    document_id = normalized_document["document_id"]
    lines = get_parsing_lines(normalized_document)
    context: dict[str, Any] = {
        "chapter_number": None,
        "chapter_title": None,
        "section_number": None,
        "section_title": None,
        "subsection_title": None,
    }
    preambles: list[dict[str, Any]] = []
    articles: list[dict[str, Any]] = []
    chapters: list[dict[str, Any]] = []
    sections: list[dict[str, Any]] = []
    unhandled_headings: list[dict[str, Any]] = []

    index = 0
    while index < len(lines):
        line = lines[index].text.strip()
        normalized = normalize_for_search(line)

        if normalized == "preambulo":
            end = next_boundary_index(lines, index + 1, document_id)
            preambles.append({"lines": lines[index:end], "context": context.copy()})
            index = end
            continue

        chapter_match = CHAPTER_RE.match(line)
        if chapter_match:
            chapter_number = chapter_match.group(1).upper()
            chapter_title, last_consumed = collect_heading_after_marker(
                lines, index, chapter_match.group(2), document_id
            )
            context.update(
                {
                    "chapter_number": chapter_number,
                    "chapter_title": chapter_title,
                    "section_number": None,
                    "section_title": None,
                    "subsection_title": None,
                }
            )
            chapters.append({"chapter_number": chapter_number, "chapter_title": chapter_title, "page": lines[index].page})
            index = last_consumed + 1
            continue

        section_match = SECTION_RE.match(line)
        if section_match:
            section_number = section_match.group(1).upper()
            section_title, last_consumed = collect_heading_after_marker(
                lines, index, section_match.group(2), document_id
            )
            context.update({"section_number": section_number, "section_title": section_title, "subsection_title": None})
            sections.append({"section_number": section_number, "section_title": section_title, "page": lines[index].page})
            index = last_consumed + 1
            continue

        if is_ethics_section_line(document_id, line):
            context.update({"section_number": None, "section_title": line, "subsection_title": None})
            sections.append({"section_number": None, "section_title": line, "page": lines[index].page})
            index += 1
            continue

        if is_ethics_subsection_line(document_id, line):
            context.update({"subsection_title": line})
            sections.append({"section_number": None, "section_title": line, "page": lines[index].page, "level": "subsection"})
            index += 1
            continue

        article_match = ARTICLE_RE.match(line)
        if article_match:
            end = next_boundary_index(lines, index + 1, document_id)
            heading = parse_article_heading(line)
            articles.append(
                {
                    "lines": lines[index:end],
                    "context": context.copy(),
                    "page_start": lines[index].page,
                    "page_end": lines[end - 1].page if end > index else lines[index].page,
                    **heading,
                }
            )
            index = end
            continue

        if is_upper_heading(line) and not is_document_cover_line(line):
            unhandled_headings.append({"page": lines[index].page, "text": line})
        index += 1

    return {
        "preambles": preambles,
        "articles": articles,
        "chapters": chapters,
        "sections": sections,
        "unhandled_headings": unhandled_headings,
        "line_count": len(lines),
    }


def document_structure_type_for_article(document: dict[str, Any]) -> str:
    """Return the article structure type for a document."""
    if document["document_type"] == "normative_ethics":
        return "ethics_article"
    return "normative_article"


def split_text_by_length(text: str, max_chars: int = MAX_CHUNK_CHARS) -> list[str]:
    """Split a long text conservatively by paragraphs/sentences."""
    if len(text) <= max_chars:
        return [text]
    parts: list[str] = []
    current = ""
    for paragraph in text.split("\n\n"):
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            parts.append(current)
            current = ""
        sentences = re.split(r"(?<=[.!?])\s+", paragraph)
        for sentence in sentences:
            candidate = f"{current} {sentence}".strip() if current else sentence
            if len(candidate) <= max_chars:
                current = candidate
            else:
                if current:
                    parts.append(current)
                current = sentence
    if current:
        parts.append(current)
    return parts


def split_article_units(article: dict[str, Any]) -> list[dict[str, Any]]:
    """Split an article by paragraph, inciso, or alinea markers."""
    lines: list[TextLine] = article["lines"]
    prefix_lines: list[TextLine] = [lines[0]]
    units: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    state: dict[str, Any] = {"paragraph_number": None, "inciso": None, "alinea": None}

    for line in lines[1:]:
        marker = parse_item_marker(line.text)
        if marker:
            if marker["type"] == "paragraph":
                state = {"paragraph_number": marker["paragraph_number"], "inciso": None, "alinea": None}
            elif marker["type"] == "inciso":
                state = {**state, "inciso": marker["inciso"], "alinea": None}
            elif marker["type"] == "alinea":
                state = {**state, "alinea": marker["alinea"]}

            if current:
                units.append(current)
            current = {
                "lines": [line],
                "document_structure_type": marker["type"],
                "paragraph_number": state.get("paragraph_number"),
                "inciso": state.get("inciso"),
                "alinea": state.get("alinea"),
                "item_label": marker.get("item_label"),
            }
            continue

        if current:
            current["lines"].append(line)
        else:
            prefix_lines.append(line)

    if current:
        units.append(current)

    if not units:
        return []
    for unit in units:
        unit["prefix_lines"] = prefix_lines
    return units


def article_to_chunks(
    article: dict[str, Any],
    document: dict[str, Any],
    normalized_document: dict[str, Any],
    topic_map: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build one or more chunks for an article."""
    article_type = document_structure_type_for_article(document)
    text = join_structural_text(article["lines"])
    base_id_parts = [f"artigo-{int(article['article_number']):03d}"]

    if len(text) <= MAX_CHUNK_CHARS:
        return [
            build_chunk(
                document=document,
                normalized_document=normalized_document,
                chunk_id=f"{document['document_id']}_{'_'.join(slugify(part) for part in base_id_parts)}",
                text=text,
                page_start=article["page_start"],
                page_end=article["page_end"],
                context=article["context"],
                document_structure_type=article_type,
                topic_map=topic_map,
                article_number=article["article_number"],
                article_display=article["article_display"],
            )
        ]

    units = split_article_units(article)
    if not units:
        split_parts = split_text_by_length(text)
        chunks: list[dict[str, Any]] = []
        for part_index, part in enumerate(split_parts, start=1):
            chunks.append(
                build_chunk(
                    document=document,
                    normalized_document=normalized_document,
                    chunk_id=(
                        f"{document['document_id']}_{slugify(base_id_parts[0])}_parte-{part_index:02d}"
                    ),
                    text=part,
                    page_start=article["page_start"],
                    page_end=article["page_end"],
                    context=article["context"],
                    document_structure_type=article_type,
                    topic_map=topic_map,
                    article_number=article["article_number"],
                    article_display=article["article_display"],
                    warnings=["article_split_by_length_without_structural_children"],
                )
            )
        return chunks

    chunks = []
    for unit_index, unit in enumerate(units, start=1):
        unit_lines = unit["prefix_lines"] + unit["lines"]
        unit_text = join_structural_text(unit_lines)
        split_parts = split_text_by_length(unit_text)
        for part_index, part in enumerate(split_parts, start=1):
            parts = [base_id_parts[0]]
            if unit.get("paragraph_number"):
                parts.append(f"paragrafo-{unit['paragraph_number']}")
            if unit.get("inciso"):
                parts.append(f"inciso-{unit['inciso']}")
            if unit.get("alinea"):
                parts.append(f"alinea-{unit['alinea']}")
            if not (unit.get("paragraph_number") or unit.get("inciso") or unit.get("alinea")):
                parts.append(f"item-{unit_index:02d}")
            if len(split_parts) > 1:
                parts.append(f"parte-{part_index:02d}")
            chunk_id = f"{document['document_id']}_{'_'.join(slugify(part) for part in parts)}"
            page_start = unit["lines"][0].page
            page_end = unit["lines"][-1].page
            warnings = ["article_split_by_structural_children"]
            if len(split_parts) > 1:
                warnings.append("structural_child_split_by_length")
            chunks.append(
                build_chunk(
                    document=document,
                    normalized_document=normalized_document,
                    chunk_id=chunk_id,
                    text=part,
                    page_start=page_start,
                    page_end=page_end,
                    context=article["context"],
                    document_structure_type=unit["document_structure_type"],
                    topic_map=topic_map,
                    article_number=article["article_number"],
                    article_display=article["article_display"],
                    paragraph_number=unit.get("paragraph_number"),
                    inciso=unit.get("inciso"),
                    alinea=unit.get("alinea"),
                    item_label=unit.get("item_label"),
                    warnings=warnings,
                )
            )
    return chunks


def is_confession_final_section_line(line: str) -> bool:
    """Detect the final congregational church-order section."""
    return normalize_for_search(line).startswith(
        "a instituicao das igrejas e a ordem apontada nelas por jesus cristo"
    )


def parse_footnote_reference_lines(lines: list[TextLine]) -> tuple[list[dict[str, str]], dict[str, str]]:
    """Parse numbered biblical reference lines and their continuations."""
    references: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for line in lines:
        match = footnote_reference_start_match(line.text)
        if match:
            if current:
                references.append(current)
            current = {"marker": match.group(1), "reference": match.group(2).strip()}
            continue
        if current:
            current["reference"] = f"{current['reference']} {line.text.strip()}".strip()
    if current:
        references.append(current)

    references = split_inline_footnote_references(references)
    reference_map = {item["marker"]: item["reference"] for item in references}
    return references, reference_map


def footnote_reference_start_match(line: str) -> re.Match[str] | None:
    """Match a numbered biblical reference line, excluding wrapped verse continuations."""
    match = FOOTNOTE_REFERENCE_RE.match(line.strip())
    if not match:
        return None
    reference_text = match.group(2).strip()
    if not BIBLE_REFERENCE_START_RE.match(reference_text):
        return None
    return match


def inline_footnote_reference_start_match(line: str) -> re.Match[str] | None:
    """Find a numbered biblical reference that was joined to the previous line."""
    for match in INLINE_FOOTNOTE_REFERENCE_START_RE.finditer(line):
        if match.start() > 0:
            return match
    return None


def split_inline_footnote_references(references: list[dict[str, str]]) -> list[dict[str, str]]:
    """Split compacted reference lines such as `5. ... 6. 1Pd ...`."""
    expanded: list[dict[str, str]] = []
    for reference in references:
        text = reference["reference"]
        matches = list(INLINE_FOOTNOTE_REFERENCE_START_RE.finditer(text))
        if not matches:
            expanded.append(reference)
            continue

        first_reference = text[: matches[0].start()].strip()
        if first_reference:
            expanded.append({"marker": reference["marker"], "reference": first_reference})
        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            expanded.append({"marker": match.group(1), "reference": text[match.end() : end].strip()})
    return expanded


def unique_in_order(values: list[str]) -> list[str]:
    """Return unique values while preserving first-seen order."""
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def link_confession_references(
    footnote_markers: list[str],
    references: list[dict[str, str]],
) -> tuple[dict[str, str], list[dict[str, Any]], list[str], dict[str, str]]:
    """Link body footnote markers to the reference block, preserving source numbering."""
    markers = unique_in_order(footnote_markers)
    source_reference_map = {item["marker"]: item["reference"] for item in references}
    links: list[dict[str, Any]] = []
    warnings: list[str] = []

    if not markers:
        return {}, links, warnings, source_reference_map

    if set(markers) == set(source_reference_map):
        linked_map = {marker: source_reference_map[marker] for marker in markers}
        links = [
            {
                "marker": marker,
                "source_marker": marker,
                "reference": source_reference_map[marker],
                "link_status": "exact",
            }
            for marker in markers
        ]
        return linked_map, links, warnings, source_reference_map

    if len(markers) == len(references):
        linked_map: dict[str, str] = {}
        for marker, reference in zip(markers, references):
            source_marker = reference["marker"]
            linked_map[marker] = reference["reference"]
            links.append(
                {
                    "marker": marker,
                    "source_marker": source_marker,
                    "reference": reference["reference"],
                    "link_status": (
                        "exact" if marker == source_marker else "position_inferred_number_mismatch"
                    ),
                }
            )
        if any(link["link_status"] != "exact" for link in links):
            warnings.append(
                "confession_reference_numbering_mismatch:"
                f"footnote_markers={','.join(markers)};"
                f"source_markers={','.join(item['marker'] for item in references)}"
            )
        return linked_map, links, warnings, source_reference_map

    linked_map = {}
    missing_markers: list[str] = []
    for marker in markers:
        reference = source_reference_map.get(marker)
        if reference:
            linked_map[marker] = reference
            links.append(
                {
                    "marker": marker,
                    "source_marker": marker,
                    "reference": reference,
                    "link_status": "exact",
                }
            )
        else:
            missing_markers.append(marker)
            links.append(
                {
                    "marker": marker,
                    "source_marker": None,
                    "reference": None,
                    "link_status": "missing_source_reference",
                }
            )

    unused_source_markers = [marker for marker in source_reference_map if marker not in markers]
    if missing_markers or unused_source_markers:
        warnings.append(
            "confession_reference_marker_mismatch:"
            f"markers_without_reference={','.join(missing_markers) or 'none'};"
            f"unused_source_markers={','.join(unused_source_markers) or 'none'}"
        )
    return linked_map, links, warnings, source_reference_map


def split_confession_body_and_references(segment: list[TextLine]) -> tuple[list[TextLine], list[TextLine]]:
    """Split a confession paragraph into doctrinal body and numbered references."""
    reference_start: int | None = None
    for index, line in enumerate(segment):
        if footnote_reference_start_match(line.text):
            reference_start = index
            break
        inline_reference = inline_footnote_reference_start_match(line.text)
        if inline_reference:
            body_text = line.text[: inline_reference.start()].strip()
            reference_text = line.text[inline_reference.start() :].strip()
            body_lines = segment[:index]
            if body_text:
                body_lines.append(TextLine(page=line.page, index=line.index, text=body_text))
            reference_lines = [TextLine(page=line.page, index=line.index, text=reference_text), *segment[index + 1 :]]
            return body_lines, reference_lines
    if reference_start is None:
        return segment, []
    return segment[:reference_start], segment[reference_start:]


def split_canon_books_table(body_lines: list[TextLine]) -> tuple[list[TextLine], list[TextLine]]:
    """Separate the canon books table from a confession paragraph body."""
    table_start: int | None = None
    table_end: int | None = None
    for index, line in enumerate(body_lines):
        if normalize_for_search(line.text) == "antigo testamento":
            table_start = index
            break
    if table_start is None:
        return body_lines, []

    for index in range(table_start + 1, len(body_lines)):
        if normalize_for_search(body_lines[index].text).startswith("todos esses livros"):
            table_end = index
            break
    if table_end is None:
        table_end = len(body_lines)

    paragraph_lines = body_lines[:table_start] + body_lines[table_end:]
    table_lines = body_lines[table_start:table_end]
    return paragraph_lines, table_lines


def build_confession_paragraph_text(
    paragraph_lines: list[TextLine],
    references: list[dict[str, str]],
) -> str:
    """Build text for a confession paragraph with its reference block."""
    text = join_structural_text(paragraph_lines)
    if references:
        reference_text = "\n".join(f"{item['marker']}. {item['reference']}" for item in references)
        text = f"{text}\n\nReferências bíblicas:\n{reference_text}"
    return text.strip()


def chunk_confession_of_faith(
    document: dict[str, Any],
    normalized_document: dict[str, Any],
    topic_map: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Chunk the Congregational Confession of Faith."""
    lines = get_parsing_lines(normalized_document)
    chunks: list[dict[str, Any]] = []
    chapters: list[dict[str, Any]] = []
    roman_paragraphs: list[str] = []
    numbered_points: list[str] = []
    canon_table_count = 0
    unhandled_headings: list[dict[str, Any]] = []
    context: dict[str, Any] = {
        "chapter_number": None,
        "chapter_title": None,
        "section_number": None,
        "section_title": None,
        "subsection_title": None,
    }

    index = 0
    while index < len(lines):
        line = lines[index].text.strip()
        chapter_match = CHAPTER_RE.match(line)
        if chapter_match:
            chapter_number = chapter_match.group(1).upper()
            chapter_title, last_consumed = collect_heading_after_marker(
                lines, index, chapter_match.group(2), normalized_document["document_id"]
            )
            context.update(
                {
                    "chapter_number": chapter_number,
                    "chapter_title": chapter_title,
                    "section_number": None,
                    "section_title": None,
                    "subsection_title": None,
                }
            )
            chapters.append({"chapter_number": chapter_number, "chapter_title": chapter_title, "page": lines[index].page})
            index = last_consumed + 1
            continue

        if is_confession_final_section_line(line):
            section_title = line
            index += 1
            while index < len(lines):
                point_match = CONFESSION_NUMBERED_POINT_RE.match(lines[index].text.strip())
                if not point_match:
                    index += 1
                    continue
                point_number = point_match.group(1)
                end = index + 1
                while end < len(lines):
                    if CONFESSION_NUMBERED_POINT_RE.match(lines[end].text.strip()):
                        break
                    end += 1
                point_lines = lines[index:end]
                point_text = join_structural_text(point_lines)
                point_context = {
                    "chapter_number": None,
                    "chapter_title": None,
                    "section_title": section_title,
                    "subsection_title": None,
                    "numbered_point": point_number,
                }
                chunks.append(
                    build_chunk(
                        document=document,
                        normalized_document=normalized_document,
                        chunk_id=f"{document['document_id']}_instituicao-igrejas_ponto-{int(point_number):02d}",
                        text=point_text,
                        page_start=point_lines[0].page,
                        page_end=point_lines[-1].page,
                        context=point_context,
                        document_structure_type="numbered_doctrinal_point",
                        topic_map=topic_map,
                        extra_metadata={"numbered_point": point_number},
                    )
                )
                numbered_points.append(point_number)
                index = end
            break

        paragraph_match = CONFESSION_ROMAN_PARAGRAPH_RE.match(line)
        if paragraph_match and context.get("chapter_number"):
            roman = paragraph_match.group(1).upper()
            end = index + 1
            while end < len(lines):
                candidate = lines[end].text.strip()
                if (
                    CHAPTER_RE.match(candidate)
                    or is_confession_final_section_line(candidate)
                    or CONFESSION_ROMAN_PARAGRAPH_RE.match(candidate)
                ):
                    break
                end += 1

            segment = lines[index:end]
            body_lines, reference_lines = split_confession_body_and_references(segment)
            paragraph_body_lines, table_lines = split_canon_books_table(body_lines)
            references, source_reference_map = parse_footnote_reference_lines(reference_lines)
            footnote_markers = re.findall(r"\(([0-9]{1,3})\)", " ".join(line.text for line in paragraph_body_lines))
            reference_map, reference_links, reference_warnings, source_reference_map = link_confession_references(
                footnote_markers,
                references,
            )
            paragraph_context = {
                **context,
                "paragraph_number_roman": roman,
            }
            paragraph_text = build_confession_paragraph_text(paragraph_body_lines, references)
            chunks.append(
                build_chunk(
                    document=document,
                    normalized_document=normalized_document,
                    chunk_id=(
                        f"{document['document_id']}_capitulo-{slugify(str(context['chapter_number']))}"
                        f"_paragrafo-{slugify(roman)}"
                    ),
                    text=paragraph_text,
                    page_start=segment[0].page,
                    page_end=segment[-1].page,
                    context=paragraph_context,
                    document_structure_type="confession_paragraph",
                    topic_map=topic_map,
                    paragraph_label=f"parágrafo {roman}",
                    paragraph_number_roman=roman,
                    footnote_markers=footnote_markers,
                    biblical_references=[f"{item['marker']}. {item['reference']}" for item in references],
                    extra_metadata={
                        "biblical_reference_map": reference_map,
                        "biblical_reference_source_map": source_reference_map,
                        "biblical_reference_links": reference_links,
                    },
                    warnings=reference_warnings,
                )
            )
            roman_paragraphs.append(f"{context['chapter_number']}.{roman}")

            if table_lines:
                canon_table_count += 1
                table_context = {**context, "paragraph_number_roman": roman}
                table_text = join_structural_text(table_lines)
                chunks.append(
                    build_chunk(
                        document=document,
                        normalized_document=normalized_document,
                        chunk_id=(
                            f"{document['document_id']}_capitulo-{slugify(str(context['chapter_number']))}"
                            "_livros-canonicos"
                        ),
                        text=table_text,
                        page_start=table_lines[0].page,
                        page_end=table_lines[-1].page,
                        context=table_context,
                        document_structure_type="canon_books_table",
                        topic_map=topic_map,
                        paragraph_label=f"parágrafo {roman}",
                        paragraph_number_roman=roman,
                        footnote_markers=[],
                        biblical_references=[],
                    )
                )
            index = end
            continue

        if is_upper_heading(line) and not is_document_cover_line(line):
            unhandled_headings.append({"page": lines[index].page, "text": line})
        index += 1

    chunks = ensure_unique_chunk_ids(chunks)
    return chunks, {
        "preamble_count": 0,
        "article_count": 0,
        "article_numbers": [],
        "chapter_count": len(chapters),
        "chapter_numbers": [chapter["chapter_number"] for chapter in chapters],
        "section_count": 1 if numbered_points else 0,
        "unhandled_headings": unhandled_headings,
        "line_count": len(lines),
        "confession_paragraph_count": len(roman_paragraphs),
        "confession_paragraphs": roman_paragraphs,
        "canon_books_table_count": canon_table_count,
        "numbered_doctrinal_point_count": len(numbered_points),
        "numbered_doctrinal_points": numbered_points,
    }


def is_resolution_signature_line(line: str) -> bool:
    """Detect the start of the resolution signature block."""
    return normalize_for_search(line).startswith("recife/pe")


def resolution_next_article_boundary(lines: list[TextLine], start_index: int) -> int:
    """Find the end of a resolution article segment."""
    for index in range(start_index, len(lines)):
        text = lines[index].text.strip()
        if ARTICLE_RE.match(text) or CHAPTER_RE.match(text) or is_resolution_signature_line(text):
            return index
    return len(lines)


def resolution_article_to_chunks(
    article: dict[str, Any],
    document: dict[str, Any],
    normalized_document: dict[str, Any],
    topic_map: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build chunks for a resolution article, splitting long articles by children."""
    text = join_structural_text(article["lines"])
    base_id = f"artigo-{int(article['article_number']):03d}"
    if len(text) <= MAX_CHUNK_CHARS:
        return [
            build_chunk(
                document=document,
                normalized_document=normalized_document,
                chunk_id=f"{document['document_id']}_{base_id}",
                text=text,
                page_start=article["page_start"],
                page_end=article["page_end"],
                context=article["context"],
                document_structure_type="resolution_article",
                topic_map=topic_map,
                article_number=article["article_number"],
                article_display=article["article_display"],
            )
        ]

    chunks: list[dict[str, Any]] = []
    for unit in split_article_units(article):
        unit_lines = unit["prefix_lines"] + unit["lines"]
        unit_text = join_structural_text(unit_lines)
        structure_type = "resolution_paragraph" if unit["document_structure_type"] == "paragraph" else "resolution_inciso"
        parts = [base_id]
        if unit.get("paragraph_number"):
            parts.append(f"paragrafo-{unit['paragraph_number']}")
        if unit.get("inciso"):
            parts.append(f"inciso-{unit['inciso']}")
        chunk_id = f"{document['document_id']}_{'_'.join(slugify(part) for part in parts)}"
        chunks.append(
            build_chunk(
                document=document,
                normalized_document=normalized_document,
                chunk_id=chunk_id,
                text=unit_text,
                page_start=unit["lines"][0].page,
                page_end=unit["lines"][-1].page,
                context=article["context"],
                document_structure_type=structure_type,
                topic_map=topic_map,
                article_number=article["article_number"],
                article_display=article["article_display"],
                paragraph_number=unit.get("paragraph_number"),
                inciso=unit.get("inciso"),
                item_label=unit.get("item_label"),
                warnings=["article_split_by_structural_children"],
            )
        )
    return chunks


def chunk_resolution(
    document: dict[str, Any],
    normalized_document: dict[str, Any],
    topic_map: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Chunk an administrative resolution."""
    lines = get_parsing_lines(normalized_document)
    chunks: list[dict[str, Any]] = []
    chapters: list[dict[str, Any]] = []
    articles: list[str] = []
    considerandos: list[str] = []
    unhandled_headings: list[dict[str, Any]] = []
    context: dict[str, Any] = {
        "chapter_number": None,
        "chapter_title": None,
        "section_number": None,
        "section_title": None,
        "subsection_title": None,
    }

    title_index = next((i for i, line in enumerate(lines) if "RESOLUÇÃO ALIANÇA" in line.text.upper()), None)
    if title_index is not None:
        chunks.append(
            build_chunk(
                document=document,
                normalized_document=normalized_document,
                chunk_id=f"{document['document_id']}_cabecalho",
                text=lines[title_index].text,
                page_start=lines[title_index].page,
                page_end=lines[title_index].page,
                context=context,
                document_structure_type="resolution_heading",
                topic_map=topic_map,
            )
        )

    intro_start = next((i for i, line in enumerate(lines) if line.text.startswith("A ALIANÇA")), None)
    first_considerando = next((i for i, line in enumerate(lines) if line.text.startswith("CONSIDERANDO")), None)
    resolve_index = next((i for i, line in enumerate(lines) if normalize_for_search(line.text) == "resolve:"), None)

    if title_index is not None and intro_start is not None and intro_start > title_index + 1:
        ementa_lines = lines[title_index + 1 : intro_start]
        chunks.append(
            build_chunk(
                document=document,
                normalized_document=normalized_document,
                chunk_id=f"{document['document_id']}_ementa",
                text=join_structural_text(ementa_lines),
                page_start=ementa_lines[0].page,
                page_end=ementa_lines[-1].page,
                context=context,
                document_structure_type="resolution_ementa",
                topic_map=topic_map,
            )
        )

    if intro_start is not None and first_considerando is not None and first_considerando > intro_start:
        intro_lines = lines[intro_start:first_considerando]
        chunks.append(
            build_chunk(
                document=document,
                normalized_document=normalized_document,
                chunk_id=f"{document['document_id']}_texto-introdutorio",
                text=join_structural_text(intro_lines),
                page_start=intro_lines[0].page,
                page_end=intro_lines[-1].page,
                context=context,
                document_structure_type="resolution_intro",
                topic_map=topic_map,
            )
        )

    if first_considerando is not None and resolve_index is not None:
        index = first_considerando
        considerando_number = 1
        while index < resolve_index:
            end = index + 1
            while end < resolve_index and not lines[end].text.startswith("CONSIDERANDO"):
                end += 1
            considerando_lines = lines[index:end]
            considerando_context = {**context, "considerando_number": str(considerando_number)}
            chunks.append(
                build_chunk(
                    document=document,
                    normalized_document=normalized_document,
                    chunk_id=f"{document['document_id']}_considerando-{considerando_number:02d}",
                    text=join_structural_text(considerando_lines),
                    page_start=considerando_lines[0].page,
                    page_end=considerando_lines[-1].page,
                    context=considerando_context,
                    document_structure_type="resolution_considerando",
                    topic_map=topic_map,
                )
            )
            considerandos.append(str(considerando_number))
            considerando_number += 1
            index = end

    index = (resolve_index + 1) if resolve_index is not None else 0
    while index < len(lines):
        line = lines[index].text.strip()
        if is_resolution_signature_line(line):
            signature_lines = lines[index:]
            chunks.append(
                build_chunk(
                    document=document,
                    normalized_document=normalized_document,
                    chunk_id=f"{document['document_id']}_assinatura",
                    text=join_structural_text(signature_lines),
                    page_start=signature_lines[0].page,
                    page_end=signature_lines[-1].page,
                    context=context,
                    document_structure_type="signature",
                    topic_map=topic_map,
                )
            )
            break

        chapter_match = CHAPTER_RE.match(line)
        if chapter_match:
            chapter_number = chapter_match.group(1).upper()
            chapter_title, last_consumed = collect_heading_after_marker(
                lines, index, chapter_match.group(2), normalized_document["document_id"]
            )
            context.update(
                {
                    "chapter_number": chapter_number,
                    "chapter_title": chapter_title,
                    "section_number": None,
                    "section_title": None,
                    "subsection_title": None,
                }
            )
            chapters.append({"chapter_number": chapter_number, "chapter_title": chapter_title, "page": lines[index].page})
            index = last_consumed + 1
            continue

        article_match = ARTICLE_RE.match(line)
        if article_match:
            end = resolution_next_article_boundary(lines, index + 1)
            heading = parse_article_heading(line)
            article = {
                "lines": lines[index:end],
                "context": context.copy(),
                "page_start": lines[index].page,
                "page_end": lines[end - 1].page if end > index else lines[index].page,
                **heading,
            }
            chunks.extend(resolution_article_to_chunks(article, document, normalized_document, topic_map))
            articles.append(article["article_number"])
            index = end
            continue

        if is_upper_heading(line) and not is_document_cover_line(line):
            unhandled_headings.append({"page": lines[index].page, "text": line})
        index += 1

    chunks = ensure_unique_chunk_ids(chunks)
    return chunks, {
        "preamble_count": 0,
        "article_count": len(articles),
        "article_numbers": articles,
        "chapter_count": len(chapters),
        "chapter_numbers": [chapter["chapter_number"] for chapter in chapters],
        "section_count": 0,
        "unhandled_headings": unhandled_headings,
        "line_count": len(lines),
        "resolution_considerando_count": len(considerandos),
        "resolution_considerandos": considerandos,
    }


def ensure_unique_chunk_ids(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Make chunk IDs unique without changing existing IDs unless needed."""
    counts: Counter[str] = Counter()
    for chunk in chunks:
        base_id = chunk["chunk_id"]
        counts[base_id] += 1
        if counts[base_id] > 1:
            chunk["chunk_id"] = f"{base_id}_duplicata-{counts[base_id]:02d}"
            chunk["embedding_text"] = build_embedding_text(chunk)
            chunk["warnings"].append("duplicate_chunk_id_disambiguated")
    return chunks


def chunk_normalized_document(
    document: dict[str, Any],
    normalized_document: dict[str, Any],
    topic_map: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Create chunks for one normalized normative document."""
    if document["document_type"] == "confession_of_faith":
        return chunk_confession_of_faith(document, normalized_document, topic_map)
    if document["document_type"] == "administrative_resolution":
        return chunk_resolution(document, normalized_document, topic_map)

    segments = parse_document_segments(normalized_document)
    chunks: list[dict[str, Any]] = []

    for preamble_index, preamble in enumerate(segments["preambles"], start=1):
        text = join_structural_text(preamble["lines"])
        if not text.strip():
            continue
        chunks.append(
            build_chunk(
                document=document,
                normalized_document=normalized_document,
                chunk_id=f"{document['document_id']}_preambulo-{preamble_index:02d}",
                text=text,
                page_start=preamble["lines"][0].page,
                page_end=preamble["lines"][-1].page,
                context=preamble["context"],
                document_structure_type="preamble",
                topic_map=topic_map,
            )
        )

    for article in segments["articles"]:
        chunks.extend(article_to_chunks(article, document, normalized_document, topic_map))

    chunks = ensure_unique_chunk_ids(chunks)
    structural_summary = {
        "preamble_count": len(segments["preambles"]),
        "article_count": len(segments["articles"]),
        "article_numbers": [article["article_number"] for article in segments["articles"]],
        "chapter_count": len(segments["chapters"]),
        "section_count": len(segments["sections"]),
        "unhandled_headings": segments["unhandled_headings"],
        "line_count": segments["line_count"],
    }
    return chunks, structural_summary


def validate_chunk(chunk: dict[str, Any]) -> list[str]:
    """Validate one normative chunk."""
    issues: list[str] = []
    missing = REQUIRED_NORMATIVE_FIELDS - set(chunk)
    if missing:
        issues.append(f"missing_fields:{sorted(missing)}")
    if not str(chunk.get("text", "")).strip():
        issues.append("empty_text")
    if not str(chunk.get("doc_id", "")).strip():
        issues.append("missing_doc_id")
    if not str(chunk.get("full_reference", "")).strip():
        issues.append("missing_full_reference")
    if not str(chunk.get("source_path", "")).startswith("corpus/raw/normative/"):
        issues.append("source_path_outside_normative_corpus")
    if chunk.get("text_hash") != text_hash(chunk.get("text", "")):
        issues.append("invalid_text_hash")
    if len(chunk.get("text", "")) > MAX_CHUNK_CHARS:
        issues.append("chunk_above_expected_limit")
    return issues


def validate_chunks(chunks: list[dict[str, Any]]) -> list[str]:
    """Validate chunk list and duplicate IDs."""
    issues: list[str] = []
    seen: set[str] = set()
    for index, chunk in enumerate(chunks, start=1):
        chunk_id = chunk.get("chunk_id")
        if chunk_id in seen:
            issues.append(f"line_{index}:duplicate_chunk_id:{chunk_id}")
        seen.add(chunk_id)
        for issue in validate_chunk(chunk):
            issues.append(f"line_{index}:{issue}")
    return issues


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    """Read a JSONL file."""
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                raise ValueError(f"Linha vazia em {relative_path(path)}:{line_number}")
            rows.append(json.loads(line))
    return rows


def summarize_chunking(
    document: dict[str, Any],
    chunks: list[dict[str, Any]],
    jsonl_path: Path,
    validation_issues: list[str],
    structural_summary: dict[str, Any],
) -> dict[str, Any]:
    """Summarize chunking for one document."""
    chunk_types = Counter(chunk["document_structure_type"] for chunk in chunks)
    long_chunks = [
        {"chunk_id": chunk["chunk_id"], "length": len(chunk["text"])}
        for chunk in chunks
        if len(chunk["text"]) > MAX_CHUNK_CHARS
    ]
    warning_chunks = []
    for chunk in chunks:
        reportable_warnings = [
            warning
            for warning in chunk.get("warnings", [])
            if warning.startswith("confession_reference")
        ]
        if reportable_warnings:
            warning_chunks.append({"chunk_id": chunk["chunk_id"], "warnings": reportable_warnings})
    return {
        "document_id": document["document_id"],
        "jsonl_path": relative_path(jsonl_path),
        "chunk_count": len(chunks),
        "chunk_types": dict(sorted(chunk_types.items())),
        "article_count": structural_summary["article_count"],
        "article_numbers": structural_summary["article_numbers"],
        "preamble_count": structural_summary["preamble_count"],
        "chapter_count": structural_summary["chapter_count"],
        "chapter_numbers": structural_summary.get("chapter_numbers", []),
        "section_count": structural_summary["section_count"],
        "confession_paragraph_count": structural_summary.get("confession_paragraph_count", 0),
        "confession_paragraphs": structural_summary.get("confession_paragraphs", []),
        "canon_books_table_count": structural_summary.get("canon_books_table_count", 0),
        "numbered_doctrinal_point_count": structural_summary.get("numbered_doctrinal_point_count", 0),
        "numbered_doctrinal_points": structural_summary.get("numbered_doctrinal_points", []),
        "resolution_considerando_count": structural_summary.get("resolution_considerando_count", 0),
        "resolution_considerandos": structural_summary.get("resolution_considerandos", []),
        "unhandled_headings": structural_summary["unhandled_headings"],
        "chunks_above_expected_limit": long_chunks,
        "warning_chunks": warning_chunks,
        "validation_issues": validation_issues,
    }


def consolidate_all_chunks(output_dir: Path, document_ids: list[str]) -> dict[str, Any]:
    """Consolidate per-document JSONL files."""
    all_chunks: list[dict[str, Any]] = []
    source_files: list[str] = []
    validation_issues: list[str] = []
    per_document_counts: dict[str, int] = {}

    for document_id in document_ids:
        path = output_dir / f"{document_id}.chunks.jsonl"
        rows = read_jsonl(path)
        source_files.append(relative_path(path))
        per_document_counts[document_id] = len(rows)
        validation_issues.extend(f"{document_id}:{issue}" for issue in validate_chunks(rows))
        all_chunks.extend(rows)

    validation_issues.extend(f"all_chunks:{issue}" for issue in validate_chunks(all_chunks))
    all_chunks_path = output_dir / CONSOLIDATED_CHUNKS_FILE
    write_jsonl(all_chunks_path, all_chunks)
    consolidated = read_jsonl(all_chunks_path)
    if len(consolidated) != sum(per_document_counts.values()):
        validation_issues.append("consolidated_count_does_not_match_document_sum")
    return {
        "jsonl_path": relative_path(all_chunks_path),
        "source_files": source_files,
        "chunk_count": len(consolidated),
        "per_document_counts": per_document_counts,
        "validation_issues": validation_issues,
    }


def run_chunking(
    manifest_path: Path = DEFAULT_MANIFEST,
    normalized_dir: Path = DEFAULT_NORMALIZED_DIR,
    output_dir: Path = DEFAULT_CHUNKS_DIR,
    report_dir: Path = DEFAULT_REPORT_DIR,
    topic_map_path: Path = DEFAULT_TOPIC_MAP,
    documents: list[str] | None = None,
) -> dict[str, Any]:
    """Run structural chunking for normative documents."""
    manifest = load_manifest(manifest_path)
    manifest_documents = manifest_documents_by_id(manifest)
    topic_map = load_topic_map(topic_map_path)
    document_ids = documents or sorted(EXPECTED_DOCUMENT_IDS)
    invalid = [document_id for document_id in document_ids if document_id not in EXPECTED_DOCUMENT_IDS]
    if invalid:
        raise ValueError(f"Documentos normativos nao suportados: {invalid}")

    summaries: list[dict[str, Any]] = []
    for document_id in document_ids:
        document = manifest_documents[document_id]
        normalized_path = normalized_dir / f"{document_id}.normalized.json"
        normalized_document = load_json(normalized_path)
        chunks, structural_summary = chunk_normalized_document(document, normalized_document, topic_map)
        jsonl_path = output_dir / f"{document_id}.chunks.jsonl"
        write_jsonl(jsonl_path, chunks)
        persisted_chunks = read_jsonl(jsonl_path)
        issues = validate_chunks(persisted_chunks)
        summaries.append(summarize_chunking(document, persisted_chunks, jsonl_path, issues, structural_summary))

    consolidation = consolidate_all_chunks(output_dir, document_ids)
    report = build_chunking_report(summaries, consolidation, manifest_path, normalized_dir, output_dir)
    write_chunking_report(report, report_dir)
    return report


def build_chunking_report(
    summaries: list[dict[str, Any]],
    consolidation: dict[str, Any],
    manifest_path: Path,
    normalized_dir: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """Build chunking report."""
    status = "PASS"
    if any(summary["validation_issues"] for summary in summaries) or consolidation["validation_issues"]:
        status = "FAIL"
    elif any(
        summary["chunks_above_expected_limit"] or summary["unhandled_headings"] or summary["warning_chunks"]
        for summary in summaries
    ):
        status = "PARTIAL"
    return {
        "status": status,
        "schema_version": SCHEMA_VERSION,
        "manifest_path": relative_path(manifest_path),
        "normalized_dir": relative_path(normalized_dir),
        "output_dir": relative_path(output_dir),
        "max_chunk_chars": MAX_CHUNK_CHARS,
        "documents_processed": [summary["document_id"] for summary in summaries],
        "summaries": summaries,
        "consolidation": consolidation,
    }


def write_chunking_report(report: dict[str, Any], report_dir: Path) -> tuple[Path, Path]:
    """Write chunking report files."""
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / "normative-chunking-report.json"
    md_path = report_dir / "normative-chunking-report.md"
    write_json(json_path, report)
    lines = [
        "# Relatório de chunking do corpus normativo congregacional",
        "",
        "## Status",
        "",
        report["status"],
        "",
        "## Resumo por documento",
        "",
    ]
    for summary in report["summaries"]:
        lines.extend(
            [
                f"### `{summary['document_id']}`",
                "",
                f"- Chunks gerados: {summary['chunk_count']}",
                f"- Artigos detectados: {summary['article_count']}",
                f"- Preâmbulos detectados: {summary['preamble_count']}",
                f"- Capítulos detectados: {summary['chapter_count']}",
                f"- Seções/subseções detectadas: {summary['section_count']}",
                f"- Tipos estruturais: {summary['chunk_types']}",
                f"- Chunks acima do limite: {summary['chunks_above_expected_limit'] or 'nenhuma ocorrência'}",
                f"- Chunks com alertas: {summary['warning_chunks'] or 'nenhuma ocorrência'}",
                f"- Cabeçalhos não consumidos: {summary['unhandled_headings'] or 'nenhuma ocorrência'}",
                f"- Problemas de validação: {summary['validation_issues'] or 'nenhuma ocorrência'}",
                f"- JSONL: `{summary['jsonl_path']}`",
                "",
            ]
        )
    consolidation = report["consolidation"]
    lines.extend(
        [
            "## Consolidação",
            "",
            f"- Arquivo consolidado: `{consolidation['jsonl_path']}`",
            f"- Total de chunks: {consolidation['chunk_count']}",
            f"- Chunks por documento: {consolidation['per_document_counts']}",
            f"- Problemas de validação: {consolidation['validation_issues'] or 'nenhuma ocorrência'}",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


def detect_article_numbers_from_normalized(normalized_document: dict[str, Any]) -> list[str]:
    """Detect article numbers at line starts in normalized text."""
    numbers: list[str] = []
    for line in get_parsing_lines(normalized_document):
        match = ARTICLE_RE.match(line.text)
        if match:
            numbers.append(match.group(1))
    return numbers


def audit_document(
    document: dict[str, Any],
    extracted_dir: Path,
    normalized_dir: Path,
    chunks_dir: Path,
    taxonomy: dict[str, Any],
) -> dict[str, Any]:
    """Audit one normative document."""
    extracted = load_json(extracted_dir / f"{document['document_id']}.extracted.json")
    normalized = load_json(normalized_dir / f"{document['document_id']}.normalized.json")
    chunks = read_jsonl(chunks_dir / f"{document['document_id']}.chunks.jsonl")

    detected_articles = detect_article_numbers_from_normalized(normalized)
    duplicate_article_numbers = sorted(
        [number for number, count in Counter(detected_articles).items() if count > 1],
        key=int,
    )
    unique_detected_articles = sorted(set(detected_articles), key=int)
    chunked_articles = sorted({str(chunk.get("article_number")) for chunk in chunks if chunk.get("article_number")}, key=int)
    missing_article_chunks = [
        article_number
        for article_number in unique_detected_articles
        if article_number not in set(chunked_articles)
    ]
    pages_without_text = [page["page_number"] for page in extracted["pages"] if page["is_empty"]]
    chunk_issues = validate_chunks(chunks)
    taxonomy_topics = set(taxonomy.get("topics", {}))
    invalid_topics = [
        {"chunk_id": chunk["chunk_id"], "topic": chunk.get("topic"), "subtopic": chunk.get("subtopic")}
        for chunk in chunks
        if chunk.get("topic") not in taxonomy_topics
        or chunk.get("subtopic") not in taxonomy.get("topics", {}).get(chunk.get("topic"), [])
    ]
    chunks_above_limit = [
        {"chunk_id": chunk["chunk_id"], "length": len(chunk["text"])}
        for chunk in chunks
        if len(chunk["text"]) > MAX_CHUNK_CHARS
    ]
    chunk_warnings = []
    for chunk in chunks:
        reportable_warnings = [
            warning
            for warning in chunk.get("warnings", [])
            if warning.startswith("confession_reference")
        ]
        if reportable_warnings:
            chunk_warnings.append({"chunk_id": chunk["chunk_id"], "warnings": reportable_warnings})
    chunk_types = Counter(chunk.get("document_structure_type") for chunk in chunks)
    chapter_numbers = sorted(
        {str(chunk.get("chapter_number")) for chunk in chunks if chunk.get("chapter_number")},
        key=lambda value: roman_sort_key(value),
    )
    confession_paragraphs = [
        f"{chunk.get('chapter_number')}.{chunk.get('paragraph_number_roman')}"
        for chunk in chunks
        if chunk.get("document_structure_type") == "confession_paragraph"
    ]
    numbered_points = sorted(
        {
            str(chunk.get("numbered_point"))
            for chunk in chunks
            if chunk.get("document_structure_type") == "numbered_doctrinal_point" and chunk.get("numbered_point")
        },
        key=int,
    )
    missing_numbered_points: list[str] = []
    if document["document_id"] == "confissao-fe-congregacional-alianca":
        expected_points = {str(number) for number in range(1, 28)}
        missing_numbered_points = sorted(expected_points - set(numbered_points), key=int)

    confession_reference_issues = [
        chunk["chunk_id"]
        for chunk in chunks
        if chunk.get("document_structure_type") == "confession_paragraph"
        and set(chunk.get("footnote_markers", [])) != set((chunk.get("biblical_reference_map") or {}).keys())
    ]
    resolution_considerandos = [
        chunk["chunk_id"]
        for chunk in chunks
        if chunk.get("document_structure_type") == "resolution_considerando"
    ]

    status = "PASS"
    document_specific_blocking = []
    if document["document_id"] == "confissao-fe-congregacional-alianca":
        if len(chapter_numbers) != 34:
            document_specific_blocking.append("confession_chapter_count_mismatch")
        if not confession_paragraphs:
            document_specific_blocking.append("confession_paragraphs_not_detected")
        if chunk_types.get("canon_books_table", 0) != 1:
            document_specific_blocking.append("canon_books_table_not_detected")
        if missing_numbered_points:
            document_specific_blocking.append("missing_numbered_doctrinal_points")
        if confession_reference_issues:
            document_specific_blocking.append("confession_reference_marker_mismatch")
    if document["document_id"] == "resolucao-alianca-01-2020":
        if unique_detected_articles != ["1", "2", "3", "4"]:
            document_specific_blocking.append("resolution_article_numbers_mismatch")
        if len(resolution_considerandos) != 3:
            document_specific_blocking.append("resolution_considerandos_mismatch")

    blocking = (
        missing_article_chunks
        or duplicate_article_numbers
        or chunk_issues
        or invalid_topics
        or document_specific_blocking
    )
    warnings = chunks_above_limit or pages_without_text or normalized.get("document_warnings") or chunk_warnings
    if blocking:
        status = "FAIL"
    elif warnings:
        status = "PARTIAL"

    return {
        "document_id": document["document_id"],
        "title": document["title"],
        "pages_extracted": extracted["pages_count"],
        "pages_without_text": pages_without_text,
        "chunks_count": len(chunks),
        "chunk_types": dict(sorted(chunk_types.items())),
        "chapter_numbers_detected": chapter_numbers,
        "articles_detected": len(unique_detected_articles),
        "article_numbers_detected": unique_detected_articles,
        "duplicate_article_numbers_detected": duplicate_article_numbers,
        "article_numbers_chunked": chunked_articles,
        "missing_article_chunks": missing_article_chunks,
        "chunks_above_expected_limit": chunks_above_limit,
        "chunk_warnings": chunk_warnings,
        "empty_chunks": [chunk["chunk_id"] for chunk in chunks if not chunk.get("text", "").strip()],
        "chunks_missing_doc_id": [chunk["chunk_id"] for chunk in chunks if not chunk.get("doc_id")],
        "chunks_missing_full_reference": [chunk["chunk_id"] for chunk in chunks if not chunk.get("full_reference")],
        "invalid_topic_assignments": invalid_topics,
        "confession_paragraphs_detected": len(confession_paragraphs),
        "canon_books_table_count": chunk_types.get("canon_books_table", 0),
        "numbered_doctrinal_points_detected": numbered_points,
        "missing_numbered_doctrinal_points": missing_numbered_points,
        "confession_reference_issues": confession_reference_issues,
        "resolution_considerandos_detected": len(resolution_considerandos),
        "document_specific_issues": document_specific_blocking,
        "normalization_alerts": normalized.get("document_warnings", []),
        "marker_validation": normalized.get("marker_validation", {}),
        "chunk_validation_issues": chunk_issues,
        "status": status,
    }


def run_audit(
    manifest_path: Path = DEFAULT_MANIFEST,
    extracted_dir: Path = DEFAULT_EXTRACTED_DIR,
    normalized_dir: Path = DEFAULT_NORMALIZED_DIR,
    chunks_dir: Path = DEFAULT_CHUNKS_DIR,
    report_dir: Path = DEFAULT_REPORT_DIR,
    taxonomy_path: Path = DEFAULT_TAXONOMY,
) -> dict[str, Any]:
    """Run the normative audit."""
    manifest = load_manifest(manifest_path)
    documents = manifest_documents_by_id(manifest)
    taxonomy = load_json(taxonomy_path)
    summaries = [
        audit_document(documents[document_id], extracted_dir, normalized_dir, chunks_dir, taxonomy)
        for document_id in sorted(EXPECTED_DOCUMENT_IDS)
    ]
    status = "PASS"
    if any(summary["status"] == "FAIL" for summary in summaries):
        status = "FAIL"
    elif any(summary["status"] == "PARTIAL" for summary in summaries):
        status = "PARTIAL"
    report = {
        "status": status,
        "corpus_id": manifest["corpus_id"],
        "manifest_path": relative_path(manifest_path),
        "extracted_dir": relative_path(extracted_dir),
        "normalized_dir": relative_path(normalized_dir),
        "chunks_dir": relative_path(chunks_dir),
        "max_chunk_chars": MAX_CHUNK_CHARS,
        "documents": summaries,
    }
    write_audit_report(report, report_dir)
    return report


def write_audit_report(report: dict[str, Any], report_dir: Path) -> tuple[Path, Path]:
    """Write normative audit report files."""
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / "normative-audit-report.json"
    md_path = report_dir / "normative-audit-report.md"
    write_json(json_path, report)

    lines = [
        "# Auditoria do corpus normativo congregacional",
        "",
        "## Status",
        "",
        report["status"],
        "",
        "## Documentos auditados",
        "",
    ]
    for document in report["documents"]:
        lines.extend(
            [
                f"### {document['title']}",
                "",
                f"- `document_id`: `{document['document_id']}`",
                f"- Total de páginas extraídas: {document['pages_extracted']}",
                f"- Total de chunks: {document['chunks_count']}",
                f"- Tipos de chunk: {document['chunk_types']}",
                f"- Capítulos detectados: {document['chapter_numbers_detected'] or 'nenhuma ocorrência'}",
                f"- Total de artigos detectados: {document['articles_detected']}",
                f"- Artigos sem chunk: {document['missing_article_chunks'] or 'nenhuma ocorrência'}",
                f"- Artigos duplicados detectados: {document['duplicate_article_numbers_detected'] or 'nenhuma ocorrência'}",
                f"- Parágrafos confessionais detectados: {document['confession_paragraphs_detected']}",
                f"- Tabelas/listas canônicas detectadas: {document['canon_books_table_count']}",
                (
                    "- Pontos doutrinários numerados detectados: "
                    f"{document['numbered_doctrinal_points_detected'] or 'nenhuma ocorrência'}"
                ),
                (
                    "- Pontos doutrinários numerados ausentes: "
                    f"{document['missing_numbered_doctrinal_points'] or 'nenhuma ocorrência'}"
                ),
                f"- Considerandos detectados: {document['resolution_considerandos_detected']}",
                f"- Chunks acima do limite esperado: {document['chunks_above_expected_limit'] or 'nenhuma ocorrência'}",
                f"- Alertas de chunks: {document['chunk_warnings'] or 'nenhuma ocorrência'}",
                f"- Páginas sem texto: {document['pages_without_text'] or 'nenhuma ocorrência'}",
                f"- Alertas de normalização: {document['normalization_alerts'] or 'nenhuma ocorrência'}",
                f"- Chunks vazios: {document['empty_chunks'] or 'nenhuma ocorrência'}",
                f"- Chunks sem `doc_id`: {document['chunks_missing_doc_id'] or 'nenhuma ocorrência'}",
                f"- Chunks sem `full_reference`: {document['chunks_missing_full_reference'] or 'nenhuma ocorrência'}",
                f"- Problemas específicos do documento: {document['document_specific_issues'] or 'nenhuma ocorrência'}",
                f"- Problemas de vínculo referências/marcadores: {document['confession_reference_issues'] or 'nenhuma ocorrência'}",
                f"- Problemas de validação: {document['chunk_validation_issues'] or 'nenhuma ocorrência'}",
                f"- Status: {document['status']}",
                "",
            ]
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path
