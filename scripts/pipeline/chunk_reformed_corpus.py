"""Gera chunks estruturais do corpus reformado.

A SPEC-003A criou a base comum do chunking e processou Cânones de Dort e
Catecismo de Heidelberg. A SPEC-003B completa o corpus reformado com
Westminster, Londres 1689 e a consolidação em `all_chunks.jsonl`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT_DIR / "corpus" / "raw" / "reformed_manifest.json"
DEFAULT_NORMALIZED_DIR = ROOT_DIR / "corpus" / "processed" / "normalized" / "reformed"
DEFAULT_STRUCTURE_DIR = ROOT_DIR / "corpus" / "reports" / "structure_analysis"
DEFAULT_OUTPUT_DIR = ROOT_DIR / "corpus" / "processed" / "chunks" / "reformed"
DEFAULT_REPORT_DIR = ROOT_DIR / "corpus" / "reports" / "chunking"
SPEC_003A_DOCUMENTS = {"canones-de-dort", "catecismo-heidelberg"}
SPEC_003B_DOCUMENTS = {"confissao-fe-westminster", "confissao-batista-londres-1689"}
ALL_DOCUMENTS = SPEC_003A_DOCUMENTS | SPEC_003B_DOCUMENTS
CONSOLIDATED_CHUNKS_FILE = "all_chunks.jsonl"
SCHEMA_VERSION = "reformed-structural-chunk-v1"
RETRIEVAL_NAMESPACE = "reformed_confessional"
REQUIRED_CHUNK_FIELDS = {
    "chunk_id",
    "schema_version",
    "corpus_id",
    "retrieval_namespace",
    "document_id",
    "document",
    "document_type",
    "tradition_family",
    "tradition_branch",
    "language",
    "chunk_type",
    "content_role",
    "is_doctrinal",
    "section_title",
    "section_reference",
    "chapter_title",
    "chapter_reference",
    "page_start",
    "page_end",
    "text",
    "embedding_text",
    "source_path",
    "normalized_source",
    "text_hash",
    "warnings",
}


def relative_path(path: Path) -> str:
    """Retorna caminho relativo ao repositorio em formato POSIX."""
    return path.relative_to(ROOT_DIR).as_posix()


def load_json(path: Path) -> dict[str, Any]:
    """Carrega um arquivo JSON."""
    if not path.exists():
        raise FileNotFoundError(f"Arquivo nao encontrado: {relative_path(path)}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_manifest(path: Path = DEFAULT_MANIFEST) -> dict[str, Any]:
    """Carrega o manifesto do corpus reformado."""
    return load_json(path)


def manifest_documents_by_id(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Indexa os documentos do manifesto por `document_id`."""
    return {document["document_id"]: document for document in manifest["documents"]}


def load_normalized_document(document_id: str, normalized_dir: Path) -> dict[str, Any]:
    """Carrega o JSON normalizado de um documento."""
    return load_json(normalized_dir / f"{document_id}.normalized.json")


def load_structure_report(document_id: str, structure_dir: Path) -> dict[str, Any]:
    """Carrega o relatorio estrutural JSON de um documento."""
    return load_json(structure_dir / f"{document_id}.structure.json")


def slugify(value: str) -> str:
    """Cria fragmento estavel para ids de chunk."""
    decomposed = unicodedata.normalize("NFKD", value)
    ascii_text = decomposed.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_text.lower()).strip("-")
    return slug or "sem-referencia"


def generate_chunk_id(document_id: str, *parts: str) -> str:
    """Gera um `chunk_id` deterministico."""
    suffix = "_".join(slugify(part) for part in parts if part)
    return f"{document_id}_{suffix}"


def text_hash(text: str) -> str:
    """Calcula SHA-256 do texto principal do chunk."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def chunk_type_label(chunk_type: str) -> str:
    """Retorna rotulo legivel para o embedding text."""
    labels = {
        "doctrinal_article": "Artigo doutrinário",
        "error_refutation": "Erro e refutação",
        "conclusion_paragraph": "Parágrafo de conclusão",
        "introductory_context": "Contexto introdutório",
        "catechism_question_answer": "Pergunta e resposta catequética",
        "confessional_section": "Seção confessional",
        "confessional_paragraph": "Parágrafo confessional",
        "special_layout": "Layout especial",
    }
    return labels.get(chunk_type, chunk_type)


def build_embedding_text(chunk: dict[str, Any]) -> str:
    """Monta texto enriquecido para embeddings sem reescrever o campo `text`."""
    parts = [
        f"Documento: {chunk['document']}",
        "Corpus: Reformado",
        f"Tipo de chunk: {chunk_type_label(chunk['chunk_type'])}",
    ]
    if chunk.get("section_title"):
        parts.append(f"Seção: {chunk['section_title']}")
    if chunk.get("section_reference"):
        parts.append(f"Referência: {chunk['section_reference']}")
    parts.append(f"Texto: {chunk['text']}")
    return "\n".join(parts)


def build_base_chunk(
    manifest_document: dict[str, Any],
    normalized_document: dict[str, Any],
    chunk_id: str,
    chunk_type: str,
    content_role: str,
    is_doctrinal: bool,
    section_title: str | None,
    section_reference: str | None,
    chapter_title: str | None,
    chapter_reference: str | None,
    page_start: int,
    page_end: int,
    text: str,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    """Monta os campos comuns de um chunk."""
    chunk = {
        "chunk_id": chunk_id,
        "schema_version": SCHEMA_VERSION,
        "corpus_id": normalized_document["corpus_id"],
        "retrieval_namespace": RETRIEVAL_NAMESPACE,
        "document_id": manifest_document["document_id"],
        "document": manifest_document["title"],
        "document_type": manifest_document["document_type"],
        "tradition_family": manifest_document["tradition_family"],
        "tradition_branch": manifest_document["tradition_branch"],
        "language": manifest_document.get("language", "pt"),
        "chunk_type": chunk_type,
        "content_role": content_role,
        "is_doctrinal": is_doctrinal,
        "section_title": section_title,
        "section_reference": section_reference,
        "chapter_title": chapter_title,
        "chapter_reference": chapter_reference,
        "page_start": page_start,
        "page_end": page_end,
        "text": text.strip(),
        "embedding_text": "",
        "source_path": manifest_document["raw_path"],
        "normalized_source": (
            f"corpus/processed/normalized/reformed/{manifest_document['document_id']}.normalized.json"
        ),
        "text_hash": "",
        "warnings": warnings or [],
    }
    chunk["embedding_text"] = build_embedding_text(chunk)
    chunk["text_hash"] = text_hash(chunk["text"])
    return chunk


def split_chapter_title(chapter_title: str) -> tuple[str, str]:
    """Separa referencia e titulo de capitulo quando houver dois pontos."""
    if ":" not in chapter_title:
        return chapter_title, chapter_title
    chapter_reference, title = chapter_title.split(":", 1)
    return chapter_reference.strip(), title.strip()


def split_confession_chapter_title(chapter_title: str, chapter_number: str) -> tuple[str, str]:
    """Separa referencia e titulo de capitulos confessionais."""
    match = re.match(r"^(CAP[IÍ]TULO\s+[A-Z0-9IVXLCDM]+)\s+(.+)$", chapter_title.strip(), flags=re.IGNORECASE)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return f"CAPÍTULO {chapter_number}", chapter_title.strip()


def join_nonempty(parts: list[str]) -> str:
    """Une partes textuais preservando quebras entre blocos."""
    return "\n\n".join(part.strip() for part in parts if part and part.strip())


def get_normalized_page_text(normalized_document: dict[str, Any], page_number: int) -> str:
    """Retorna o texto normalizado de uma pagina."""
    for page in normalized_document["pages"]:
        if page["page_number"] == page_number:
            return page["text"]
    return ""


def get_normalized_page(normalized_document: dict[str, Any], page_number: int) -> dict[str, Any] | None:
    """Retorna a pagina normalizada completa, quando existir."""
    for page in normalized_document["pages"]:
        if page["page_number"] == page_number:
            return page
    return None


def build_page_intro_chunks(
    manifest_document: dict[str, Any],
    normalized_document: dict[str, Any],
    introductory_pages: list[int],
    skip_zones: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Gera chunks contextuais por pagina introdutoria, ignorando sumarios e paginas vazias."""
    skip_zones = skip_zones or set()
    chunks: list[dict[str, Any]] = []
    document_id = manifest_document["document_id"]
    for page_number in introductory_pages:
        page = get_normalized_page(normalized_document, page_number)
        if not page:
            continue
        if page.get("page_zone") in skip_zones:
            continue
        text = page.get("text", "")
        if len(text.strip()) < 30:
            continue
        chunks.append(
            build_base_chunk(
                manifest_document=manifest_document,
                normalized_document=normalized_document,
                chunk_id=generate_chunk_id(document_id, "introducao", f"pagina-{page_number:02d}"),
                chunk_type="introductory_context",
                content_role="contextual",
                is_doctrinal=False,
                section_title="Material introdutório",
                section_reference=f"Página {page_number}",
                chapter_title=None,
                chapter_reference=None,
                page_start=page_number,
                page_end=page_number,
                text=text,
                warnings=[],
            )
        )
    return chunks


def build_special_layout_chunk(
    manifest_document: dict[str, Any],
    normalized_document: dict[str, Any],
    layout: dict[str, Any],
    index: int,
    section_title: str = "Layout especial",
) -> dict[str, Any]:
    """Gera chunk para estrutura especial preservada no relatorio estrutural."""
    page_number = layout["page"]
    return build_base_chunk(
        manifest_document=manifest_document,
        normalized_document=normalized_document,
        chunk_id=generate_chunk_id(
            manifest_document["document_id"],
            "special-layout",
            f"pagina-{page_number:02d}",
            f"item-{index:02d}",
        ),
        chunk_type="special_layout",
        content_role="structural",
        is_doctrinal=False,
        section_title=section_title,
        section_reference=f"Página {page_number}",
        chapter_title=None,
        chapter_reference=None,
        page_start=page_number,
        page_end=page_number,
        text=layout["text"],
        warnings=[],
    )


def build_dort_intro_chunk(
    manifest_document: dict[str, Any],
    normalized_document: dict[str, Any],
    structure_report: dict[str, Any],
) -> list[dict[str, Any]]:
    """Gera chunk contextual introdutorio dos Cânones de Dort, quando houver texto."""
    chunks: list[dict[str, Any]] = []
    for page_number in structure_report.get("introductory_pages", []):
        text = get_normalized_page_text(normalized_document, page_number)
        if not text.strip():
            continue
        chunks.append(
            build_base_chunk(
                manifest_document=manifest_document,
                normalized_document=normalized_document,
                chunk_id=generate_chunk_id("canones-de-dort", "introducao", f"pagina-{page_number:02d}"),
                chunk_type="introductory_context",
                content_role="contextual",
                is_doctrinal=False,
                section_title="Material introdutório",
                section_reference=f"Página {page_number}",
                chapter_title=None,
                chapter_reference=None,
                page_start=page_number,
                page_end=page_number,
                text=text,
                warnings=[],
            )
        )
    return chunks


def build_dort_article_chunk(
    manifest_document: dict[str, Any],
    normalized_document: dict[str, Any],
    chapter_index: int,
    article: dict[str, Any],
) -> dict[str, Any]:
    """Gera chunk de artigo positivo dos Cânones de Dort."""
    chapter_reference, chapter_title = split_chapter_title(article["chapter_title"])
    text_parts = [article["article_heading"], article["article_text"]]
    if article.get("article_references"):
        text_parts.append(f"Referências bíblicas: {article['article_references']}")
    text = join_nonempty(text_parts)

    chunk = build_base_chunk(
        manifest_document=manifest_document,
        normalized_document=normalized_document,
        chunk_id=generate_chunk_id(
            "canones-de-dort",
            f"capitulo-{chapter_index:02d}",
            f"artigo-{int(article['article_number']):02d}",
        ),
        chunk_type="doctrinal_article",
        content_role="doctrinal",
        is_doctrinal=True,
        section_title=article["chapter_title"],
        section_reference=f"Artigo {article['article_number']}",
        chapter_title=chapter_title,
        chapter_reference=chapter_reference,
        page_start=article["page_start"],
        page_end=article["page_end"],
        text=text,
        warnings=[],
    )
    chunk["article_number"] = article["article_number"]
    chunk["article_title"] = article.get("article_title")
    chunk["reference_in_text"] = article.get("reference_in_text", [])
    chunk["article_references"] = article.get("article_references")
    return chunk


def build_dort_error_refutation_chunk(
    manifest_document: dict[str, Any],
    normalized_document: dict[str, Any],
    chapter_index: int,
    pair: dict[str, Any],
) -> dict[str, Any]:
    """Gera chunk de par erro/refutação dos Cânones de Dort."""
    chapter_reference, chapter_title = split_chapter_title(pair["chapter_title"])
    text = join_nonempty(
        [
            pair["error_heading"],
            pair["error_text"],
            "Refutação",
            pair["refutation_text"],
        ]
    )
    chunk = build_base_chunk(
        manifest_document=manifest_document,
        normalized_document=normalized_document,
        chunk_id=generate_chunk_id(
            "canones-de-dort",
            f"capitulo-{chapter_index:02d}",
            "rejeicao-erros",
            f"erro-{int(pair['error_number']):02d}",
        ),
        chunk_type="error_refutation",
        content_role="doctrinal",
        is_doctrinal=True,
        section_title=f"{pair['chapter_title']} — Rejeição de Erros",
        section_reference=f"Erro {pair['error_number']} / Refutação",
        chapter_title=chapter_title,
        chapter_reference=chapter_reference,
        page_start=pair["page_start"],
        page_end=pair["page_end"],
        text=text,
        warnings=[],
    )
    chunk["error_number"] = pair["error_number"]
    chunk["refutation_references"] = pair.get("refutation_references", [])
    return chunk


def build_dort_conclusion_chunk(
    manifest_document: dict[str, Any],
    normalized_document: dict[str, Any],
    paragraph_index: int,
    paragraph: dict[str, Any],
) -> dict[str, Any]:
    """Gera chunk de paragrafo da conclusão dos Cânones de Dort."""
    paragraph_number = paragraph.get("number")
    section_reference = f"Conclusão {paragraph_number}" if paragraph_number else f"Conclusão parágrafo {paragraph_index}"
    chunk = build_base_chunk(
        manifest_document=manifest_document,
        normalized_document=normalized_document,
        chunk_id=generate_chunk_id("canones-de-dort", "conclusao", f"paragrafo-{paragraph_index:02d}"),
        chunk_type="conclusion_paragraph",
        content_role="doctrinal",
        is_doctrinal=True,
        section_title="Conclusão",
        section_reference=section_reference,
        chapter_title=None,
        chapter_reference=None,
        page_start=paragraph["page_start"],
        page_end=paragraph["page_end"],
        text=paragraph["text"],
        warnings=[],
    )
    chunk["paragraph_type"] = paragraph.get("paragraph_type")
    chunk["paragraph_number"] = paragraph_number
    return chunk


def chunk_canons_of_dort(
    manifest_document: dict[str, Any],
    normalized_document: dict[str, Any],
    structure_report: dict[str, Any],
) -> list[dict[str, Any]]:
    """Gera chunks estruturais para os Cânones de Dort."""
    if "canons_structure" not in structure_report:
        raise ValueError("Relatorio estrutural dos Cânones nao contem `canons_structure`.")

    chunks = build_dort_intro_chunk(manifest_document, normalized_document, structure_report)
    canons = structure_report["canons_structure"]
    for chapter_index, chapter in enumerate(canons["doctrinal_chapters"], start=1):
        for article in chapter.get("articles", []):
            chunks.append(build_dort_article_chunk(manifest_document, normalized_document, chapter_index, article))
        for pair in chapter.get("rejection_of_errors", {}).get("pairs", []):
            chunks.append(build_dort_error_refutation_chunk(manifest_document, normalized_document, chapter_index, pair))

    conclusion = canons.get("conclusion")
    if conclusion:
        for paragraph_index, paragraph in enumerate(conclusion.get("paragraphs", []), start=1):
            chunks.append(build_dort_conclusion_chunk(manifest_document, normalized_document, paragraph_index, paragraph))
    return chunks


def build_catechism_text(unit: dict[str, Any]) -> str:
    """Monta texto principal de um chunk pergunta-resposta."""
    parts = []
    if unit.get("part"):
        parts.append(unit["part"])
    if unit.get("lords_day"):
        parts.append(unit["lords_day"])
    if unit.get("section_title"):
        parts.append(unit["section_title"])
    parts.append(f"P.{unit['question_number']}. {unit['question_text']}")
    parts.append(f"R. {unit['answer_text']}")
    if unit.get("references"):
        reference_lines = [
            f"{marker}. {reference}"
            for marker, reference in sorted(unit["references"].items(), key=lambda item: int(item[0]))
        ]
        parts.append("Referências bíblicas: " + " ".join(reference_lines))
    if unit.get("unresolved_answer_markers"):
        parts.append("Marcadores de referência pendentes: " + ", ".join(unit["unresolved_answer_markers"]))
    return join_nonempty(parts)


def extract_catechism_intro_text(normalized_document: dict[str, Any]) -> tuple[str, list[str]]:
    """Extrai o material introdutório do Catecismo sem incluir a primeira pergunta."""
    warnings: list[str] = []
    page_one = get_normalized_page_text(normalized_document, 1)
    if not page_one.strip():
        return "", ["introductory_page_text_not_found"]

    delimiter = "\nCATECISMO DE HEIDELBERG\nDia do Senhor 1"
    if delimiter in page_one:
        return page_one.split(delimiter, 1)[0].strip(), warnings

    fallback = "\nDia do Senhor 1"
    if fallback in page_one:
        warnings.append("introductory_context_split_by_lords_day_fallback")
        candidate = page_one.split(fallback, 1)[0].strip()
        lines = candidate.splitlines()
        if lines and lines[-1].strip() == "CATECISMO DE HEIDELBERG":
            candidate = "\n".join(lines[:-1]).strip()
        return candidate, warnings

    return "", ["introductory_context_boundary_not_found"]


def build_catechism_intro_chunk(
    manifest_document: dict[str, Any],
    normalized_document: dict[str, Any],
    structure_report: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Gera chunk contextual introdutório do Catecismo de Heidelberg."""
    contexts = structure_report.get("introductory_contexts", []) if structure_report else []
    if contexts:
        context = contexts[0]
        intro_text = context["text"]
        warnings: list[str] = []
        page_start = context.get("page_start", 1)
        page_end = context.get("page_end", page_start)
        section_title = context.get("section_title", "Material introdutório")
        section_reference = context.get("section_reference", "Página 1")
    else:
        intro_text, warnings = extract_catechism_intro_text(normalized_document)
        if not intro_text:
            return []
        page_start = 1
        page_end = 1
        section_title = "Material introdutório"
        section_reference = "Página 1"

    return [
        build_base_chunk(
            manifest_document=manifest_document,
            normalized_document=normalized_document,
            chunk_id=generate_chunk_id("catecismo-heidelberg", "introducao", "pagina-01"),
            chunk_type="introductory_context",
            content_role="contextual",
            is_doctrinal=False,
            section_title=section_title,
            section_reference=section_reference,
            chapter_title=None,
            chapter_reference=None,
            page_start=page_start,
            page_end=page_end,
            text=intro_text,
            warnings=warnings,
        )
    ]


def build_catechism_chunk(
    manifest_document: dict[str, Any],
    normalized_document: dict[str, Any],
    unit: dict[str, Any],
) -> dict[str, Any]:
    """Gera chunk pergunta-resposta do Catecismo de Heidelberg."""
    warnings: list[str] = []
    for marker in unit.get("unresolved_answer_markers", []):
        warnings.append(f"unresolved_reference_marker:{marker}")
    for issue in unit.get("reference_parse_issues", []):
        warnings.append(f"reference_parse_issue:{issue['marker']}:{issue['issue']}")

    section_reference = f"Pergunta {unit['question_number']}"
    chunk = build_base_chunk(
        manifest_document=manifest_document,
        normalized_document=normalized_document,
        chunk_id=generate_chunk_id(
            "catecismo-heidelberg",
            f"pergunta-{int(unit['question_number']):03d}",
        ),
        chunk_type="catechism_question_answer",
        content_role="doctrinal",
        is_doctrinal=True,
        section_title=unit.get("lords_day"),
        section_reference=section_reference,
        chapter_title=unit.get("part_title"),
        chapter_reference=unit.get("part_label"),
        page_start=unit["page_start"],
        page_end=unit["page_end"],
        text=build_catechism_text(unit),
        warnings=warnings,
    )
    chunk["question_number"] = unit["question_number"]
    chunk["part"] = unit.get("part")
    chunk["lords_day"] = unit.get("lords_day")
    chunk["lords_day_raw"] = unit.get("lords_day_raw")
    chunk["lords_day_inferred"] = unit.get("lords_day_inferred")
    chunk["question_text"] = unit.get("question_text")
    chunk["answer_text"] = unit.get("answer_text")
    chunk["references"] = unit.get("references", {})
    chunk["answer_reference_markers"] = unit.get("answer_reference_markers", [])
    chunk["unresolved_answer_markers"] = unit.get("unresolved_answer_markers", [])
    chunk["reference_parse_issues"] = unit.get("reference_parse_issues", [])
    return chunk


def chunk_catechism(
    manifest_document: dict[str, Any],
    normalized_document: dict[str, Any],
    structure_report: dict[str, Any],
) -> list[dict[str, Any]]:
    """Gera chunks estruturais para o Catecismo de Heidelberg."""
    if "catechism_units" not in structure_report:
        raise ValueError("Relatorio estrutural do Catecismo nao contem `catechism_units`.")
    chunks = build_catechism_intro_chunk(manifest_document, normalized_document, structure_report)
    chunks.extend(
        build_catechism_chunk(manifest_document, normalized_document, unit)
        for unit in structure_report["catechism_units"]
    )
    return chunks


def build_westminster_section_chunk(
    manifest_document: dict[str, Any],
    normalized_document: dict[str, Any],
    section: dict[str, Any],
) -> dict[str, Any]:
    """Gera chunk de seção confessional da Confissão de Westminster."""
    chapter_reference, chapter_title = split_confession_chapter_title(
        section["chapter_title"],
        section["chapter_number"],
    )
    text = join_nonempty(
        [
            section["chapter_title"],
            f"{section['section_number']}.",
            section["section_text"],
        ]
    )
    chunk = build_base_chunk(
        manifest_document=manifest_document,
        normalized_document=normalized_document,
        chunk_id=generate_chunk_id(
            "confissao-fe-westminster",
            f"capitulo-{section['chapter_number']}",
            f"secao-{section['section_number']}",
        ),
        chunk_type="confessional_section",
        content_role="doctrinal",
        is_doctrinal=True,
        section_title=section["chapter_title"],
        section_reference=f"Seção {section['section_number']}",
        chapter_title=chapter_title,
        chapter_reference=chapter_reference,
        page_start=section["page_start"],
        page_end=section["page_end"],
        text=text,
        warnings=[],
    )
    chunk["chapter_number"] = section["chapter_number"]
    chunk["section_number"] = section["section_number"]
    chunk["biblical_references"] = section.get("biblical_references", [])
    return chunk


def chunk_westminster_confession(
    manifest_document: dict[str, Any],
    normalized_document: dict[str, Any],
    structure_report: dict[str, Any],
) -> list[dict[str, Any]]:
    """Gera chunks estruturais para a Confissão de Fé de Westminster."""
    if "westminster_structure" not in structure_report:
        raise ValueError("Relatorio estrutural de Westminster nao contem `westminster_structure`.")

    chunks = build_page_intro_chunks(
        manifest_document,
        normalized_document,
        structure_report.get("introductory_pages", []),
        skip_zones={"table_of_contents"},
    )
    westminster = structure_report["westminster_structure"]
    for chapter in westminster["chapters"]:
        for section in chapter.get("sections", []):
            chunks.append(build_westminster_section_chunk(manifest_document, normalized_document, section))
    for index, layout in enumerate(westminster.get("special_layouts", []), start=1):
        chunk = build_special_layout_chunk(
            manifest_document,
            normalized_document,
            layout,
            index,
            section_title="Tabela de livros bíblicos",
        )
        chunk["layout_type"] = "biblical_books_table"
        chunks.append(chunk)
    return chunks


def build_london_paragraph_chunk(
    manifest_document: dict[str, Any],
    normalized_document: dict[str, Any],
    paragraph: dict[str, Any],
) -> dict[str, Any]:
    """Gera chunk de paragrafo confessional da Confissão Batista de Londres de 1689."""
    chapter_reference, chapter_title = split_confession_chapter_title(
        paragraph["chapter_title"],
        paragraph["chapter_number"],
    )
    text_parts = [
        paragraph["chapter_title"],
        f"{paragraph['paragraph_number']}. {paragraph['paragraph_text']}",
    ]
    if paragraph.get("reference_text"):
        text_parts.append(f"Referências bíblicas: {paragraph['reference_text']}")
    text = join_nonempty(
        text_parts
    )
    chunk = build_base_chunk(
        manifest_document=manifest_document,
        normalized_document=normalized_document,
        chunk_id=generate_chunk_id(
            "confissao-batista-londres-1689",
            f"capitulo-{paragraph['chapter_number']}",
            f"paragrafo-{paragraph['paragraph_number']}",
        ),
        chunk_type="confessional_paragraph",
        content_role="doctrinal",
        is_doctrinal=True,
        section_title=paragraph["chapter_title"],
        section_reference=f"Parágrafo {paragraph['paragraph_number']}",
        chapter_title=chapter_title,
        chapter_reference=chapter_reference,
        page_start=paragraph["page_start"],
        page_end=paragraph["page_end"],
        text=text,
        warnings=[],
    )
    chunk["chapter_number"] = paragraph["chapter_number"]
    chunk["paragraph_number"] = paragraph["paragraph_number"]
    chunk["reference_in_text"] = paragraph.get("reference_in_text", [])
    chunk["reference_text"] = paragraph.get("reference_text", "")
    chunk["references"] = paragraph.get("references", {})
    chunk["reference_associations"] = paragraph.get("reference_associations", {})
    return chunk


def chunk_london_baptist_confession(
    manifest_document: dict[str, Any],
    normalized_document: dict[str, Any],
    structure_report: dict[str, Any],
) -> list[dict[str, Any]]:
    """Gera chunks estruturais para a Confissão Batista de Londres de 1689."""
    if "london_baptist_structure" not in structure_report:
        raise ValueError("Relatorio estrutural de Londres 1689 nao contem `london_baptist_structure`.")

    chunks: list[dict[str, Any]] = []
    london = structure_report["london_baptist_structure"]
    for chapter in london["chapters"]:
        for paragraph in chapter.get("paragraphs", []):
            chunks.append(build_london_paragraph_chunk(manifest_document, normalized_document, paragraph))
    for index, layout in enumerate(london.get("special_layouts", []), start=1):
        chunk = build_special_layout_chunk(
            manifest_document,
            normalized_document,
            layout,
            index,
            section_title="Tabela de livros bíblicos",
        )
        chunk["layout_type"] = "biblical_books_table"
        chunks.append(chunk)
    return chunks


def chunk_document(
    document_id: str,
    manifest_documents: dict[str, dict[str, Any]],
    normalized_dir: Path,
    structure_dir: Path,
) -> list[dict[str, Any]]:
    """Gera chunks estruturais para um documento reformado suportado."""
    if document_id not in ALL_DOCUMENTS:
        raise ValueError(f"{document_id} nao faz parte do corpus reformado suportado.")
    manifest_document = manifest_documents[document_id]
    normalized_document = load_normalized_document(document_id, normalized_dir)
    structure_report = load_structure_report(document_id, structure_dir)

    if document_id == "confissao-fe-westminster":
        return chunk_westminster_confession(manifest_document, normalized_document, structure_report)
    if document_id == "canones-de-dort":
        return chunk_canons_of_dort(manifest_document, normalized_document, structure_report)
    if document_id == "catecismo-heidelberg":
        return chunk_catechism(manifest_document, normalized_document, structure_report)
    if document_id == "confissao-batista-londres-1689":
        return chunk_london_baptist_confession(manifest_document, normalized_document, structure_report)
    raise ValueError(f"Chunking nao implementado para {document_id}.")


def write_jsonl(chunks: list[dict[str, Any]], path: Path) -> None:
    """Grava chunks em JSONL."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for chunk in chunks:
            file.write(json.dumps(chunk, ensure_ascii=False) + "\n")


def validate_chunk(chunk: dict[str, Any]) -> list[str]:
    """Valida um chunk individual."""
    issues: list[str] = []
    missing = REQUIRED_CHUNK_FIELDS - set(chunk)
    if missing:
        issues.append(f"missing_fields:{sorted(missing)}")
    if not str(chunk.get("text", "")).strip():
        issues.append("empty_text")
    if not str(chunk.get("source_path", "")).startswith("corpus/raw/reformed/"):
        issues.append("source_path_outside_reformed_corpus")
    if chunk.get("text_hash") != text_hash(chunk.get("text", "")):
        issues.append("invalid_text_hash")
    if chunk.get("schema_version") != SCHEMA_VERSION:
        issues.append("invalid_schema_version")
    return issues


def validate_chunks(chunks: list[dict[str, Any]]) -> list[str]:
    """Valida uma lista de chunks."""
    issues: list[str] = []
    seen_ids: set[str] = set()
    for index, chunk in enumerate(chunks, start=1):
        chunk_id = chunk.get("chunk_id")
        if chunk_id in seen_ids:
            issues.append(f"duplicate_chunk_id:{chunk_id}")
        seen_ids.add(chunk_id)
        for issue in validate_chunk(chunk):
            issues.append(f"line_{index}:{issue}")
    return issues


def validate_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """Valida um JSONL linha a linha."""
    chunks: list[dict[str, Any]] = []
    issues: list[str] = []
    if not path.exists():
        return chunks, [f"jsonl_not_found:{relative_path(path)}"]

    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                issues.append(f"line_{line_number}:blank_line")
                continue
            try:
                chunks.append(json.loads(line))
            except json.JSONDecodeError as exc:
                issues.append(f"line_{line_number}:invalid_json:{exc}")
    issues.extend(validate_chunks(chunks))
    return chunks, issues


def summarize_chunks(
    document_id: str,
    chunks: list[dict[str, Any]],
    jsonl_path: Path,
    issues: list[str],
    document_warnings: list[str] | None = None,
) -> dict[str, Any]:
    """Resume chunks gerados para relatorios."""
    chunk_type_counts = Counter(chunk["chunk_type"] for chunk in chunks)
    non_doctrinal_count = sum(1 for chunk in chunks if not chunk["is_doctrinal"])
    special_layout_count = sum(1 for chunk in chunks if chunk["chunk_type"] == "special_layout")
    warning_chunks = [
        {"chunk_id": chunk["chunk_id"], "warnings": chunk["warnings"]}
        for chunk in chunks
        if chunk["warnings"]
    ]
    structural_origin = {
        "confissao-fe-westminster": (
            "`westminster_structure.chapters[].sections[]` para seções confessionais e "
            "`westminster_structure.special_layouts` para layouts especiais"
        ),
        "canones-de-dort": "`canons_structure` para artigos, rejeições de erro, conclusão e contexto introdutório",
        "catecismo-heidelberg": (
            "`introductory_contexts` para o contexto introdutório e "
            "`catechism_units` para as unidades pergunta-resposta"
        ),
        "confissao-batista-londres-1689": (
            "`london_baptist_structure.chapters[].paragraphs[]` para parágrafos confessionais e "
            "`london_baptist_structure.special_layouts` para layouts especiais"
        ),
    }.get(document_id)
    return {
        "document_id": document_id,
        "jsonl_path": relative_path(jsonl_path),
        "chunk_count": len(chunks),
        "chunk_types": dict(sorted(chunk_type_counts.items())),
        "non_doctrinal_count": non_doctrinal_count,
        "special_layout_count": special_layout_count,
        "structural_origin": structural_origin,
        "warning_chunks": warning_chunks,
        "document_warnings": document_warnings or [],
        "validation_issues": issues,
    }


def document_warnings_for_summary(document_id: str, normalized_document: dict[str, Any]) -> list[str]:
    """Coleta avisos relevantes no nivel do documento."""
    warnings: list[str] = []
    if document_id == "confissao-fe-westminster":
        page_one = get_normalized_page(normalized_document, 1)
        if page_one and not page_one.get("text", "").strip():
            warnings.append("westminster_page_1_without_extractable_text_in_spec_002")
    return warnings


def build_report(summaries: list[dict[str, Any]]) -> dict[str, Any]:
    """Monta o relatorio geral de chunking da SPEC-003A."""
    status = "PASS"
    if any(summary["validation_issues"] for summary in summaries):
        status = "FAIL"
    elif any(summary["warning_chunks"] or summary["document_warnings"] for summary in summaries):
        status = "PARTIAL"
    if {summary["document_id"] for summary in summaries} != SPEC_003A_DOCUMENTS:
        status = "FAIL"

    return {
        "status": status,
        "schema_version": SCHEMA_VERSION,
        "documents_processed": [summary["document_id"] for summary in summaries],
        "summaries": summaries,
        "not_created_in_spec_003a": [
            "corpus/processed/chunks/reformed/all_chunks.jsonl",
            "corpus/processed/chunks/reformed/confissao-fe-westminster.chunks.jsonl",
            "corpus/processed/chunks/reformed/confissao-batista-londres-1689.chunks.jsonl",
        ],
        "scope_not_executed": [
            "embeddings",
            "vector_index",
            "chatbot",
            "openai_api_call",
            "ocr",
            "manual_doctrinal_editing",
            "other_traditions_evaluation",
            "user_upload",
        ],
    }


def load_existing_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    """Carrega e valida um JSONL ja existente."""
    return validate_jsonl(path)


def consolidate_all_chunks(output_dir: Path) -> dict[str, Any]:
    """Consolida os quatro JSONL por documento em `all_chunks.jsonl`."""
    all_chunks: list[dict[str, Any]] = []
    source_files: list[str] = []
    validation_issues: list[str] = []
    per_document_counts: dict[str, int] = {}
    document_order = [
        "confissao-fe-westminster",
        "canones-de-dort",
        "catecismo-heidelberg",
        "confissao-batista-londres-1689",
    ]

    for document_id in document_order:
        path = output_dir / f"{document_id}.chunks.jsonl"
        chunks, issues = load_existing_jsonl(path)
        source_files.append(relative_path(path))
        per_document_counts[document_id] = len(chunks)
        validation_issues.extend(f"{document_id}:{issue}" for issue in issues)
        all_chunks.extend(chunks)

    duplicate_issues = validate_chunks(all_chunks)
    validation_issues.extend(f"all_chunks:{issue}" for issue in duplicate_issues)

    all_chunks_path = output_dir / CONSOLIDATED_CHUNKS_FILE
    write_jsonl(all_chunks, all_chunks_path)
    consolidated_chunks, consolidated_issues = validate_jsonl(all_chunks_path)
    validation_issues.extend(f"consolidated:{issue}" for issue in consolidated_issues)
    if len(consolidated_chunks) != sum(per_document_counts.values()):
        validation_issues.append("consolidated_count_does_not_match_document_sum")

    return {
        "jsonl_path": relative_path(all_chunks_path),
        "source_files": source_files,
        "chunk_count": len(consolidated_chunks),
        "per_document_counts": per_document_counts,
        "validation_issues": validation_issues,
    }


def build_spec_003b_report(
    summaries: list[dict[str, Any]],
    consolidation: dict[str, Any],
    generated_documents: list[str],
) -> dict[str, Any]:
    """Monta o relatorio geral de chunking e consolidacao da SPEC-003B."""
    status = "PASS"
    if any(summary["validation_issues"] for summary in summaries) or consolidation["validation_issues"]:
        status = "FAIL"
    elif any(summary["warning_chunks"] or summary["document_warnings"] for summary in summaries):
        status = "PARTIAL"
    if {summary["document_id"] for summary in summaries} != ALL_DOCUMENTS:
        status = "FAIL"

    return {
        "status": status,
        "schema_version": SCHEMA_VERSION,
        "documents_processed": [summary["document_id"] for summary in summaries],
        "documents_chunked_in_spec_003b": generated_documents,
        "documents_preserved_from_spec_003a": [
            document_id for document_id in ["canones-de-dort", "catecismo-heidelberg"]
            if document_id not in generated_documents
        ],
        "summaries": summaries,
        "consolidation": consolidation,
        "scope_not_executed": [
            "embeddings",
            "vector_index",
            "chatbot",
            "openai_api_call",
            "ocr",
            "manual_doctrinal_editing",
            "other_traditions_evaluation",
            "user_upload",
        ],
    }


def write_chunking_report(report: dict[str, Any], report_dir: Path) -> tuple[Path, Path]:
    """Grava relatorio geral de chunking em JSON e Markdown."""
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / "SPEC-003A-chunking-report.json"
    md_path = report_dir / "SPEC-003A-chunking-report.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Relatório de chunking — SPEC-003A",
        "",
        "## Status",
        "",
        report["status"],
        "",
        "## Síntese",
        "",
        (
            "A SPEC-003A gerou chunks estruturais para Cânones de Dort e Catecismo de Heidelberg "
            "a partir dos relatórios estruturais da SPEC-001 e dos textos normalizados da SPEC-002."
        ),
        "",
        "## Documentos chunkados",
        "",
    ]
    for summary in report["summaries"]:
        lines.extend(
            [
                f"### `{summary['document_id']}`",
                "",
                f"- Chunks gerados: {summary['chunk_count']}",
                f"- Tipos de chunk: {summary['chunk_types']}",
                f"- Conteúdos `is_doctrinal=false`: {summary['non_doctrinal_count']}",
                f"- Origem estrutural: {summary['structural_origin']}",
                f"- Chunks com avisos: {len(summary['warning_chunks'])}",
                f"- Arquivo JSONL: `{summary['jsonl_path']}`",
                f"- Problemas de validação: {summary['validation_issues'] or 'nenhuma ocorrência'}",
                "",
            ]
        )

    lines.extend(
        [
            "## O que não foi feito nesta SPEC",
            "",
            "- Westminster ainda não foi chunkado.",
            "- Londres 1689 ainda não foi chunkado.",
            "- `all_chunks.jsonl` ainda não foi criado.",
            "- Não foram gerados embeddings.",
            "- Não foi criado índice vetorial.",
            "- Não foi implementado chatbot.",
            "- Não houve chamada à OpenAI.",
            "- Não houve OCR.",
            "- Não houve alteração manual de conteúdo doutrinário.",
            "- Não houve avaliação com documentos de outras tradições.",
            "- Não houve upload de documentos pelo usuário.",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


def write_spec_003b_chunking_report(report: dict[str, Any], report_dir: Path) -> tuple[Path, Path]:
    """Grava relatorio de chunking e consolidacao da SPEC-003B."""
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / "SPEC-003B-chunking-report.json"
    md_path = report_dir / "SPEC-003B-chunking-report.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Relatório de chunking — SPEC-003B",
        "",
        "## Status",
        "",
        report["status"],
        "",
        "## Síntese",
        "",
        (
            "A SPEC-003B completou o chunking estrutural do corpus reformado com Westminster "
            "e Confissão Batista de Londres de 1689, preservou os chunks de Dort e Heidelberg "
            "gerados na SPEC-003A e consolidou os quatro documentos em `all_chunks.jsonl`."
        ),
        "",
        "## Documentos chunkados nesta SPEC",
        "",
    ]
    for document_id in report["documents_chunked_in_spec_003b"]:
        lines.append(f"- `{document_id}`")

    lines.extend(["", "## Documentos preservados da SPEC-003A", ""])
    for document_id in report["documents_preserved_from_spec_003a"]:
        lines.append(f"- `{document_id}`")

    lines.extend(["", "## Resumo por documento", ""])
    for summary in report["summaries"]:
        lines.extend(
            [
                f"### `{summary['document_id']}`",
                "",
                f"- Chunks gerados ou preservados: {summary['chunk_count']}",
                f"- Tipos de chunk: {summary['chunk_types']}",
                f"- Conteúdos `is_doctrinal=false`: {summary['non_doctrinal_count']}",
                f"- Layouts especiais preservados: {summary['special_layout_count']}",
                f"- Origem estrutural: {summary['structural_origin']}",
                f"- Chunks com avisos: {len(summary['warning_chunks'])}",
                f"- Avisos do documento: {summary['document_warnings'] or 'nenhuma ocorrência'}",
                f"- Arquivo JSONL: `{summary['jsonl_path']}`",
                f"- Problemas de validação: {summary['validation_issues'] or 'nenhuma ocorrência'}",
                "",
            ]
        )

    consolidation = report["consolidation"]
    lines.extend(
        [
            "## Consolidação",
            "",
            f"- Arquivo consolidado: `{consolidation['jsonl_path']}`",
            f"- Total de chunks consolidados: {consolidation['chunk_count']}",
            f"- Soma por documento: {consolidation['per_document_counts']}",
            f"- Problemas de validação: {consolidation['validation_issues'] or 'nenhuma ocorrência'}",
            "",
            "## O que não foi feito nesta SPEC",
            "",
            "- Não foram gerados embeddings.",
            "- Não foi criado índice vetorial.",
            "- Não foi implementado chatbot.",
            "- Não houve chamada à OpenAI.",
            "- Não houve OCR.",
            "- Não houve alteração manual de conteúdo doutrinário.",
            "- Não houve avaliação com documentos de outras tradições.",
            "- Não houve upload de documentos pelo usuário.",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


def run_chunking(
    documents: list[str],
    manifest_path: Path,
    normalized_dir: Path,
    structure_dir: Path,
    output_dir: Path,
    report_dir: Path,
    consolidate: bool = False,
) -> dict[str, Any]:
    """Executa o chunking estrutural para os documentos solicitados."""
    invalid_documents = [document_id for document_id in documents if document_id not in ALL_DOCUMENTS]
    if invalid_documents:
        raise ValueError(f"Documentos fora do corpus reformado suportado: {invalid_documents}")

    manifest = load_manifest(manifest_path)
    manifest_documents = manifest_documents_by_id(manifest)
    summaries: list[dict[str, Any]] = []

    for document_id in documents:
        normalized_document = load_normalized_document(document_id, normalized_dir)
        chunks = chunk_document(document_id, manifest_documents, normalized_dir, structure_dir)
        jsonl_path = output_dir / f"{document_id}.chunks.jsonl"
        write_jsonl(chunks, jsonl_path)
        validated_chunks, issues = validate_jsonl(jsonl_path)
        document_warnings = document_warnings_for_summary(document_id, normalized_document)
        summaries.append(summarize_chunks(document_id, validated_chunks, jsonl_path, issues, document_warnings))

    if consolidate:
        all_summaries: list[dict[str, Any]] = []
        for document_id in [
            "confissao-fe-westminster",
            "canones-de-dort",
            "catecismo-heidelberg",
            "confissao-batista-londres-1689",
        ]:
            jsonl_path = output_dir / f"{document_id}.chunks.jsonl"
            validated_chunks, issues = validate_jsonl(jsonl_path)
            normalized_document = load_normalized_document(document_id, normalized_dir)
            document_warnings = document_warnings_for_summary(document_id, normalized_document)
            all_summaries.append(
                summarize_chunks(document_id, validated_chunks, jsonl_path, issues, document_warnings)
            )
        consolidation = consolidate_all_chunks(output_dir)
        report = build_spec_003b_report(all_summaries, consolidation, documents)
        write_spec_003b_chunking_report(report, report_dir)
        return report

    report = build_report(summaries)
    write_chunking_report(report, report_dir)
    return report


def build_parser() -> argparse.ArgumentParser:
    """Cria o parser de linha de comando."""
    parser = argparse.ArgumentParser(description="Gera chunks estruturais do corpus reformado.")
    parser.add_argument("--documents", nargs="+", choices=sorted(ALL_DOCUMENTS), required=True)
    parser.add_argument(
        "--consolidate",
        action="store_true",
        help="Consolida os quatro arquivos por documento em all_chunks.jsonl.",
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--normalized-dir", type=Path, default=DEFAULT_NORMALIZED_DIR)
    parser.add_argument("--structure-dir", type=Path, default=DEFAULT_STRUCTURE_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    return parser


def main() -> int:
    """Ponto de entrada do script de chunking."""
    args = build_parser().parse_args()
    try:
        report = run_chunking(
            documents=args.documents,
            manifest_path=args.manifest,
            normalized_dir=args.normalized_dir,
            structure_dir=args.structure_dir,
            output_dir=args.output_dir,
            report_dir=args.report_dir,
            consolidate=args.consolidate,
        )
    except Exception as exc:
        print(f"O chunking estrutural falhou: {exc}", file=sys.stderr)
        return 1

    spec_label = "SPEC-003B" if args.consolidate else "SPEC-003A"
    print(f"Chunking {spec_label} concluído com status {report['status']}.")
    for summary in report["summaries"]:
        print(f"- {summary['document_id']}: {summary['chunk_count']} chunks em {summary['jsonl_path']}")
    if args.consolidate:
        consolidation = report["consolidation"]
        print(f"- consolidado: {consolidation['chunk_count']} chunks em {consolidation['jsonl_path']}")
    return 0 if report["status"] in {"PASS", "PARTIAL"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
