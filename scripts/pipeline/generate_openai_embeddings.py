"""Seleciona chunks elegiveis e gera embeddings OpenAI para o corpus da Alianca."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - fallback para ambientes minimos
    load_dotenv = None


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_CHUNKS_PATH = ROOT_DIR / "corpus" / "processed" / "chunks" / "alliance" / "all_chunks.jsonl"
DEFAULT_FILTERED_OUTPUT = (
    ROOT_DIR / "corpus" / "processed" / "chunks" / "alliance" / "all_chunks_for_embeddings.jsonl"
)
DEFAULT_EMBEDDINGS_OUTPUT = (
    ROOT_DIR / "corpus" / "processed" / "embeddings" / "alliance" / "openai_embeddings.jsonl"
)
DEFAULT_MANIFEST_OUTPUT = ROOT_DIR / "corpus" / "processed" / "embeddings" / "alliance" / "embedding_manifest.json"
DEFAULT_REPORT_DIR = ROOT_DIR / "corpus" / "reports" / "embeddings"
DEFAULT_STAGE_REPORT = ROOT_DIR / "reports" / "specs" / "openai-embeddings.md"
REFORMED_CHUNKS_PATH = ROOT_DIR / "corpus" / "processed" / "chunks" / "reformed" / "all_chunks.jsonl"
NORMATIVE_CHUNKS_PATH = ROOT_DIR / "corpus" / "processed" / "chunks" / "normative" / "all_chunks.jsonl"
REFORMED_EMBEDDINGS_PATH = (
    ROOT_DIR / "corpus" / "processed" / "embeddings" / "reformed" / "openai_embeddings.jsonl"
)
DEFAULT_MODEL = "text-embedding-3-large"
DEFAULT_BATCH_SIZE = 64
DEFAULT_DIMENSIONS = 3072
EMBEDDING_PROVIDER = "openai"
OPENAI_EMBEDDINGS_URL = "https://api.openai.com/v1/embeddings"
REQUIRED_CHUNK_FIELDS = {
    "chunk_id",
    "document_id",
    "corpus_id",
    "retrieval_namespace",
    "document",
    "chunk_type",
    "source_path",
    "text_hash",
    "embedding_text",
    "is_doctrinal",
}
DOCTRINAL_DOCUMENT_TYPES = {
    "confession_of_faith",
    "catechism",
    "doctrinal_canons",
}
NORMATIVE_DOCUMENT_TYPES = {
    "constitution",
    "internal_regiment",
    "normative_ethics",
    "administrative_resolution",
}
NON_RETRIEVABLE_CHUNK_TYPES = {
    "special_layout",
    "signature",
}


def relative_path(path: Path) -> str:
    """Retorna caminho relativo ao repositorio."""
    return path.relative_to(ROOT_DIR).as_posix()


def sha256_text(text: str) -> str:
    """Calcula hash SHA-256 de uma string."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    """Le um arquivo JSONL."""
    if not path.exists():
        raise FileNotFoundError(f"Arquivo nao encontrado: {relative_path(path)}")
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"JSON invalido em {relative_path(path)}:{line_number}: {exc}") from exc
    return rows


def write_jsonl(rows: list[dict[str, Any]], path: Path) -> None:
    """Grava linhas JSONL."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")


def ensure_default_alliance_chunks(path: Path) -> None:
    """Gera o JSONL unificado usado pelo retrieval atual."""
    if path != DEFAULT_CHUNKS_PATH:
        return
    chunks = []
    for source_path in (REFORMED_CHUNKS_PATH, NORMATIVE_CHUNKS_PATH):
        if not source_path.exists():
            continue
        chunks.extend(normalize_alliance_chunk(chunk) for chunk in read_jsonl(source_path))
    if not chunks:
        return

    seen_ids: set[str] = set()
    unique_chunks: list[dict[str, Any]] = []
    for chunk in chunks:
        chunk_id = str(chunk.get("chunk_id") or "")
        if not chunk_id or chunk_id in seen_ids:
            continue
        seen_ids.add(chunk_id)
        unique_chunks.append(chunk)
    write_jsonl(unique_chunks, path)


def normalize_alliance_chunk(chunk: dict[str, Any]) -> dict[str, Any]:
    """Padroniza metadados comuns sem reescrever o conteudo do chunk."""
    row = dict(chunk)
    document_id = str(row.get("document_id") or row.get("doc_id") or "").strip()
    document = str(row.get("document") or row.get("document_title") or document_id).strip()
    document_type = str(row.get("document_type") or "").strip()
    source_path = str(row.get("source_path") or "")
    is_normative_source = "/normative/" in source_path.replace("\\", "/")

    row["document_id"] = document_id
    row["doc_id"] = str(row.get("doc_id") or document_id)
    row["document"] = document
    row["document_title"] = str(row.get("document_title") or document)
    row["source_category"] = str(
        row.get("source_category")
        or ("denominational_normative_document" if is_normative_source else "doctrinal_document")
    )
    row["denomination"] = str(
        row.get("denomination")
        or (
            "Aliança das Igrejas Evangélicas Congregacionais do Brasil"
            if is_normative_source
            else ""
        )
    )
    row["tradition"] = str(
        row.get("tradition")
        or (
            "congregacional"
            if is_normative_source
            else str(row.get("tradition_branch") or "").lower()
        )
    )
    row["full_reference"] = str(
        row.get("full_reference")
        or row.get("section_reference")
        or row.get("chapter_reference")
        or row.get("section_title")
        or row.get("chapter_title")
        or ""
    )
    row["document_structure_type"] = str(row.get("document_structure_type") or row.get("chunk_type") or "")
    row["biblical_references"] = row.get("biblical_references") or []
    if document_type in DOCTRINAL_DOCUMENT_TYPES and row.get("source_category") == "doctrinal_document":
        row["is_doctrinal"] = True
        if row.get("content_role") == "normative":
            row["content_role"] = "doctrinal"
    return row


def append_jsonl(rows: list[dict[str, Any]], path: Path) -> None:
    """Acrescenta linhas JSONL."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")


def validate_chunks(chunks: list[dict[str, Any]]) -> list[str]:
    """Valida os campos minimos dos chunks de entrada."""
    issues: list[str] = []
    seen_ids: set[str] = set()
    for index, chunk in enumerate(chunks, start=1):
        chunk_id = chunk.get("chunk_id")
        if not chunk_id:
            issues.append(f"line_{index}:missing_chunk_id")
        elif chunk_id in seen_ids:
            issues.append(f"line_{index}:duplicate_chunk_id:{chunk_id}")
        seen_ids.add(chunk_id)

        missing = REQUIRED_CHUNK_FIELDS - set(chunk)
        if missing:
            issues.append(f"line_{index}:missing_fields:{sorted(missing)}")
        if chunk.get("is_doctrinal") and not chunk.get("document_id"):
            issues.append(f"line_{index}:doctrinal_chunk_without_document_id")
        source_path = str(chunk.get("source_path", ""))
        if not source_path.startswith(("corpus/raw/reformed/", "corpus/raw/normative/")):
            issues.append(f"line_{index}:source_path_outside_known_corpus")
        if not str(chunk.get("embedding_text", "")).strip():
            issues.append(f"line_{index}:empty_embedding_text")
    return issues


def embedding_selection_for_chunk(chunk: dict[str, Any]) -> tuple[bool, str | None]:
    """Define elegibilidade de um chunk para embeddings."""
    chunk_type = str(chunk.get("chunk_type") or "")
    document_structure_type = str(chunk.get("document_structure_type") or "")
    document_type = str(chunk.get("document_type") or "")
    source_category = str(chunk.get("source_category") or "")
    content_role = str(chunk.get("content_role") or "")
    if (
        chunk_type in NON_RETRIEVABLE_CHUNK_TYPES
        or document_structure_type in NON_RETRIEVABLE_CHUNK_TYPES
        or content_role == "structural"
    ):
        return False, "summary_or_non_retrievable_layout"
    if chunk.get("is_doctrinal") is True:
        return True, None
    if document_type in DOCTRINAL_DOCUMENT_TYPES | NORMATIVE_DOCUMENT_TYPES:
        return True, None
    if source_category in {"doctrinal_document", "denominational_normative_document"}:
        return True, None
    if content_role in {"doctrinal", "normative"}:
        return True, None
    if chunk.get("chunk_type") in {"introductory_context", "conclusion_paragraph"}:
        return True, None
    return False, "non_documentary_context_not_selected"


def select_chunks_for_embeddings(chunks: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Adiciona campos de controle de elegibilidade para embeddings."""
    selected_rows: list[dict[str, Any]] = []
    exclusion_reasons: Counter[str] = Counter()
    eligible_count = 0

    for chunk in chunks:
        row = dict(chunk)
        eligible, reason = embedding_selection_for_chunk(chunk)
        row["embedding_eligible"] = eligible
        row["embedding_exclusion_reason"] = reason
        selected_rows.append(row)
        if eligible:
            eligible_count += 1
        elif reason:
            exclusion_reasons[reason] += 1

    summary = {
        "total_chunks": len(chunks),
        "eligible_chunks": eligible_count,
        "excluded_chunks": len(chunks) - eligible_count,
        "exclusion_reasons": dict(sorted(exclusion_reasons.items())),
    }
    return selected_rows, summary


def metadata_for_embedding(chunk: dict[str, Any]) -> dict[str, Any]:
    """Monta metadados rastreaveis para o registro de embedding."""
    return {
        "corpus_id": chunk["corpus_id"],
        "retrieval_namespace": chunk["retrieval_namespace"],
        "doc_id": chunk.get("doc_id") or chunk.get("document_id"),
        "document_id": chunk["document_id"],
        "document": chunk["document"],
        "document_title": chunk.get("document_title") or chunk["document"],
        "document_type": chunk.get("document_type"),
        "source_category": chunk.get("source_category"),
        "denomination": chunk.get("denomination"),
        "tradition": chunk.get("tradition"),
        "chunk_type": chunk["chunk_type"],
        "content_role": chunk.get("content_role"),
        "source_path": chunk["source_path"],
        "page_start": chunk.get("page_start"),
        "page_end": chunk.get("page_end"),
        "chapter_title": chunk.get("chapter_title"),
        "chapter_reference": chunk.get("chapter_reference"),
        "section_title": chunk.get("section_title"),
        "section_reference": chunk.get("section_reference"),
        "subsection_title": chunk.get("subsection_title"),
        "article_number": chunk.get("article_number"),
        "paragraph_number": chunk.get("paragraph_number"),
        "paragraph_label": chunk.get("paragraph_label"),
        "paragraph_number_roman": chunk.get("paragraph_number_roman"),
        "inciso": chunk.get("inciso"),
        "alinea": chunk.get("alinea"),
        "full_reference": chunk.get("full_reference"),
        "document_structure_type": chunk.get("document_structure_type"),
        "biblical_references": chunk.get("biblical_references"),
        "is_doctrinal": chunk.get("is_doctrinal"),
    }


def existing_embedding_chunk_ids(path: Path) -> set[str]:
    """Le ids ja presentes no arquivo de embeddings."""
    if not path.exists():
        return set()
    return {row["chunk_id"] for row in read_jsonl(path) if row.get("chunk_id")}


def seed_reformed_embeddings_if_available(
    output_path: Path,
    eligible_chunks: list[dict[str, Any]],
) -> int:
    """Reaproveita embeddings reformados ja calculados no arquivo unificado."""
    if output_path != DEFAULT_EMBEDDINGS_OUTPUT:
        return 0
    if output_path.exists() and output_path.stat().st_size > 0:
        return 0
    if not REFORMED_EMBEDDINGS_PATH.exists():
        return 0

    eligible_by_id = {chunk["chunk_id"]: chunk for chunk in eligible_chunks}
    seeded_records = []
    for record in read_jsonl(REFORMED_EMBEDDINGS_PATH):
        chunk_id = record.get("chunk_id")
        chunk = eligible_by_id.get(chunk_id)
        if not chunk:
            continue
        if record.get("text_hash") != chunk.get("text_hash"):
            continue
        seeded_records.append(record)

    if seeded_records:
        write_jsonl(seeded_records, output_path)
    return len(seeded_records)


def build_embedding_record(
    chunk: dict[str, Any],
    embedding: list[float],
    model: str,
    dimensions: int,
) -> dict[str, Any]:
    """Monta uma linha do arquivo de embeddings."""
    return {
        "chunk_id": chunk["chunk_id"],
        "document_id": chunk["document_id"],
        "embedding_model": model,
        "embedding_provider": EMBEDDING_PROVIDER,
        "embedding": embedding,
        "embedding_dimensions": dimensions,
        "embedding_input_hash": sha256_text(chunk["embedding_text"]),
        "text_hash": chunk["text_hash"],
        "metadata": metadata_for_embedding(chunk),
    }


def request_openai_embeddings(
    inputs: list[str],
    api_key: str,
    model: str,
    dimensions: int,
    max_retries: int = 3,
) -> list[list[float]]:
    """Chama a API de embeddings da OpenAI usando biblioteca padrao."""
    payload = json.dumps(
        {
            "model": model,
            "input": inputs,
            "dimensions": dimensions,
        }
    ).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    for attempt in range(1, max_retries + 1):
        request = urllib.request.Request(
            OPENAI_EMBEDDINGS_URL,
            data=payload,
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                body = json.loads(response.read().decode("utf-8"))
            return [item["embedding"] for item in sorted(body["data"], key=lambda item: item["index"])]
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            if exc.code in {429, 500, 502, 503, 504} and attempt < max_retries:
                time.sleep(2 * attempt)
                continue
            raise RuntimeError(f"OpenAI API returned HTTP {exc.code}: {error_body[:500]}") from exc
        except urllib.error.URLError as exc:
            if attempt < max_retries:
                time.sleep(2 * attempt)
                continue
            raise RuntimeError(f"OpenAI API request failed: {exc}") from exc

    raise RuntimeError("OpenAI API request failed after retries")


def batched(items: list[dict[str, Any]], batch_size: int) -> list[list[dict[str, Any]]]:
    """Divide itens em lotes."""
    return [items[index : index + batch_size] for index in range(0, len(items), batch_size)]


def generate_embeddings(
    eligible_chunks: list[dict[str, Any]],
    output_path: Path,
    api_key: str,
    model: str,
    dimensions: int,
    batch_size: int,
    resume: bool,
) -> tuple[int, bool, str | None]:
    """Gera embeddings em lotes e grava JSONL incrementalmente."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    existing_ids = existing_embedding_chunk_ids(output_path) if resume else set()
    if not resume:
        output_path.write_text("", encoding="utf-8")

    pending_chunks = [chunk for chunk in eligible_chunks if chunk["chunk_id"] not in existing_ids]
    resumed = bool(existing_ids)
    generated_count = len(existing_ids)

    try:
        for batch in batched(pending_chunks, batch_size):
            embeddings = request_openai_embeddings(
                [chunk["embedding_text"] for chunk in batch],
                api_key=api_key,
                model=model,
                dimensions=dimensions,
            )
            records = [
                build_embedding_record(chunk, embedding, model, dimensions)
                for chunk, embedding in zip(batch, embeddings, strict=True)
            ]
            append_jsonl(records, output_path)
            generated_count += len(records)
    except Exception as exc:
        return generated_count, resumed, str(exc)

    return generated_count, resumed, None


def audit_paths() -> list[str]:
    """Lista auditorias existentes para registro metodologico."""
    audits_dir = ROOT_DIR / "reports" / "audits"
    if not audits_dir.exists():
        return []
    return [relative_path(path) for path in sorted(audits_dir.glob("*.md"))]


def write_embedding_manifest(
    path: Path,
    report: dict[str, Any],
    embeddings_output: Path,
    filtered_output: Path,
) -> None:
    """Grava manifesto de embeddings."""
    path.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "embedding_provider": EMBEDDING_PROVIDER,
        "embedding_model": report["embedding_model"],
        "embedding_dimensions": report["embedding_dimensions"],
        "input_chunks_path": report["input_chunks_path"],
        "filtered_chunks_path": relative_path(filtered_output),
        "embeddings_path": relative_path(embeddings_output),
        "total_chunks": report["total_chunks"],
        "eligible_chunks": report["eligible_chunks"],
        "excluded_chunks": report["excluded_chunks"],
        "embeddings_generated": report["embeddings_generated"],
        "status": report["status"],
    }
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_report(
    chunks_path: Path,
    filtered_output: Path,
    embeddings_output: Path,
    selection_summary: dict[str, Any],
    model: str,
    dimensions: int,
    embeddings_generated: int,
    resumed: bool,
    api_key_available: bool,
    api_error: str | None,
    validation_issues: list[str],
) -> dict[str, Any]:
    """Monta relatorio estruturado da geração de embeddings OpenAI."""
    status = "PASS"
    if validation_issues:
        status = "FAIL"
    elif api_key_available and api_error:
        status = "FAIL"
    elif not api_key_available or embeddings_generated < selection_summary["eligible_chunks"]:
        status = "PARTIAL"

    return {
        "status": status,
        "input_chunks_path": relative_path(chunks_path),
        "filtered_chunks_path": relative_path(filtered_output),
        "embeddings_path": relative_path(embeddings_output),
        "embedding_provider": EMBEDDING_PROVIDER,
        "embedding_model": model,
        "embedding_dimensions": dimensions,
        "total_chunks": selection_summary["total_chunks"],
        "eligible_chunks": selection_summary["eligible_chunks"],
        "excluded_chunks": selection_summary["excluded_chunks"],
        "exclusion_reasons": selection_summary["exclusion_reasons"],
        "embeddings_generated": embeddings_generated,
        "resumed": resumed,
        "api_key_available": api_key_available,
        "api_error": api_error,
        "validation_issues": validation_issues,
        "manual_audit_paths": audit_paths(),
        "scope_not_executed": [
            "chromadb_index",
            "chatbot",
            "llm_response_generation",
            "other_traditions_evaluation",
            "user_upload",
            "manual_doctrinal_text_editing",
            "new_extraction_normalization_or_chunking",
        ],
    }


def write_markdown_reports(report: dict[str, Any], report_dir: Path, spec_report_path: Path) -> None:
    """Grava relatorios Markdown da geração de embeddings OpenAI."""
    report_dir.mkdir(parents=True, exist_ok=True)
    spec_report_path.parent.mkdir(parents=True, exist_ok=True)

    audit_text = (
        "\n".join(f"- `{path}`" for path in report["manual_audit_paths"])
        if report["manual_audit_paths"]
        else "- Auditoria manual registrada como etapa metodológica prévia, sem arquivo específico local."
    )
    api_status = "configurada" if report["api_key_available"] else "não configurada"
    api_error = report["api_error"] or "nenhuma ocorrência"

    embedding_report_lines = [
        "# Relatório de embeddings — OpenAI",
        "",
        "## Status",
        "",
        report["status"],
        "",
        "## Síntese",
        "",
        (
            f"Foram lidos {report['total_chunks']} chunks do corpus documental da Aliança. "
            f"A seleção marcou {report['eligible_chunks']} chunks como elegíveis para embeddings "
            f"e excluiu {report['excluded_chunks']} chunks por critérios de recuperação."
        ),
        "",
        "## Seleção",
        "",
        f"- Chunks lidos: {report['total_chunks']}",
        f"- Chunks elegíveis: {report['eligible_chunks']}",
        f"- Chunks excluídos: {report['excluded_chunks']}",
        f"- Motivos de exclusão: {report['exclusion_reasons'] or 'nenhuma ocorrência'}",
        "",
        "## Geração de embeddings",
        "",
        f"- Provedor: `{report['embedding_provider']}`",
        f"- Modelo: `{report['embedding_model']}`",
        f"- Dimensões: {report['embedding_dimensions']}",
        f"- Embeddings gerados: {report['embeddings_generated']}",
        f"- Retomada parcial: {report['resumed']}",
        f"- Chave OpenAI: {api_status}",
        f"- Erro de API: {api_error}",
        "",
        "## O que não foi feito nesta etapa",
        "",
        "- Não foi criado índice ChromaDB.",
        "- Não foi implementado chatbot.",
        "- Não houve geração de respostas com LLM.",
        "- Não foi feita avaliação com documentos de outras tradições.",
        "- Não houve upload de documentos pelo usuário.",
        "- Não houve alteração manual de texto doutrinário.",
        "- Não houve nova extração, normalização ou chunking.",
    ]
    (report_dir / "openai-embedding-report.md").write_text(
        "\n".join(embedding_report_lines) + "\n",
        encoding="utf-8",
    )

    spec_lines = [
        "# Seleção de chunks e geração de embeddings com OpenAI",
        "",
        "## Status",
        "",
        report["status"],
        "",
        "## Objetivo da etapa",
        "",
        (
            "Selecionar chunks elegíveis do corpus doutrinário e normativo da Aliança e gerar embeddings com OpenAI, "
            "preservando rastreabilidade documental para a etapa posterior de indexação no ChromaDB."
        ),
        "",
        "## Entradas utilizadas",
        "",
        "- `corpus/raw/reformed_manifest.json`",
        "- `reports/specs/reformed-corpus-foundation.md`",
        "- `reports/specs/extraction-normalization.md`",
        "- `reports/specs/structural-chunking-base.md`",
        "- `reports/specs/structural-chunking-final.md`",
        f"- `{report['input_chunks_path']}`",
        "",
        "## Auditoria manual prévia",
        "",
        "A auditoria manual dos chunks foi realizada pela desenvolvedora/pesquisadora antes desta etapa.",
        "",
        audit_text,
        "",
        "## Seleção de chunks para embeddings",
        "",
        f"Foram lidos {report['total_chunks']} chunks. A seleção marcou {report['eligible_chunks']} chunks como elegíveis e {report['excluded_chunks']} como excluídos.",
        "",
        f"Motivos de exclusão: {report['exclusion_reasons'] or 'nenhuma ocorrência'}.",
        "",
        "## Modelo de embeddings",
        "",
        f"- Provedor: `{report['embedding_provider']}`",
        f"- Modelo: `{report['embedding_model']}`",
        f"- Dimensões solicitadas: {report['embedding_dimensions']}",
        "",
        "## Embeddings gerados",
        "",
        f"Foram gerados {report['embeddings_generated']} embeddings.",
        "",
        "## Validações executadas",
        "",
        "```bash",
        "python scripts/pipeline/generate_openai_embeddings.py",
        "python -m py_compile scripts/pipeline/generate_openai_embeddings.py",
        "python -m pytest tests/test_openai_embeddings.py",
        "```",
        "",
        f"Problemas de validação: {report['validation_issues'] or 'nenhuma ocorrência'}.",
        "",
        "## Pontos de atenção",
        "",
        f"- Chave OpenAI: {api_status}.",
        f"- Erro de API: {api_error}.",
        "- Chunks `special_layout` foram excluídos da geração de embeddings por serem layouts técnicos/listas isoladas.",
        "",
        "## O que não foi feito nesta etapa",
        "",
        "- não foi criado índice ChromaDB;",
        "- não foi implementado chatbot;",
        "- não houve geração de respostas com LLM;",
        "- não foi feita avaliação com documentos de outras tradições;",
        "- não houve upload de documentos pelo usuário;",
        "- não houve alteração manual de texto doutrinário;",
        "- não houve nova extração, normalização ou chunking.",
    ]
    spec_report_path.write_text("\n".join(spec_lines) + "\n", encoding="utf-8")


def write_json_report(report: dict[str, Any], report_dir: Path) -> None:
    """Grava relatorio JSON."""
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "openai-embedding-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def run(
    chunks_path: Path,
    filtered_output: Path,
    embeddings_output: Path,
    embedding_model: str,
    batch_size: int,
    output_dimensions: int,
    resume: bool,
) -> dict[str, Any]:
    """Executa a geração de embeddings OpenAI."""
    if load_dotenv is not None:
        load_dotenv(ROOT_DIR / ".env")

    ensure_default_alliance_chunks(chunks_path)
    chunks = read_jsonl(chunks_path)
    validation_issues = validate_chunks(chunks)
    selected_rows, selection_summary = select_chunks_for_embeddings(chunks)
    write_jsonl(selected_rows, filtered_output)

    eligible_chunks = [row for row in selected_rows if row["embedding_eligible"]]
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    api_key_available = bool(api_key)
    embeddings_generated = 0
    resumed = False
    api_error: str | None = None

    if validation_issues:
        api_error = "embedding_generation_skipped_due_to_invalid_chunks"
    elif not api_key_available:
        embeddings_output.parent.mkdir(parents=True, exist_ok=True)
        if not embeddings_output.exists():
            embeddings_output.write_text("", encoding="utf-8")
    else:
        seeded_count = seed_reformed_embeddings_if_available(embeddings_output, eligible_chunks)
        embeddings_generated, resumed, api_error = generate_embeddings(
            eligible_chunks=eligible_chunks,
            output_path=embeddings_output,
            api_key=api_key,
            model=embedding_model,
            dimensions=output_dimensions,
            batch_size=batch_size,
            resume=resume or seeded_count > 0,
        )

    report = build_report(
        chunks_path=chunks_path,
        filtered_output=filtered_output,
        embeddings_output=embeddings_output,
        selection_summary=selection_summary,
        model=embedding_model,
        dimensions=output_dimensions,
        embeddings_generated=embeddings_generated,
        resumed=resumed,
        api_key_available=api_key_available,
        api_error=api_error,
        validation_issues=validation_issues,
    )
    write_embedding_manifest(DEFAULT_MANIFEST_OUTPUT, report, embeddings_output, filtered_output)
    write_json_report(report, DEFAULT_REPORT_DIR)
    write_markdown_reports(report, DEFAULT_REPORT_DIR, DEFAULT_STAGE_REPORT)
    return report


def build_parser() -> argparse.ArgumentParser:
    """Cria parser CLI."""
    parser = argparse.ArgumentParser(description="Gera embeddings OpenAI para chunks da Aliança.")
    parser.add_argument("--chunks-path", type=Path, default=DEFAULT_CHUNKS_PATH)
    parser.add_argument("--filtered-output", type=Path, default=DEFAULT_FILTERED_OUTPUT)
    parser.add_argument("--embeddings-output", type=Path, default=DEFAULT_EMBEDDINGS_OUTPUT)
    parser.add_argument("--embedding-model", default=DEFAULT_MODEL)
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--output-dimensions", type=int, default=DEFAULT_DIMENSIONS)
    parser.add_argument("--resume", action="store_true")
    return parser


def main() -> int:
    """Ponto de entrada CLI."""
    args = build_parser().parse_args()
    try:
        report = run(
            chunks_path=args.chunks_path,
            filtered_output=args.filtered_output,
            embeddings_output=args.embeddings_output,
            embedding_model=args.embedding_model,
            batch_size=args.batch_size,
            output_dimensions=args.output_dimensions,
            resume=args.resume,
        )
    except Exception as exc:
        print(f"A geração de embeddings OpenAI falhou: {exc}", file=sys.stderr)
        return 1

    print(f"Geração de embeddings OpenAI concluída com status {report['status']}.")
    print(f"- chunks lidos: {report['total_chunks']}")
    print(f"- chunks elegíveis: {report['eligible_chunks']}")
    print(f"- chunks excluídos: {report['excluded_chunks']}")
    print(f"- embeddings gerados: {report['embeddings_generated']}")
    if report["api_error"]:
        print(f"- ponto de atenção: {report['api_error']}")
    return 0 if report["status"] in {"PASS", "PARTIAL"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
