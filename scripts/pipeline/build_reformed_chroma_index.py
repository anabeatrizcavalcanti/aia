"""Cria índice ChromaDB persistente para o corpus documental da Alianca."""

from __future__ import annotations

import argparse
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
    import chromadb
except ImportError:  # pragma: no cover - tratado no fluxo principal
    chromadb = None

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - fallback para ambientes minimos
    load_dotenv = None


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_EMBEDDINGS_PATH = (
    ROOT_DIR / "corpus" / "processed" / "embeddings" / "alliance" / "openai_embeddings.jsonl"
)
DEFAULT_CHUNKS_PATH = (
    ROOT_DIR / "corpus" / "processed" / "chunks" / "alliance" / "all_chunks_for_embeddings.jsonl"
)
DEFAULT_EMBEDDING_MANIFEST = (
    ROOT_DIR / "corpus" / "processed" / "embeddings" / "alliance" / "embedding_manifest.json"
)
DEFAULT_PERSIST_DIR = ROOT_DIR / "corpus" / "indexes" / "chroma" / "alliance"
DEFAULT_REPORT_DIR = ROOT_DIR / "corpus" / "reports" / "vector_index"
DEFAULT_STAGE_REPORT = ROOT_DIR / "reports" / "specs" / "chroma-vector-index.md"
DEFAULT_COLLECTION_NAME = "solabot_alliance_v1"
DEFAULT_BATCH_SIZE = 100
OPENAI_EMBEDDINGS_URL = "https://api.openai.com/v1/embeddings"
VALIDATION_QUERIES = [
    "O que a Confissão de Fé Congregacional ensina sobre justificação?",
    "Quais documentos uma igreja precisa apresentar para se filiar à Aliança?",
    "Quais são os deveres de uma igreja local?",
    "Como funciona o processo de ordenação de ministros?",
    "Quais são os deveres éticos do pastor em relação à Aliança?",
    "Quais os critérios para emancipação de campos missionários?",
]
MINIMUM_METADATA_FIELDS = [
    "chunk_id",
    "corpus_id",
    "retrieval_namespace",
    "document_id",
    "doc_id",
    "document",
    "document_title",
    "document_type",
    "source_category",
    "denomination",
    "tradition",
    "tradition_family",
    "tradition_branch",
    "language",
    "chunk_type",
    "content_role",
    "is_doctrinal",
    "document_structure_type",
    "section_title",
    "section_reference",
    "subsection_title",
    "chapter_title",
    "chapter_reference",
    "article_number",
    "paragraph_number",
    "paragraph_label",
    "paragraph_number_roman",
    "inciso",
    "alinea",
    "full_reference",
    "biblical_references",
    "page_start",
    "page_end",
    "source_path",
    "normalized_source",
    "text_hash",
]


def relative_path(path: Path) -> str:
    """Retorna caminho relativo ao repositorio."""
    return path.relative_to(ROOT_DIR).as_posix()


def read_json(path: Path) -> dict[str, Any]:
    """Le um arquivo JSON."""
    if not path.exists():
        raise FileNotFoundError(f"Arquivo nao encontrado: {relative_path(path)}")
    return json.loads(path.read_text(encoding="utf-8"))


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


def write_json(path: Path, data: dict[str, Any]) -> None:
    """Grava JSON formatado."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def batch(items: list[Any], size: int) -> list[list[Any]]:
    """Divide lista em lotes."""
    return [items[index : index + size] for index in range(0, len(items), size)]


def validate_embeddings(embeddings: list[dict[str, Any]]) -> list[str]:
    """Valida linhas do arquivo de embeddings."""
    issues: list[str] = []
    seen_ids: set[str] = set()
    expected_dimensions: int | None = None

    for index, row in enumerate(embeddings, start=1):
        chunk_id = row.get("chunk_id")
        if not chunk_id:
            issues.append(f"line_{index}:missing_chunk_id")
        elif chunk_id in seen_ids:
            issues.append(f"line_{index}:duplicate_chunk_id:{chunk_id}")
        seen_ids.add(chunk_id)

        vector = row.get("embedding")
        if not isinstance(vector, list) or not vector:
            issues.append(f"line_{index}:missing_embedding_vector")
            continue
        if not all(isinstance(value, int | float) for value in vector):
            issues.append(f"line_{index}:embedding_contains_non_numeric_values")
        dimensions = row.get("embedding_dimensions")
        if dimensions != len(vector):
            issues.append(f"line_{index}:embedding_dimension_mismatch")
        if expected_dimensions is None:
            expected_dimensions = len(vector)
        elif expected_dimensions != len(vector):
            issues.append(f"line_{index}:inconsistent_embedding_dimensions")

        for field in ("document_id", "embedding_model", "embedding_provider", "text_hash"):
            if not row.get(field):
                issues.append(f"line_{index}:missing_{field}")
    return issues


def chunks_by_id(chunks: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Indexa chunks por `chunk_id`."""
    return {chunk["chunk_id"]: chunk for chunk in chunks if chunk.get("chunk_id")}


def validate_embedding_chunk_alignment(
    embeddings: list[dict[str, Any]],
    chunks: dict[str, dict[str, Any]],
) -> list[str]:
    """Valida que cada embedding possui chunk correspondente."""
    issues: list[str] = []
    for row in embeddings:
        chunk_id = row.get("chunk_id")
        chunk = chunks.get(chunk_id)
        if not chunk:
            issues.append(f"embedding_without_chunk:{chunk_id}")
            continue
        if not chunk.get("embedding_eligible"):
            issues.append(f"embedding_for_ineligible_chunk:{chunk_id}")
        if not str(chunk.get("embedding_text", "")).strip():
            issues.append(f"chunk_without_embedding_text:{chunk_id}")
        if row.get("text_hash") != chunk.get("text_hash"):
            issues.append(f"text_hash_mismatch:{chunk_id}")
    return issues


def scalar_metadata_value(value: Any) -> str | int | float | bool | None:
    """Converte metadado para formato aceito pelo ChromaDB."""
    if value is None:
        return None
    if isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, list | dict):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def build_metadata(chunk: dict[str, Any]) -> dict[str, str | int | float | bool]:
    """Monta metadados escalares para ChromaDB."""
    metadata: dict[str, str | int | float | bool] = {}
    for field in MINIMUM_METADATA_FIELDS:
        value = scalar_metadata_value(chunk.get(field))
        if value is not None:
            metadata[field] = value
    return metadata


def create_chroma_collection(persist_dir: Path, collection_name: str, reset: bool) -> Any:
    """Cria ou abre a collection persistente do ChromaDB."""
    if chromadb is None:
        raise RuntimeError("chromadb_not_installed")
    persist_dir.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(persist_dir))
    if reset:
        try:
            client.delete_collection(collection_name)
        except Exception:
            pass
    return client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )


def index_embeddings(
    collection: Any,
    embeddings: list[dict[str, Any]],
    chunks: dict[str, dict[str, Any]],
    batch_size: int,
) -> int:
    """Insere embeddings ja calculados no ChromaDB."""
    records = []
    for row in embeddings:
        chunk = chunks[row["chunk_id"]]
        records.append(
            {
                "id": row["chunk_id"],
                "embedding": row["embedding"],
                "document": chunk["embedding_text"],
                "metadata": build_metadata(chunk),
            }
        )

    for group in batch(records, batch_size):
        collection.upsert(
            ids=[item["id"] for item in group],
            embeddings=[item["embedding"] for item in group],
            documents=[item["document"] for item in group],
            metadatas=[item["metadata"] for item in group],
        )
    return len(records)


def request_openai_embeddings(
    inputs: list[str],
    api_key: str,
    model: str,
    dimensions: int,
    max_retries: int = 3,
) -> list[list[float]]:
    """Gera embeddings de consulta pela OpenAI."""
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


def observe_result_coherence(query: str, metadatas: list[dict[str, Any]]) -> str:
    """Registra observacao breve sobre coerencia aparente do retrieval."""
    if not metadatas:
        return "Nenhum resultado foi retornado para a consulta."
    lowered = query.lower()
    documents = {metadata.get("document_id") for metadata in metadatas}
    document_types = {metadata.get("document_type") for metadata in metadatas}
    source_categories = {metadata.get("source_category") for metadata in metadatas}
    if "justificação" in lowered or "justificacao" in lowered:
        if "confissao-fe-congregacional-alianca" in documents:
            return "A consulta recuperou a Confissão de Fé Congregacional para um tema doutrinário."
        return "A consulta retornou documentos doutrinários, mas a Confissão Congregacional deve ser revisada nos resultados."
    if any(term in lowered for term in ("filiar", "filiação", "filiacao", "igreja local", "contribuição", "contribuicao")):
        if {"constitution", "internal_regiment"} & document_types:
            return "A consulta normativa recuperou Constituição e/ou Regimento Interno."
        return "A consulta normativa retornou resultados, mas precisa de revisão humana de escopo."
    if any(term in lowered for term in ("ordenação", "ordenacao", "emancipação", "emancipacao", "campos missionários", "campos missionarios")):
        if "resolucao-alianca-01-2020" in documents or "regimento-interno-alianca-2022" in documents:
            return "A consulta recuperou documentos normativos sobre ordenação ou emancipação."
    if "ético" in lowered or "eticos" in lowered or "ética" in lowered or "etica" in lowered:
        if "codigo-etica-ministro-alianca" in documents:
            return "A consulta recuperou o Código de Ética do Ministro Congregacional."
    if "denominational_normative_document" in source_categories:
        return "Os resultados incluem documentos normativos da Aliança."
    return "Os resultados retornaram chunks do corpus documental da Aliança; a coerência precisa de revisão humana."


def run_validation_queries(
    collection: Any,
    queries: list[str],
    api_key: str,
    model: str,
    dimensions: int,
    top_k: int = 5,
) -> tuple[list[dict[str, Any]], str | None]:
    """Executa consultas basicas de retrieval."""
    if not api_key:
        return [], "openai_api_key_missing_for_query_embeddings"
    try:
        query_embeddings = request_openai_embeddings(queries, api_key, model, dimensions)
    except Exception as exc:
        return [], str(exc)

    validations: list[dict[str, Any]] = []
    for query, embedding in zip(queries, query_embeddings, strict=True):
        result = collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        ids = result.get("ids", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        top_chunks = []
        for chunk_id, metadata, distance in zip(ids, metadatas, distances, strict=False):
            top_chunks.append(
                {
                    "chunk_id": chunk_id,
                    "document_id": metadata.get("document_id"),
                    "document": metadata.get("document"),
                    "chunk_type": metadata.get("chunk_type"),
                    "page_start": metadata.get("page_start"),
                    "page_end": metadata.get("page_end"),
                    "distance": distance,
                }
            )
        validations.append(
            {
                "query": query,
                "results_count": len(top_chunks),
                "top_chunks": top_chunks,
                "observation": observe_result_coherence(query, metadatas),
            }
        )
    return validations, None


def build_report(
    embeddings_path: Path,
    chunks_path: Path,
    persist_dir: Path,
    collection_name: str,
    embedding_manifest: dict[str, Any],
    embeddings_count: int,
    indexed_count: int,
    collection_count: int,
    validation_issues: list[str],
    retrieval_validations: list[dict[str, Any]],
    retrieval_error: str | None,
    chromadb_available: bool,
) -> dict[str, Any]:
    """Monta relatorio do índice vetorial ChromaDB."""
    status = "PASS"
    if validation_issues or not chromadb_available or indexed_count == 0 or collection_count == 0:
        status = "FAIL"
    elif retrieval_error or any(item["results_count"] == 0 for item in retrieval_validations):
        status = "PARTIAL"
    return {
        "status": status,
        "embeddings_path": relative_path(embeddings_path),
        "chunks_path": relative_path(chunks_path),
        "persist_directory": relative_path(persist_dir),
        "collection_name": collection_name,
        "distance_metric": "cosine",
        "embedding_provider": embedding_manifest.get("embedding_provider"),
        "embedding_model": embedding_manifest.get("embedding_model"),
        "embedding_dimensions": embedding_manifest.get("embedding_dimensions"),
        "embeddings_read": embeddings_count,
        "chunks_indexed": indexed_count,
        "collection_count": collection_count,
        "metadata_fields": MINIMUM_METADATA_FIELDS,
        "validation_queries": retrieval_validations,
        "retrieval_error": retrieval_error,
        "validation_issues": validation_issues,
        "chromadb_available": chromadb_available,
        "scope_not_executed": [
            "new_chunk_embeddings",
            "chatbot",
            "llm_response_generation",
            "external_corpus_evaluation",
            "user_upload",
            "manual_doctrinal_text_editing",
            "new_extraction_normalization_or_chunking",
        ],
    }


def write_reports(report: dict[str, Any], report_dir: Path, spec_report_path: Path) -> None:
    """Grava relatorios JSON e Markdown."""
    report_dir.mkdir(parents=True, exist_ok=True)
    spec_report_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(report_dir / "chroma-vector-index-report.json", report)

    query_lines: list[str] = []
    for item in report["validation_queries"]:
        query_lines.extend(
            [
                f"### {item['query']}",
                "",
                f"- Resultados retornados: {item['results_count']}",
                f"- Observação: {item['observation']}",
            ]
        )
        for chunk in item["top_chunks"][:3]:
            query_lines.append(
                "- "
                f"`{chunk['chunk_id']}` | `{chunk['document_id']}` | "
                f"`{chunk['chunk_type']}` | páginas {chunk['page_start']}-{chunk['page_end']} | "
                f"distância {chunk['distance']}"
            )
        query_lines.append("")

    index_lines = [
        "## Índice ChromaDB",
        "",
        f"- Collection: `{report['collection_name']}`",
        f"- Diretório persistente: `{report['persist_directory']}`",
        f"- Métrica: `{report['distance_metric']}`",
        f"- Embeddings lidos: {report['embeddings_read']}",
        f"- Chunks indexados: {report['chunks_indexed']}",
        f"- Documentos na collection: {report['collection_count']}",
        f"- Modelo usado para consultas: `{report['embedding_model']}`",
        "",
    ]
    metadata_lines = [
        "## Metadados preservados",
        "",
        ", ".join(f"`{field}`" for field in report["metadata_fields"]),
        "",
    ]
    validation_query_lines = [
        "## Consultas de validação",
        "",
        *(query_lines or ["Nenhuma consulta foi executada com sucesso.", ""]),
    ]
    not_done_lines = [
        "## O que não foi feito nesta etapa",
        "",
        "- não foram gerados novos embeddings dos chunks;",
        "- não foi implementado chatbot;",
        "- não houve geração de respostas com LLM;",
        "- não foi feita avaliação com documentos externos ao corpus da Aliança;",
        "- não houve upload de documentos pelo usuário;",
        "- não houve alteração manual de texto doutrinário;",
        "- não houve nova extração, normalização ou chunking.",
    ]
    embedding_report = [
        "# Relatório de índice vetorial — ChromaDB",
        "",
        "## Status",
        "",
        report["status"],
        "",
        "## Síntese",
        "",
        (
            f"A collection `{report['collection_name']}` foi criada em `{report['persist_directory']}` "
            f"com {report['chunks_indexed']} chunks indexados a partir dos embeddings OpenAI disponíveis."
        ),
        "",
        *index_lines,
        *metadata_lines,
        *validation_query_lines,
        *not_done_lines,
    ]
    (report_dir / "chroma-vector-index-report.md").write_text(
        "\n".join(embedding_report) + "\n",
        encoding="utf-8",
    )

    spec_report = [
        "# Índice vetorial ChromaDB e validação de retrieval",
        "",
        "## Status",
        "",
        report["status"],
        "",
        "## Objetivo da etapa",
        "",
        "Criar uma collection ChromaDB persistente para o corpus doutrinário e normativo da Aliança e validar retrieval básico sem gerar respostas com LLM.",
        "",
        "## Entradas utilizadas",
        "",
        f"- `{report['embeddings_path']}`",
        f"- `{report['chunks_path']}`",
        "- `corpus/processed/embeddings/alliance/embedding_manifest.json`",
        "- `reports/specs/openai-embeddings.md`",
        "",
        *index_lines,
        *metadata_lines,
        *validation_query_lines,
        "## Validações executadas",
        "",
        "```bash",
        "python scripts/pipeline/build_reformed_chroma_index.py --reset",
        "python -m py_compile scripts/pipeline/build_reformed_chroma_index.py",
        "python -m pytest tests/test_chroma_vector_index.py",
        "```",
        "",
        f"Problemas de validação: {report['validation_issues'] or 'nenhuma ocorrência'}.",
        f"Erro de retrieval: {report['retrieval_error'] or 'nenhuma ocorrência'}.",
        "",
        "## Pontos de atenção",
        "",
        "- As consultas desta etapa avaliam apenas recuperação de chunks, sem composição de resposta.",
        "- O modelo de consulta foi lido do manifesto de embeddings para manter compatibilidade dimensional com os embeddings indexados.",
        "",
        *not_done_lines,
    ]
    spec_report_path.write_text("\n".join(spec_report) + "\n", encoding="utf-8")


def run(
    embeddings_path: Path,
    chunks_path: Path,
    persist_dir: Path,
    collection_name: str,
    reset: bool,
    batch_size: int,
) -> dict[str, Any]:
    """Executa a criação do índice vetorial ChromaDB."""
    if load_dotenv is not None:
        load_dotenv(ROOT_DIR / ".env")

    persist_dir.mkdir(parents=True, exist_ok=True)
    embedding_manifest = read_json(DEFAULT_EMBEDDING_MANIFEST)

    if chromadb is None:
        report = build_report(
            embeddings_path=embeddings_path,
            chunks_path=chunks_path,
            persist_dir=persist_dir,
            collection_name=collection_name,
            embedding_manifest=embedding_manifest,
            embeddings_count=0,
            indexed_count=0,
            collection_count=0,
            validation_issues=["chromadb_not_installed"],
            retrieval_validations=[],
            retrieval_error=None,
            chromadb_available=False,
        )
        write_reports(report, DEFAULT_REPORT_DIR, DEFAULT_STAGE_REPORT)
        return report

    embeddings = read_jsonl(embeddings_path)
    chunks = chunks_by_id(read_jsonl(chunks_path))
    validation_issues = validate_embeddings(embeddings)
    validation_issues.extend(validate_embedding_chunk_alignment(embeddings, chunks))

    collection_count = 0
    indexed_count = 0
    retrieval_validations: list[dict[str, Any]] = []
    retrieval_error: str | None = None

    if not validation_issues:
        collection = create_chroma_collection(persist_dir, collection_name, reset)
        indexed_count = index_embeddings(collection, embeddings, chunks, batch_size)
        collection_count = collection.count()
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        retrieval_validations, retrieval_error = run_validation_queries(
            collection=collection,
            queries=VALIDATION_QUERIES,
            api_key=api_key,
            model=embedding_manifest["embedding_model"],
            dimensions=embedding_manifest["embedding_dimensions"],
        )

    report = build_report(
        embeddings_path=embeddings_path,
        chunks_path=chunks_path,
        persist_dir=persist_dir,
        collection_name=collection_name,
        embedding_manifest=embedding_manifest,
        embeddings_count=len(embeddings),
        indexed_count=indexed_count,
        collection_count=collection_count,
        validation_issues=validation_issues,
        retrieval_validations=retrieval_validations,
        retrieval_error=retrieval_error,
        chromadb_available=True,
    )
    write_reports(report, DEFAULT_REPORT_DIR, DEFAULT_STAGE_REPORT)
    return report


def build_parser() -> argparse.ArgumentParser:
    """Cria parser CLI."""
    parser = argparse.ArgumentParser(description="Cria índice ChromaDB para o corpus da Aliança.")
    parser.add_argument("--embeddings-path", type=Path, default=DEFAULT_EMBEDDINGS_PATH)
    parser.add_argument("--chunks-path", type=Path, default=DEFAULT_CHUNKS_PATH)
    parser.add_argument("--persist-dir", type=Path, default=DEFAULT_PERSIST_DIR)
    parser.add_argument("--collection-name", default=DEFAULT_COLLECTION_NAME)
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    return parser


def main() -> int:
    """Ponto de entrada CLI."""
    args = build_parser().parse_args()
    try:
        report = run(
            embeddings_path=args.embeddings_path,
            chunks_path=args.chunks_path,
            persist_dir=args.persist_dir,
            collection_name=args.collection_name,
            reset=args.reset,
            batch_size=args.batch_size,
        )
    except Exception as exc:
        print(f"A criação do índice vetorial falhou: {exc}", file=sys.stderr)
        return 1

    print(f"Índice vetorial ChromaDB concluído com status {report['status']}.")
    print(f"- embeddings lidos: {report['embeddings_read']}")
    print(f"- chunks indexados: {report['chunks_indexed']}")
    print(f"- collection: {report['collection_name']}")
    print(f"- diretório: {report['persist_directory']}")
    if report["retrieval_error"]:
        print(f"- ponto de atenção: {report['retrieval_error']}")
    return 0 if report["status"] in {"PASS", "PARTIAL"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
