"""Executa perguntas de avaliação no AIA e gera dataset para RAGAS."""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None


ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


REQUIRED_COLUMNS = [
    "id",
    "categoria",
    "pergunta",
    "documentos_esperados",
    "escopo_esperado",
    "mistura_permitida",
    "referencia_esperada",
    "resposta_esperada_ground_truth",
    "deve_responder",
    "observacao",
]

CSV_SUMMARY_COLUMNS = [
    "id",
    "categoria",
    "question",
    "answer",
    "ground_truth",
    "context_count",
    "source_count",
    "retrieved_document_ids",
    "retrieved_document_titles",
    "documentos_esperados",
    "escopo_esperado",
    "mistura_permitida",
    "referencia_esperada",
    "deve_responder",
    "observacao",
    "error",
    "warning",
]

SOURCE_FIELDS = [
    "chunk_id",
    "document_id",
    "document_title",
    "page",
    "chapter",
    "section",
    "article",
    "paragraph",
    "score",
    "rerank_score",
    "document_type",
    "source_category",
    "denomination",
    "tradition",
    "full_reference",
    "source_path",
]


def load_questions(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        sample = file.read(4096)
        file.seek(0)
        dialect = sniff_csv_dialect(sample)
        reader = csv.DictReader(file, dialect=dialect)
        fieldnames = [clean_cell(fieldname) for fieldname in (reader.fieldnames or [])]
        missing = [column for column in REQUIRED_COLUMNS if column not in fieldnames]
        if missing:
            raise ValueError(
                "CSV de avaliação sem colunas obrigatórias: " + ", ".join(missing)
            )
        rows: list[dict[str, str]] = []
        for row in reader:
            normalized_row = {
                clean_cell(key): clean_cell(value)
                for key, value in row.items()
                if key is not None
            }
            rows.append(normalized_row)
        return rows


def sniff_csv_dialect(sample: str) -> csv.Dialect:
    try:
        return csv.Sniffer().sniff(sample, delimiters=";,")
    except csv.Error:
        class SemicolonDialect(csv.excel):
            delimiter = ";"

        return SemicolonDialect


def clean_cell(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def make_base_record(row: dict[str, str]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "categoria": row["categoria"],
        "question": row["pergunta"],
        "answer": "",
        "contexts": [],
        "prompt_contexts": [],
        "prompt_sources": [],
        "expanded_sources": [],
        "retrieval_candidates": [],
        "retrieved_sources": [],
        "ground_truth": row["resposta_esperada_ground_truth"],
        "documentos_esperados": row["documentos_esperados"],
        "escopo_esperado": row["escopo_esperado"],
        "mistura_permitida": row["mistura_permitida"],
        "referencia_esperada": row["referencia_esperada"],
        "deve_responder": row["deve_responder"],
        "observacao": row["observacao"],
        "error": None,
        "warning": None,
    }


class InternalRagClient:
    """Cliente local que reutiliza o gerador RAG oficial do projeto."""

    def __init__(self, model: str | None, temperature: float, max_output_tokens: int) -> None:
        if load_dotenv is not None:
            load_dotenv(ROOT_DIR / ".env")
        from aia.generation.rag_generator import RagGenerator

        self.generator = RagGenerator(
            model=model,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )

    def ask(self, question: str, context_mode: str = "prompt") -> dict[str, Any]:
        answer = self.generator.answer(question)
        answer_data = answer.to_dict()
        metadata = answer_data.get("metadata") if isinstance(answer_data.get("metadata"), dict) else {}
        audit_fields = extract_from_retrieval_package(
            metadata.get("retrieval_package"),
            context_mode=context_mode,
            used_source_ids=set(answer.used_sources),
        )
        return {
            "answer": answer.answer,
            **audit_fields,
            "contexts": audit_fields["contexts"],
            "retrieved_sources": audit_fields["expanded_sources"],
            "status": answer.status,
            "raw_response": answer_data,
        }


class HttpRagClient:
    """Cliente HTTP para endpoint FastAPI do chatbot."""

    def __init__(self, endpoint: str, timeout: float) -> None:
        self.endpoint = endpoint
        self.timeout = timeout

    def ask(self, question: str, context_mode: str = "prompt") -> dict[str, Any]:
        payload = json.dumps({"question": question}, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            self.endpoint,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code}: {body}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Erro HTTP: {exc.reason}") from exc

        data = json.loads(raw)
        audit_fields = extract_from_http_response(data, context_mode=context_mode)
        return {
            "answer": clean_cell(data.get("answer")),
            **audit_fields,
            "contexts": audit_fields["contexts"],
            "retrieved_sources": audit_fields["expanded_sources"],
            "status": data.get("status"),
            "raw_response": data,
        }


def extract_from_retrieval_package(
    package: Any,
    context_mode: str = "prompt",
    used_source_ids: set[str] | None = None,
) -> dict[str, Any]:
    if not isinstance(package, dict):
        return empty_audit_fields()

    contexts: list[str] = []
    prompt_contexts: list[str] = []
    prompt_sources: list[dict[str, Any]] = []
    expanded_sources: list[dict[str, Any]] = []
    all_contexts = [context for context in package.get("contexts") or [] if isinstance(context, dict)]
    source_contexts = [(f"source_{index}", context) for index, context in enumerate(all_contexts, start=1)]
    source_map = package.get("source_map") if isinstance(package.get("source_map"), dict) else {}
    package_metadata = package.get("metadata") if isinstance(package.get("metadata"), dict) else {}
    retrieval_candidates = normalize_retrieval_candidates(
        package_metadata.get("retrieval_candidates")
    )

    selected_contexts = source_contexts
    if context_mode == "cited" and used_source_ids:
        selected_contexts = [
            (source_id, context)
            for source_id, context in source_contexts
            if source_id in used_source_ids
        ]

    for source_id, context in source_contexts:
        if not isinstance(context, dict):
            continue
        context_index = int(source_id.split("_")[-1])
        context_text = clean_cell(context.get("context_text"))
        if context_text:
            prompt_contexts.append(context_text)
        prompt_sources.append(
            prompt_source_from_context(
                context=context,
                source_id=source_id,
                source_map_entry=source_map.get(source_id) if isinstance(source_map, dict) else None,
                context_index=context_index,
            )
        )
        metadata = context.get("metadata") if isinstance(context.get("metadata"), dict) else {}
        chunks = metadata.get("included_chunks")
        if isinstance(chunks, list) and chunks:
            for chunk in chunks:
                if not isinstance(chunk, dict):
                    continue
                source = source_from_chunk(context, chunk)
                source["source_id"] = source_id
                source["context_index"] = context_index
                source["selected_for_prompt"] = True
                source["is_anchor"] = source.get("chunk_id") in set(context.get("anchor_chunk_ids") or [])
                expanded_sources.append(source)
            continue

        source = source_from_context(context)
        source["source_id"] = source_id
        source["context_index"] = context_index
        source["selected_for_prompt"] = True
        source["is_anchor"] = True
        expanded_sources.append(source)

    for source_id, context in selected_contexts:
        metadata = context.get("metadata") if isinstance(context.get("metadata"), dict) else {}
        chunks = metadata.get("included_chunks")
        if context_mode == "chunks" and isinstance(chunks, list) and chunks:
            for chunk in chunks:
                if not isinstance(chunk, dict):
                    continue
                text = clean_cell(chunk.get("text"))
                if text:
                    contexts.append(text)
            continue

        context_text = clean_cell(context.get("context_text"))
        if context_text:
            contexts.append(context_text)
    return {
        "contexts": contexts,
        "prompt_contexts": prompt_contexts,
        "prompt_sources": prompt_sources,
        "expanded_sources": expanded_sources,
        "retrieval_candidates": retrieval_candidates,
    }


def extract_from_http_response(
    data: dict[str, Any],
    context_mode: str = "prompt",
) -> dict[str, Any]:
    contexts: list[str] = []
    prompt_contexts: list[str] = []
    prompt_sources: list[dict[str, Any]] = []
    expanded_sources: list[dict[str, Any]] = []
    metadata = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
    retrieval_candidates = normalize_retrieval_candidates(metadata.get("retrieval_candidates"))
    for context_index, citation in enumerate(data.get("citations") or [], start=1):
        if not isinstance(citation, dict):
            continue
        source_id = clean_cell(citation.get("source_id")) or f"source_{context_index}"
        prompt_sources.append(
            prompt_source_from_http_citation(citation, context_index=context_index)
        )
        context_text = clean_cell(citation.get("context_text"))
        if context_text:
            prompt_contexts.append(context_text)
        chunk_texts = citation.get("chunk_texts")
        if isinstance(chunk_texts, list) and chunk_texts:
            for chunk in chunk_texts:
                if not isinstance(chunk, dict):
                    continue
                source = source_from_http_citation(citation, chunk)
                source["context_index"] = context_index
                source["source_id"] = source_id
                source["selected_for_prompt"] = True
                source["is_anchor"] = source.get("chunk_id") in set(citation.get("anchor_chunk_ids") or [])
                expanded_sources.append(source)
            if context_mode == "chunks":
                for chunk in chunk_texts:
                    if not isinstance(chunk, dict):
                        continue
                    text = clean_cell(chunk.get("text"))
                    if text:
                        contexts.append(text)
                continue

        if context_text:
            contexts.append(context_text)
        source = source_from_http_citation(citation, {})
        source["context_index"] = context_index
        source["selected_for_prompt"] = True
        source["is_anchor"] = True
        expanded_sources.append(source)
    return {
        "contexts": contexts,
        "prompt_contexts": prompt_contexts,
        "prompt_sources": prompt_sources,
        "expanded_sources": expanded_sources,
        "retrieval_candidates": retrieval_candidates,
    }


def empty_audit_fields() -> dict[str, Any]:
    return {
        "contexts": [],
        "prompt_contexts": [],
        "prompt_sources": [],
        "expanded_sources": [],
        "retrieval_candidates": [],
    }


def prompt_source_from_context(
    context: dict[str, Any],
    source_id: str,
    source_map_entry: Any,
    context_index: int,
) -> dict[str, Any]:
    metadata = context.get("metadata") if isinstance(context.get("metadata"), dict) else {}
    source_map = source_map_entry if isinstance(source_map_entry, dict) else {}
    source = {
        "context_index": context_index,
        "source_id": source_id,
        "anchor_chunk_id": first_value(source_map, "anchor_chunk_id")
        or first_list_value(context.get("anchor_chunk_ids")),
        "document_id": source_map.get("document_id") or context.get("document_id"),
        "document_title": source_map.get("document_title")
        or source_map.get("document")
        or context.get("document")
        or metadata.get("document_title"),
        "parent_key": source_map.get("parent_key") or context.get("parent_key"),
        "parent_title": source_map.get("parent_title") or context.get("parent_title"),
        "full_reference": source_map.get("full_reference") or metadata.get("full_reference"),
        "page": source_map.get("pages") or format_page(context.get("page_start"), context.get("page_end")),
        "final_rank": source_map.get("final_rank") or context.get("rank") or context_index,
        "score": source_map.get("score") or first_list_value(context.get("anchor_scores")),
        "ranking_score": source_map.get("ranking_score") or metadata.get("ranking_score"),
        "selected_for_prompt": True,
    }
    return normalize_prompt_source(source)


def prompt_source_from_http_citation(
    citation: dict[str, Any],
    context_index: int,
) -> dict[str, Any]:
    source = {
        "context_index": context_index,
        "source_id": citation.get("source_id") or f"source_{context_index}",
        "anchor_chunk_id": first_list_value(citation.get("anchor_chunk_ids")),
        "document_id": citation.get("document_id"),
        "document_title": citation.get("document"),
        "parent_key": citation.get("parent_key"),
        "parent_title": citation.get("parent_title"),
        "full_reference": citation.get("full_reference") or citation.get("structural_reference"),
        "page": citation.get("pages") or format_page(citation.get("page_start"), citation.get("page_end")),
        "final_rank": context_index,
        "score": None,
        "ranking_score": None,
        "selected_for_prompt": True,
    }
    return normalize_prompt_source(source)


def normalize_prompt_source(source: dict[str, Any]) -> dict[str, Any]:
    return {
        key: (None if value == "" else value)
        for key, value in source.items()
    }


def normalize_retrieval_candidates(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    candidates: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        candidates.append(
            {
                "chunk_id": item.get("chunk_id"),
                "document_id": item.get("document_id"),
                "document_title": item.get("document_title"),
                "dense_score": item.get("dense_score"),
                "bm25_score": item.get("bm25_score"),
                "rrf_score": item.get("rrf_score"),
                "rerank_score": item.get("rerank_score"),
                "ranking_score": item.get("ranking_score"),
                "candidate_rank": item.get("candidate_rank"),
                "final_rank": item.get("final_rank"),
                "selected_for_prompt": bool(item.get("selected_for_prompt")),
                "parent_key": item.get("parent_key"),
                "parent_title": item.get("parent_title"),
                "page": item.get("page"),
                "context_status": item.get("context_status"),
                "included_chunk_ids": item.get("included_chunk_ids") or [],
                "retrieval_sources": item.get("retrieval_sources") or [],
            }
        )
    return candidates


def source_from_chunk(context: dict[str, Any], chunk: dict[str, Any]) -> dict[str, Any]:
    metadata = context.get("metadata") if isinstance(context.get("metadata"), dict) else {}
    source = {
        "source_id": None,
        "chunk_id": first_value(chunk, "chunk_id", "id"),
        "document_id": first_value(chunk, "document_id") or context.get("document_id"),
        "document_title": first_value(chunk, "document", "document_title", "title")
        or context.get("document"),
        "page": format_page(
            first_value(chunk, "page", "page_number", "page_start") or context.get("page_start"),
            first_value(chunk, "page_end") or context.get("page_end"),
        ),
        "chapter": first_value(
            chunk,
            "chapter",
            "chapter_title",
            "chapter_reference",
            "chapter_number",
        ),
        "section": first_value(chunk, "section", "section_title", "section_reference"),
        "article": first_value(chunk, "article", "article_number", "article_label"),
        "paragraph": first_value(chunk, "paragraph", "paragraph_number", "paragraph_label"),
        "score": first_value(chunk, "score", "distance") or anchor_score_for_chunk(context, chunk),
        "rerank_score": first_value(chunk, "rerank_score", "cross_encoder_score"),
        "document_type": first_value(chunk, "document_type") or metadata.get("document_type"),
        "source_category": first_value(chunk, "source_category") or metadata.get("source_category"),
        "denomination": first_value(chunk, "denomination") or metadata.get("denomination"),
        "tradition": first_value(chunk, "tradition") or metadata.get("tradition"),
        "full_reference": first_value(chunk, "full_reference") or metadata.get("full_reference"),
        "source_path": first_value(chunk, "source_path") or first_list_value(context.get("source_paths")),
    }
    return normalize_source(source)


def source_from_context(context: dict[str, Any]) -> dict[str, Any]:
    metadata = context.get("metadata") if isinstance(context.get("metadata"), dict) else {}
    source = {
        "source_id": None,
        "chunk_id": first_list_value(context.get("included_chunk_ids")),
        "document_id": context.get("document_id"),
        "document_title": context.get("document"),
        "page": format_page(context.get("page_start"), context.get("page_end")),
        "chapter": metadata.get("chapter_title") or metadata.get("chapter_reference"),
        "section": metadata.get("section_title") or metadata.get("section_reference"),
        "article": metadata.get("article_number") or metadata.get("article_label"),
        "paragraph": metadata.get("paragraph_number") or metadata.get("paragraph_label"),
        "score": first_list_value(context.get("anchor_scores")),
        "rerank_score": metadata.get("rerank_score") or metadata.get("cross_encoder_score"),
        "document_type": metadata.get("document_type"),
        "source_category": metadata.get("source_category"),
        "denomination": metadata.get("denomination"),
        "tradition": metadata.get("tradition"),
        "full_reference": metadata.get("full_reference"),
        "source_path": first_list_value(context.get("source_paths")),
    }
    return normalize_source(source)


def source_from_http_citation(citation: dict[str, Any], chunk: dict[str, Any]) -> dict[str, Any]:
    source = {
        "source_id": citation.get("source_id"),
        "chunk_id": first_value(chunk, "chunk_id") or first_list_value(citation.get("included_chunk_ids")),
        "document_id": citation.get("document_id"),
        "document_title": citation.get("document"),
        "page": citation.get("pages") or format_page(citation.get("page_start"), citation.get("page_end")),
        "chapter": citation.get("parent_title"),
        "section": citation.get("structural_reference"),
        "article": None,
        "paragraph": None,
        "score": None,
        "rerank_score": None,
        "document_type": citation.get("document_type"),
        "source_category": citation.get("source_category"),
        "denomination": citation.get("denomination"),
        "tradition": citation.get("tradition"),
        "full_reference": citation.get("full_reference"),
        "source_path": first_list_value(citation.get("source_paths")),
    }
    return normalize_source(source)


def first_value(data: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = data.get(key)
        if value not in (None, ""):
            return value
    return None


def first_list_value(value: Any) -> Any:
    if isinstance(value, list) and value:
        return value[0]
    return value


def anchor_score_for_chunk(context: dict[str, Any], chunk: dict[str, Any]) -> Any:
    chunk_id = clean_cell(chunk.get("chunk_id"))
    anchor_ids = context.get("anchor_chunk_ids")
    anchor_scores = context.get("anchor_scores")
    if not chunk_id or not isinstance(anchor_ids, list) or not isinstance(anchor_scores, list):
        return None
    try:
        index = [str(value) for value in anchor_ids].index(chunk_id)
    except ValueError:
        return None
    if index >= len(anchor_scores):
        return None
    return anchor_scores[index]


def format_page(start: Any, end: Any = None) -> str | None:
    if start in (None, "") and end in (None, ""):
        return None
    if end in (None, "") or str(start) == str(end):
        return str(start)
    if start in (None, ""):
        return str(end)
    return f"{start}-{end}"


def normalize_source(source: dict[str, Any]) -> dict[str, Any]:
    normalized = {
        "source_id": None if source.get("source_id") == "" else source.get("source_id"),
    }
    normalized.update(
        {
            field: (None if source.get(field) == "" else source.get(field))
            for field in SOURCE_FIELDS
        }
    )
    return normalized


def run_questions(args: argparse.Namespace) -> list[dict[str, Any]]:
    rows = load_questions(args.input)
    client = (
        HttpRagClient(args.endpoint, args.timeout)
        if args.endpoint
        else InternalRagClient(args.model, args.temperature, args.max_output_tokens)
    )

    records: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        record = make_base_record(row)
        question = record["question"]
        print(f"[{index}/{len(rows)}] {record['id']} - executando pergunta...")
        try:
            response = client.ask(question, context_mode=args.context_mode)
            record["answer"] = response["answer"]
            record["contexts"] = response["contexts"]
            record["prompt_contexts"] = response.get("prompt_contexts", [])
            record["prompt_sources"] = response.get("prompt_sources", [])
            record["expanded_sources"] = response.get("expanded_sources", [])
            record["retrieval_candidates"] = response.get("retrieval_candidates", [])
            record["retrieved_sources"] = response.get("retrieved_sources") or record["expanded_sources"]
            record["chatbot_status"] = response.get("status")
            if args.include_raw_response:
                record["raw_response"] = response.get("raw_response")
            if not record["contexts"]:
                record["warning"] = "Nenhum contexto recuperado retornado pelo chatbot."
        except Exception as exc:  # pragma: no cover - depende do ambiente RAG/HTTP
            record["error"] = f"{type(exc).__name__}: {exc}"
        records.append(record)
        if args.sleep_seconds > 0 and index < len(rows):
            time.sleep(args.sleep_seconds)
    return records


def write_jsonl(records: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_csv(records: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_SUMMARY_COLUMNS)
        writer.writeheader()
        for record in records:
            sources = record.get("retrieved_sources") or []
            writer.writerow(
                {
                    "id": record.get("id"),
                    "categoria": record.get("categoria"),
                    "question": record.get("question"),
                    "answer": record.get("answer"),
                    "ground_truth": record.get("ground_truth"),
                    "context_count": len(record.get("contexts") or []),
                    "source_count": len(sources),
                    "retrieved_document_ids": join_unique(source.get("document_id") for source in sources),
                    "retrieved_document_titles": join_unique(
                        source.get("document_title") for source in sources
                    ),
                    "documentos_esperados": record.get("documentos_esperados"),
                    "escopo_esperado": record.get("escopo_esperado"),
                    "mistura_permitida": record.get("mistura_permitida"),
                    "referencia_esperada": record.get("referencia_esperada"),
                    "deve_responder": record.get("deve_responder"),
                    "observacao": record.get("observacao"),
                    "error": record.get("error"),
                    "warning": record.get("warning"),
                }
            )


def join_unique(values: Any) -> str:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return " | ".join(result)


def print_summary(records: list[dict[str, Any]], jsonl_path: Path, csv_path: Path) -> None:
    total = len(records)
    errors = sum(1 for record in records if record.get("error"))
    no_contexts = sum(1 for record in records if not record.get("contexts"))
    no_mixing = sum(
        1 for record in records if str(record.get("mistura_permitida", "")).strip().lower() == "não"
    )
    should_not_answer = sum(
        1 for record in records if str(record.get("deve_responder", "")).strip().lower() == "não"
    )
    print()
    print(f"Total de perguntas: {total}")
    print(f"Processadas com sucesso: {total - errors}")
    print(f"Com erro: {errors}")
    print(f"Sem contextos recuperados: {no_contexts}")
    print(f"Perguntas com mistura_permitida = não: {no_mixing}")
    print(f"Perguntas com deve_responder = não: {should_not_answer}")
    print(f"Arquivo JSONL salvo em: {jsonl_path}")
    print(f"Arquivo CSV salvo em: {csv_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Executa perguntas de avaliação no chatbot RAG e gera JSONL/CSV."
    )
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--endpoint", help="Endpoint HTTP opcional do chatbot, ex.: http://localhost:8000/api/chat")
    parser.add_argument("--output-jsonl", required=True, type=Path)
    parser.add_argument("--output-csv", required=True, type=Path)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--sleep-seconds", type=float, default=0.0)
    parser.add_argument("--model")
    parser.add_argument("--temperature", type=float, default=0.1)
    parser.add_argument("--max-output-tokens", type=int, default=1200)
    parser.add_argument(
        "--context-mode",
        choices=["prompt", "chunks", "cited"],
        default="prompt",
        help=(
            "`prompt` salva os contextos consolidados enviados ao modelo; "
            "`chunks` salva cada chunk interno expandido; "
            "`cited` salva apenas contextos cujas fontes aparecem na resposta final."
        ),
    )
    parser.add_argument("--include-raw-response", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        records = run_questions(args)
    except Exception as exc:
        print(f"Falha ao preparar execução: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    write_jsonl(records, args.output_jsonl)
    write_csv(records, args.output_csv)
    print_summary(records, args.output_jsonl, args.output_csv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
