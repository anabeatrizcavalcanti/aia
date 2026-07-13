"""Consulta o retriever híbrido do corpus reformado."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from sola_bot.retrieval.bm25_retriever import BM25Retriever, BM25RetrieverError  # noqa: E402
from sola_bot.retrieval.hybrid_retriever import HybridRetriever  # noqa: E402
from sola_bot.retrieval.query_embedder import QueryEmbeddingError  # noqa: E402
from sola_bot.retrieval.vector_retriever import DEFAULT_FILTERS, VectorRetrieverError  # noqa: E402


REPORT_DIR = ROOT_DIR / "corpus" / "reports" / "retrieval"
SPEC_DOC = ROOT_DIR / "specs" / "hybrid-retrieval.md"
STAGE_REPORT = ROOT_DIR / "reports" / "specs" / "hybrid-retrieval.md"
TECHNICAL_REPORT_MD = REPORT_DIR / "hybrid-retrieval-report.md"
TECHNICAL_REPORT_JSON = REPORT_DIR / "hybrid-retrieval-report.json"
DEFAULT_TOP_K = 5
DEFAULT_VECTOR_K = 20
DEFAULT_BM25_K = 20
DEFAULT_RRF_K = 60
DEFAULT_BM25_TEXT_FIELD = "embedding_text"
VALIDATION_QUERIES = [
    "O que é o batismo?",
    "O que é necessário para a salvação?",
    "O que é eleição?",
    "O que é justificação?",
    "O que a tradição reformada ensina sobre as Escrituras?",
    "O crente pode perder a salvação?",
    "O que é regeneração?",
    "O que é expiação?",
]
REQUIRED_INPUTS = [
    ROOT_DIR / "reports" / "specs" / "vector-retrieval.md",
    ROOT_DIR / "corpus" / "reports" / "retrieval" / "vector-retrieval-report.md",
    ROOT_DIR / "corpus" / "reports" / "retrieval" / "vector-retrieval-report.json",
    ROOT_DIR / "corpus" / "processed" / "chunks" / "reformed" / "all_chunks_for_embeddings.jsonl",
    ROOT_DIR / "corpus" / "processed" / "embeddings" / "reformed" / "embedding_manifest.json",
    ROOT_DIR / "corpus" / "indexes" / "chroma" / "reformed",
]


def relative_path(path: Path) -> str:
    """Retorna caminho relativo à raiz do repositório."""
    return path.relative_to(ROOT_DIR).as_posix()


def compact_text(text: str, limit: int = 420) -> str:
    """Compacta texto para terminal e relatórios."""
    compacted = " ".join(text.split())
    if len(compacted) <= limit:
        return compacted
    return compacted[: limit - 3].rstrip() + "..."


def format_pages(result: Any) -> str:
    """Formata páginas de um resultado."""
    if result.page_start is None and result.page_end is None:
        return "não informado"
    if result.page_end is None or result.page_start == result.page_end:
        return str(result.page_start)
    return f"{result.page_start}-{result.page_end}"


def format_section(result: Any) -> str:
    """Monta descrição curta de capítulo/seção."""
    parts = [
        result.chapter_title or result.chapter_reference,
        result.section_title,
        result.section_reference,
    ]
    return " | ".join(part for part in parts if part) or "sem seção informada"


def ranking_scores(result: Any) -> dict[str, float | None]:
    """Extrai pontuações vetorial e BM25 dos metadados do RRF."""
    vector_score = result.metadata.get("vector_score")
    vector_distance = result.metadata.get("vector_distance")
    bm25_score = result.metadata.get("bm25_score")
    for item in result.metadata.get("source_rankings", []):
        if item.get("source") == "vector":
            vector_score = item.get("original_score")
            vector_distance = item.get("distance")
        if item.get("source") == "bm25":
            bm25_score = item.get("original_score")
    return {
        "vector_score": vector_score,
        "vector_distance": vector_distance,
        "bm25_score": bm25_score,
    }


def result_to_report_row(result: Any) -> dict[str, Any]:
    """Converte um resultado híbrido para linha de relatório."""
    scores = ranking_scores(result)
    return {
        "chunk_id": result.chunk_id,
        "document_id": result.document_id,
        "document": result.document,
        "chunk_type": result.chunk_type,
        "content_role": result.content_role,
        "section_title": result.section_title,
        "section_reference": result.section_reference,
        "chapter_title": result.chapter_title,
        "chapter_reference": result.chapter_reference,
        "page_start": result.page_start,
        "page_end": result.page_end,
        "source_path": result.source_path,
        "text_hash": result.text_hash,
        "rrf_score": result.score,
        "vector_score": scores["vector_score"],
        "vector_distance": scores["vector_distance"],
        "bm25_score": scores["bm25_score"],
        "retrieval_sources": result.metadata.get("retrieval_sources", []),
        "text_preview": compact_text(result.text),
    }


def build_filters(document_id: str | None, chunk_type: str | None) -> dict[str, str] | None:
    """Monta filtros opcionais sem duplicar os filtros obrigatórios."""
    filters: dict[str, str] = {}
    if document_id:
        filters["document_id"] = document_id
    if chunk_type:
        filters["chunk_type"] = chunk_type
    return filters or None


def run_single_query(args: argparse.Namespace) -> list[Any]:
    """Executa uma consulta híbrida."""
    check_runtime_requirements()
    retriever = HybridRetriever(
        vector_candidate_k=args.vector_k,
        bm25_candidate_k=args.bm25_k,
        rrf_k=args.rrf_k,
        final_top_k=args.top_k,
        bm25_text_field=args.bm25_text_field,
    )
    return retriever.retrieve(
        query=args.query,
        top_k=args.top_k,
        filters=build_filters(args.document_id, args.chunk_type),
    )


def print_results(query: str, results: list[Any]) -> None:
    """Imprime resultados no terminal."""
    print(f"Pergunta: {query}")
    print(f"Resultados retornados: {len(results)}")
    print(f"Filtros obrigatórios: {DEFAULT_FILTERS}")
    print()
    for index, result in enumerate(results, start=1):
        scores = ranking_scores(result)
        print(f"{index}. {result.document} ({result.document_id})")
        print(f"   Chunk: {result.chunk_id}")
        print(f"   Tipo: {result.chunk_type}")
        print(f"   Fontes de retrieval: {', '.join(result.metadata.get('retrieval_sources', []))}")
        print(f"   Score RRF: {result.score}")
        print(f"   Distância vetorial: {scores['vector_distance']}")
        print(f"   Score BM25: {scores['bm25_score']}")
        print(f"   Seção: {format_section(result)}")
        print(f"   Páginas: {format_pages(result)}")
        print(f"   Fonte: {result.source_path}")
        print(f"   Trecho: {compact_text(result.text, limit=360)}")
        print()


def dependency_status() -> dict[str, bool]:
    """Retorna dependências disponíveis para execução real."""
    if load_dotenv is not None:
        load_dotenv(ROOT_DIR / ".env")
    return {
        "rank_bm25_available": importlib.util.find_spec("rank_bm25") is not None,
        "chromadb_available": importlib.util.find_spec("chromadb") is not None,
        "openai_api_key_configured": bool(os.getenv("OPENAI_API_KEY", "").strip()),
    }


def check_runtime_requirements() -> None:
    """Valida dependências necessárias para consulta híbrida real."""
    status = dependency_status()
    if not status["rank_bm25_available"]:
        raise BM25RetrieverError(
            "rank-bm25 não está instalado. Instale a dependência para executar a busca lexical BM25."
        )
    if not status["chromadb_available"]:
        raise VectorRetrieverError("chromadb não está instalado neste ambiente.")
    if not status["openai_api_key_configured"]:
        raise QueryEmbeddingError("OPENAI_API_KEY não está configurada.")


def missing_required_inputs() -> list[str]:
    """Lista entradas obrigatórias ausentes."""
    return [relative_path(path) for path in REQUIRED_INPUTS if not path.exists()]


def get_bm25_chunks_loaded() -> int | None:
    """Conta chunks carregados pelo BM25 quando a dependência está disponível."""
    try:
        return len(BM25Retriever().chunks)
    except BM25RetrieverError:
        return None


def run_validation_report(args: argparse.Namespace) -> dict[str, Any]:
    """Executa consultas de validação e grava relatórios."""
    status = dependency_status()
    missing_inputs = missing_required_inputs()
    validations: list[dict[str, Any]] = []
    retrieval_error: str | None = None
    bm25_chunks_loaded = get_bm25_chunks_loaded() if status["rank_bm25_available"] else None

    if missing_inputs:
        retrieval_error = "Entradas obrigatórias ausentes: " + ", ".join(missing_inputs)
    elif not status["rank_bm25_available"]:
        retrieval_error = "rank-bm25 não está instalado; a etapa ficou limitada aos arquivos e validações estáticas."
    elif not status["chromadb_available"]:
        retrieval_error = "chromadb não está instalado; não foi possível consultar o índice vetorial."
    elif not status["openai_api_key_configured"]:
        retrieval_error = "OPENAI_API_KEY não está configurada; a rota vetorial não foi chamada."
    else:
        try:
            retriever = HybridRetriever(
                vector_candidate_k=args.vector_k,
                bm25_candidate_k=args.bm25_k,
                rrf_k=args.rrf_k,
                final_top_k=args.top_k,
                bm25_text_field=args.bm25_text_field,
            )
            bm25_chunks_loaded = len(retriever.bm25_retriever.chunks)
            for query in VALIDATION_QUERIES:
                results = retriever.retrieve(query=query, top_k=args.top_k)
                rows = [result_to_report_row(result) for result in results]
                validations.append(
                    {
                        "query": query,
                        "vector_candidate_k": args.vector_k,
                        "bm25_candidate_k": args.bm25_k,
                        "final_top_k": args.top_k,
                        "rrf_k": args.rrf_k,
                        "results_count": len(rows),
                        "documents": sorted({row["document_id"] for row in rows}),
                        "chunk_types": sorted({row["chunk_type"] for row in rows}),
                        "results": rows,
                    }
                )
        except (BM25RetrieverError, VectorRetrieverError, QueryEmbeddingError, Exception) as exc:
            retrieval_error = str(exc)

    result_rows = [row for item in validations for row in item["results"]]
    documents_counter = Counter(row["document_id"] for row in result_rows)
    chunk_types_counter = Counter(row["chunk_type"] for row in result_rows)
    report_status = "PASS"
    if missing_inputs or (retrieval_error and status["rank_bm25_available"] and status["chromadb_available"]):
        report_status = "FAIL" if missing_inputs else "PARTIAL"
    if retrieval_error or not validations:
        report_status = "PARTIAL" if not missing_inputs else "FAIL"

    report = {
        "status": report_status,
        "configuration": {
            "vector_candidate_k": args.vector_k,
            "bm25_candidate_k": args.bm25_k,
            "final_top_k": args.top_k,
            "rrf_k": args.rrf_k,
            "bm25_text_field": args.bm25_text_field,
            "default_filters": DEFAULT_FILTERS,
        },
        "dependency_status": status,
        "missing_required_inputs": missing_inputs,
        "retrieval_error": retrieval_error,
        "bm25_implementation": "rank-bm25 / BM25Okapi",
        "bm25_chunks_loaded": bm25_chunks_loaded,
        "validation_queries": validations,
        "most_retrieved_documents": dict(documents_counter.most_common()),
        "most_retrieved_chunk_types": dict(chunk_types_counter.most_common()),
        "scope_not_executed": [
            "final_chatbot",
            "llm_answer_generation",
            "openai_chat_model_call",
            "other_traditions_evaluation",
            "user_upload",
            "chunk_embedding_pdf_change",
            "new_extraction_normalization_chunking_or_indexing",
            "neural_reranking",
            "parent_hierarchical_retrieval",
        ],
    }
    write_reports(report)
    return report


def write_reports(report: dict[str, Any]) -> None:
    """Grava relatórios técnico e da etapa."""
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    STAGE_REPORT.parent.mkdir(parents=True, exist_ok=True)
    SPEC_DOC.parent.mkdir(parents=True, exist_ok=True)

    TECHNICAL_REPORT_JSON.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    query_summary_lines = render_query_summary_lines(report)
    query_detail_lines = render_query_detail_lines(report)
    dependency_lines = [
        f"- Dependências: `{report['dependency_status']}`.",
        f"- Entradas ausentes: `{report['missing_required_inputs']}`.",
    ]
    if not report["dependency_status"].get("rank_bm25_available"):
        dependency_lines.append("- `rank-bm25` ausente; a busca lexical não foi executada.")
    if report["retrieval_error"]:
        dependency_lines.append(f"- Bloqueio registrado: {report['retrieval_error']}")

    technical_lines = [
        "# Relatório de retrieval híbrido",
        "",
        "## Status",
        "",
        report["status"],
        "",
        "## Parâmetros",
        "",
        f"- Vector candidate k: `{report['configuration']['vector_candidate_k']}`",
        f"- BM25 candidate k: `{report['configuration']['bm25_candidate_k']}`",
        f"- Final top-k: `{report['configuration']['final_top_k']}`",
        f"- RRF k: `{report['configuration']['rrf_k']}`",
        f"- Campo lexical BM25: `{report['configuration']['bm25_text_field']}`",
        f"- Filtros padrão: `{report['configuration']['default_filters']}`",
        "",
        "## Arquivos e índices",
        "",
        "- Chunks: `corpus/processed/chunks/reformed/all_chunks_for_embeddings.jsonl`.",
        "- Índice ChromaDB: `corpus/indexes/chroma/reformed/`.",
        "- Collection: `solabot_reformed_v1`.",
        f"- BM25: `rank-bm25` / `BM25Okapi`, `{report['bm25_chunks_loaded']}` chunks carregados.",
        "- Modelo de embedding da pergunta: `text-embedding-3-large`.",
        "",
        "## Consultas",
        "",
        *(query_detail_lines or ["As consultas não foram executadas nesta rodada.", ""]),
        "## Agregados",
        "",
        "Documentos:",
        "",
        json.dumps(report["most_retrieved_documents"], ensure_ascii=False, indent=2),
        "",
        "Tipos de chunk:",
        "",
        json.dumps(report["most_retrieved_chunk_types"], ensure_ascii=False, indent=2),
        "",
        "## Fora do escopo",
        "",
        "- Sem reranking neural.",
        "- Sem recuperação hierárquica de documentos-pai.",
        "- Sem geração de resposta com LLM.",
    ]
    TECHNICAL_REPORT_MD.write_text("\n".join(technical_lines) + "\n", encoding="utf-8")

    stage_lines = [
        "# Retrieval híbrido do corpus reformado",
        "",
        "## Status",
        "",
        report["status"],
        "",
        "## Entradas",
        "",
        "- `reports/specs/vector-retrieval.md`",
        "- `corpus/reports/retrieval/vector-retrieval-report.md`",
        "- `corpus/reports/retrieval/vector-retrieval-report.json`",
        "- `corpus/processed/chunks/reformed/all_chunks_for_embeddings.jsonl`",
        "- `corpus/processed/embeddings/reformed/embedding_manifest.json`",
        "- `corpus/indexes/chroma/reformed/`",
        "",
        "## Código",
        "",
        "- `src/sola_bot/retrieval/bm25_retriever.py`",
        "- `src/sola_bot/retrieval/rrf.py`",
        "- `src/sola_bot/retrieval/hybrid_retriever.py`",
        "- `scripts/pipeline/query_hybrid_retriever.py`",
        "",
        "## Configuração",
        "",
        f"- Vector candidate k: `{report['configuration']['vector_candidate_k']}`",
        f"- BM25 candidate k: `{report['configuration']['bm25_candidate_k']}`",
        f"- Final top-k: `{report['configuration']['final_top_k']}`",
        f"- RRF k: `{report['configuration']['rrf_k']}`",
        f"- BM25 text field: `{report['configuration']['bm25_text_field']}`",
        f"- Filtros: `{report['configuration']['default_filters']}`",
        "",
        "## Consultas",
        "",
        *(query_summary_lines or ["As consultas não foram executadas nesta rodada.", ""]),
        "## Agregados",
        "",
        f"- Documentos mais recuperados: `{report['most_retrieved_documents']}`",
        f"- Tipos de chunk mais recuperados: `{report['most_retrieved_chunk_types']}`",
        f"- Erro ou bloqueio: {report['retrieval_error'] or 'nenhuma ocorrência'}",
        "",
        "## Validações executadas",
        "",
        "```bash",
        'python scripts/pipeline/query_hybrid_retriever.py "O que é o batismo?" --top-k 5',
        'python scripts/pipeline/query_hybrid_retriever.py "O que é eleição?" --top-k 5',
        'python scripts/pipeline/query_hybrid_retriever.py "O que é justificação?" --top-k 5',
        "python scripts/pipeline/query_hybrid_retriever.py --write-report",
        "python -m py_compile src/sola_bot/retrieval/bm25_retriever.py",
        "python -m py_compile src/sola_bot/retrieval/rrf.py",
        "python -m py_compile src/sola_bot/retrieval/hybrid_retriever.py",
        "python -m py_compile scripts/pipeline/query_hybrid_retriever.py",
        "python -m pytest tests/test_hybrid_retriever.py",
        "```",
        "",
        "## Pontos de atenção",
        "",
        *dependency_lines,
        "",
        "## Fora do escopo",
        "",
        "- chatbot final",
        "- resposta com LLM",
        "- chamada a modelo de chat da OpenAI",
        "- avaliação com documentos de outras tradições",
        "- upload de documentos pelo usuário",
        "- alteração de chunks, embeddings ou PDFs",
        "- nova extração, normalização, chunking ou indexação",
        "- reranking neural",
        "- parent/hierarchical retrieval",
    ]
    STAGE_REPORT.write_text("\n".join(stage_lines) + "\n", encoding="utf-8")


def render_query_summary_lines(report: dict[str, Any]) -> list[str]:
    """Renderiza resumo das consultas em tabela Markdown."""
    if not report["validation_queries"]:
        return []
    lines = [
        "| Consulta | Resultados | Documentos | Tipos de chunk |",
        "| --- | ---: | --- | --- |",
    ]
    for item in report["validation_queries"]:
        lines.append(
            "| "
            f"{item['query']} | "
            f"{item['results_count']} | "
            f"{', '.join(item['documents']) or 'nenhum'} | "
            f"{', '.join(item['chunk_types']) or 'nenhum'} |"
        )
    lines.append("")
    return lines


def render_query_detail_lines(report: dict[str, Any]) -> list[str]:
    """Renderiza top resultados das consultas em tabelas Markdown."""
    lines: list[str] = []
    for item in report["validation_queries"]:
        lines.extend(
            [
                f"### {item['query']}",
                "",
                f"- Resultados: `{item['results_count']}`",
                f"- Documentos: `{', '.join(item['documents']) or 'nenhum'}`",
                "",
                "| Rank | Chunk | Documento | Tipo | Páginas | RRF |",
                "| ---: | --- | --- | --- | --- | ---: |",
            ]
        )
        for rank, row in enumerate(item["results"][:5], start=1):
            lines.append(
                "| "
                f"{rank} | "
                f"`{row['chunk_id']}` | "
                f"`{row['document_id']}` | "
                f"`{row['chunk_type']}` | "
                f"{row['page_start']}-{row['page_end']} | "
                f"{row['rrf_score']} |"
            )
        lines.extend(
            [
                "",
            ]
        )
    return lines


def build_parser() -> argparse.ArgumentParser:
    """Cria parser CLI."""
    parser = argparse.ArgumentParser(description="Consulta o retriever híbrido reformado.")
    parser.add_argument("query", nargs="?", help="Pergunta doutrinária a consultar.")
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    parser.add_argument("--vector-k", type=int, default=DEFAULT_VECTOR_K)
    parser.add_argument("--bm25-k", type=int, default=DEFAULT_BM25_K)
    parser.add_argument("--rrf-k", type=int, default=DEFAULT_RRF_K)
    parser.add_argument("--bm25-text-field", default=DEFAULT_BM25_TEXT_FIELD)
    parser.add_argument("--document-id")
    parser.add_argument("--chunk-type")
    parser.add_argument("--write-report", action="store_true")
    return parser


def main() -> int:
    """Ponto de entrada CLI."""
    args = build_parser().parse_args()

    if args.write_report:
        report = run_validation_report(args)
        print(f"Relatório de retrieval híbrido concluído com status {report['status']}.")
        print(f"- BM25 chunks carregados: {report['bm25_chunks_loaded']}")
        if report["retrieval_error"]:
            print(f"- ponto de atenção: {report['retrieval_error']}")
        return 0 if report["status"] in {"PASS", "PARTIAL"} else 1

    if not args.query:
        print("Informe uma pergunta ou use --write-report.", file=sys.stderr)
        return 2

    try:
        results = run_single_query(args)
    except (BM25RetrieverError, VectorRetrieverError, QueryEmbeddingError) as exc:
        print(f"A consulta híbrida não pôde ser executada: {exc}", file=sys.stderr)
        return 1

    print_results(args.query, results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
