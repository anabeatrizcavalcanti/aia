"""Consulta o retriever com reranking neural."""

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
except ImportError:  # pragma: no cover
    load_dotenv = None


ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from aia.retrieval.cross_encoder_reranker import (  # noqa: E402
    DEFAULT_MAX_TEXT_CHARS,
    DEFAULT_RERANKER_MODEL,
    CrossEncoderRerankerError,
)
from aia.retrieval.reranked_retriever import RerankedRetriever  # noqa: E402
from aia.retrieval.retrieval_result import RetrievalResult  # noqa: E402


REPORT_DIR = ROOT_DIR / "corpus" / "reports" / "retrieval"
STAGE_REPORT = ROOT_DIR / "reports" / "specs" / "reranker-retrieval.md"
TECHNICAL_REPORT_MD = REPORT_DIR / "reranker-retrieval-report.md"
TECHNICAL_REPORT_JSON = REPORT_DIR / "reranker-retrieval-report.json"
DEFAULT_TOP_K = 5
DEFAULT_HYBRID_K = 20
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
    ROOT_DIR / "reports" / "specs" / "hybrid-retrieval.md",
    ROOT_DIR / "corpus" / "reports" / "retrieval" / "hybrid-retrieval-report.md",
    ROOT_DIR / "corpus" / "reports" / "retrieval" / "hybrid-retrieval-report.json",
    ROOT_DIR / "corpus" / "processed" / "chunks" / "reformed" / "all_chunks_for_embeddings.jsonl",
    ROOT_DIR / "corpus" / "processed" / "embeddings" / "reformed" / "embedding_manifest.json",
    ROOT_DIR / "corpus" / "indexes" / "chroma" / "reformed",
    ROOT_DIR / "config" / "retrieval_config.example.yaml",
    ROOT_DIR / "requirements.txt",
]


def relative_path(path: Path) -> str:
    """Retorna caminho relativo à raiz do repositório."""
    return path.relative_to(ROOT_DIR).as_posix()


def compact_text(text: str, limit: int = 360) -> str:
    """Compacta texto para saída de terminal."""
    compacted = " ".join(text.split())
    if len(compacted) <= limit:
        return compacted
    return compacted[: limit - 3].rstrip() + "..."


def format_pages(result: RetrievalResult) -> str:
    """Formata páginas de um resultado."""
    if result.page_start is None and result.page_end is None:
        return "não informado"
    if result.page_end is None or result.page_start == result.page_end:
        return str(result.page_start)
    return f"{result.page_start}-{result.page_end}"


def format_section(result: RetrievalResult) -> str:
    """Formata capítulo/seção de um resultado."""
    parts = [
        result.chapter_title or result.chapter_reference,
        result.section_title,
        result.section_reference,
    ]
    return " | ".join(part for part in parts if part) or "não informado"


def build_filters(document_id: str | None, chunk_type: str | None) -> dict[str, str] | None:
    """Monta filtros adicionais."""
    filters: dict[str, str] = {}
    if document_id:
        filters["document_id"] = document_id
    if chunk_type:
        filters["chunk_type"] = chunk_type
    return filters or None


def dependency_status() -> dict[str, bool]:
    """Dependências necessárias para execução real."""
    if load_dotenv is not None:
        load_dotenv(ROOT_DIR / ".env")
    return {
        "sentence_transformers_available": importlib.util.find_spec("sentence_transformers") is not None,
        "rank_bm25_available": importlib.util.find_spec("rank_bm25") is not None,
        "chromadb_available": importlib.util.find_spec("chromadb") is not None,
        "openai_api_key_configured": bool(os.getenv("OPENAI_API_KEY", "").strip()),
    }


def missing_required_inputs() -> list[str]:
    """Lista entradas obrigatórias ausentes."""
    return [relative_path(path) for path in REQUIRED_INPUTS if not path.exists()]


def check_runtime_requirements() -> None:
    """Interrompe execução real quando dependências não estão disponíveis."""
    status = dependency_status()
    if not status["sentence_transformers_available"]:
        raise CrossEncoderRerankerError("sentence-transformers não está instalado.")
    if not status["rank_bm25_available"]:
        raise CrossEncoderRerankerError("rank-bm25 não está instalado.")
    if not status["chromadb_available"]:
        raise CrossEncoderRerankerError("chromadb não está instalado.")
    if not status["openai_api_key_configured"]:
        raise CrossEncoderRerankerError("OPENAI_API_KEY não está configurada.")


def result_to_row(result: RetrievalResult, final_rank: int) -> dict[str, Any]:
    """Converte resultado reranqueado para linha de relatório."""
    metadata = result.metadata
    pre_rank = metadata.get("pre_rerank_rank")
    rank_delta = None
    if isinstance(pre_rank, int):
        rank_delta = pre_rank - final_rank
    return {
        "final_rank": final_rank,
        "chunk_id": result.chunk_id,
        "document_id": result.document_id,
        "document": result.document,
        "chunk_type": result.chunk_type,
        "page_start": result.page_start,
        "page_end": result.page_end,
        "source_path": result.source_path,
        "text_hash": result.text_hash,
        "reranker_score": metadata.get("reranker_score"),
        "pre_rerank_rank": pre_rank,
        "pre_rerank_score": metadata.get("pre_rerank_score"),
        "pre_rerank_sources": metadata.get("pre_rerank_sources", []),
        "rank_delta": rank_delta,
        "text_preview": compact_text(result.text),
    }


def run_single_query(args: argparse.Namespace) -> list[RetrievalResult]:
    """Executa consulta com reranking."""
    check_runtime_requirements()
    retriever = RerankedRetriever(
        hybrid_candidate_k=args.hybrid_k,
        final_top_k=args.top_k,
        reranker_model=args.reranker_model,
        max_text_chars=args.max_text_chars,
    )
    return retriever.retrieve(
        query=args.query,
        top_k=args.top_k,
        filters=build_filters(args.document_id, args.chunk_type),
    )


def print_results(query: str, results: list[RetrievalResult], hybrid_k: int) -> None:
    """Imprime resultados no terminal."""
    print(f"Pergunta: {query}")
    print(f"Candidatos híbridos: {hybrid_k}")
    print(f"Resultados finais: {len(results)}")
    print()
    for rank, result in enumerate(results, start=1):
        metadata = result.metadata
        print(f"{rank}. {result.document} ({result.document_id})")
        print(f"   Chunk: {result.chunk_id}")
        print(f"   Tipo: {result.chunk_type}")
        print(f"   Rank antes: {metadata.get('pre_rerank_rank')}")
        print(f"   Score RRF antes: {metadata.get('pre_rerank_score')}")
        print(f"   Score reranker: {metadata.get('reranker_score')}")
        print(f"   Fontes antes: {metadata.get('pre_rerank_sources')}")
        print(f"   Capítulo/seção: {format_section(result)}")
        print(f"   Páginas: {format_pages(result)}")
        print(f"   Fonte: {result.source_path}")
        print(f"   Trecho: {compact_text(result.text)}")
        print()


def run_validation_report(args: argparse.Namespace) -> dict[str, Any]:
    """Executa consultas de validação e grava relatórios."""
    status = dependency_status()
    missing_inputs = missing_required_inputs()
    validations: list[dict[str, Any]] = []
    retrieval_error: str | None = None

    if missing_inputs:
        retrieval_error = "Entradas obrigatórias ausentes: " + ", ".join(missing_inputs)
    elif not status["sentence_transformers_available"]:
        retrieval_error = "sentence-transformers não está instalado."
    elif not status["rank_bm25_available"]:
        retrieval_error = "rank-bm25 não está instalado."
    elif not status["chromadb_available"]:
        retrieval_error = "chromadb não está instalado."
    elif not status["openai_api_key_configured"]:
        retrieval_error = "OPENAI_API_KEY não está configurada."
    else:
        try:
            retriever = RerankedRetriever(
                hybrid_candidate_k=args.hybrid_k,
                final_top_k=args.top_k,
                reranker_model=args.reranker_model,
                max_text_chars=args.max_text_chars,
            )
            filters = build_filters(args.document_id, args.chunk_type)
            for query in VALIDATION_QUERIES:
                candidates = retriever.hybrid_retriever.retrieve(
                    query=query,
                    top_k=args.hybrid_k,
                    filters=filters,
                )
                results = retriever.reranker.rerank(query=query, candidates=candidates, top_k=args.top_k)
                rows = [result_to_row(result, rank) for rank, result in enumerate(results, start=1)]
                validations.append(
                    {
                        "query": query,
                        "hybrid_candidate_k": args.hybrid_k,
                        "final_top_k": args.top_k,
                        "reranker_model": args.reranker_model,
                        "hybrid_candidates_count": len(candidates),
                        "results_count": len(rows),
                        "documents": sorted({row["document_id"] for row in rows}),
                        "chunk_types": sorted({row["chunk_type"] for row in rows}),
                        "results": rows,
                    }
                )
        except Exception as exc:
            retrieval_error = str(exc)

    result_rows = [row for item in validations for row in item["results"]]
    documents_counter = Counter(row["document_id"] for row in result_rows)
    chunk_types_counter = Counter(row["chunk_type"] for row in result_rows)
    ranking_changes = summarize_ranking_changes(result_rows)
    report_status = "PASS"
    if missing_inputs:
        report_status = "FAIL"
    elif retrieval_error or not validations:
        report_status = "PARTIAL"

    report = {
        "status": report_status,
        "configuration": {
            "hybrid_candidate_k": args.hybrid_k,
            "final_top_k": args.top_k,
            "reranker_model": args.reranker_model,
            "max_text_chars": args.max_text_chars,
            "default_filters": {
                "corpus_id": "reformed",
                "retrieval_namespace": "reformed_confessional",
            },
        },
        "dependency_status": status,
        "missing_required_inputs": missing_inputs,
        "retrieval_error": retrieval_error,
        "validation_queries": validations,
        "ranking_changes": ranking_changes,
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
            "parent_hierarchical_retrieval",
            "evidence_based_refusal_policy",
        ],
    }
    write_reports(report)
    return report


def summarize_ranking_changes(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Resume deslocamentos entre ranking híbrido e ranking final."""
    deltas = [row["rank_delta"] for row in rows if isinstance(row.get("rank_delta"), int)]
    if not deltas:
        return {
            "items_with_rank_delta": 0,
            "moved_up": 0,
            "moved_down": 0,
            "unchanged": 0,
            "max_position_gain": None,
            "max_position_loss": None,
        }
    return {
        "items_with_rank_delta": len(deltas),
        "moved_up": sum(1 for delta in deltas if delta > 0),
        "moved_down": sum(1 for delta in deltas if delta < 0),
        "unchanged": sum(1 for delta in deltas if delta == 0),
        "max_position_gain": max(deltas),
        "max_position_loss": min(deltas),
    }


def write_reports(report: dict[str, Any]) -> None:
    """Grava relatórios Markdown e JSON."""
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    STAGE_REPORT.parent.mkdir(parents=True, exist_ok=True)
    TECHNICAL_REPORT_JSON.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    summary_lines = render_query_summary(report)
    detail_lines = render_query_details(report)
    dependency_lines = [
        f"- Dependências: `{report['dependency_status']}`.",
        f"- Entradas ausentes: `{report['missing_required_inputs']}`.",
    ]
    if report["retrieval_error"]:
        dependency_lines.append(f"- Bloqueio: {report['retrieval_error']}")

    technical_lines = [
        "# Relatório de reranking neural",
        "",
        "## Status",
        "",
        report["status"],
        "",
        "## Parâmetros",
        "",
        f"- Hybrid candidate k: `{report['configuration']['hybrid_candidate_k']}`",
        f"- Final top-k: `{report['configuration']['final_top_k']}`",
        f"- Reranker model: `{report['configuration']['reranker_model']}`",
        f"- Max text chars: `{report['configuration']['max_text_chars']}`",
        f"- Filtros padrão: `{report['configuration']['default_filters']}`",
        "",
        "## Arquivos e índices",
        "",
        "- Hybrid report: `corpus/reports/retrieval/hybrid-retrieval-report.json`.",
        "- Chunks: `corpus/processed/chunks/reformed/all_chunks_for_embeddings.jsonl`.",
        "- Índice ChromaDB: `corpus/indexes/chroma/reformed/`.",
        "- Collection: `aia_reformed_v1`.",
        "",
        "## Dependências",
        "",
        f"- sentence-transformers: `{report['dependency_status']['sentence_transformers_available']}`",
        "- CrossEncoder: `sentence_transformers.CrossEncoder`",
        f"- Modelo: `{report['configuration']['reranker_model']}`",
        "",
        "## Consultas",
        "",
        *(detail_lines or ["Consultas não executadas.", ""]),
        "## Mudanças de ranking",
        "",
        json.dumps(report["ranking_changes"], ensure_ascii=False, indent=2),
        "",
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
        "## Notas técnicas",
        "",
        f"- Execução real do CrossEncoder: `{'não executada' if report['retrieval_error'] else 'executada'}`.",
        f"- Bloqueio: `{report['retrieval_error'] or 'nenhum'}`.",
        "",
        "## Limitações",
        "",
        "- Sem parent/hierarchical retrieval.",
        "- Sem política de recusa baseada em evidência.",
        "- Sem geração de resposta.",
    ]
    TECHNICAL_REPORT_MD.write_text("\n".join(technical_lines) + "\n", encoding="utf-8")

    stage_lines = [
        "# Reranking neural do corpus reformado",
        "",
        "## Status",
        "",
        report["status"],
        "",
        "## Entradas",
        "",
        "- `reports/specs/hybrid-retrieval.md`",
        "- `corpus/reports/retrieval/hybrid-retrieval-report.md`",
        "- `corpus/reports/retrieval/hybrid-retrieval-report.json`",
        "- `corpus/processed/chunks/reformed/all_chunks_for_embeddings.jsonl`",
        "- `corpus/processed/embeddings/reformed/embedding_manifest.json`",
        "- `corpus/indexes/chroma/reformed/`",
        "- `config/retrieval_config.example.yaml`",
        "- `requirements.txt`",
        "",
        "## Código",
        "",
        "- `src/aia/retrieval/cross_encoder_reranker.py`",
        "- `src/aia/retrieval/reranked_retriever.py`",
        "- `scripts/pipeline/query_reranked_retriever.py`",
        "",
        "## Configuração",
        "",
        f"- Hybrid candidate k: `{report['configuration']['hybrid_candidate_k']}`",
        f"- Final top-k: `{report['configuration']['final_top_k']}`",
        f"- Reranker model: `{report['configuration']['reranker_model']}`",
        f"- Max text chars: `{report['configuration']['max_text_chars']}`",
        f"- Filtros: `{report['configuration']['default_filters']}`",
        "",
        "## Implementação",
        "",
        "- `CrossEncoderReranker`: montagem dos pares pergunta/chunk e pontuação por `CrossEncoder`.",
        "- `RerankedRetriever`: recuperação híbrida inicial e reordenação pelo reranker.",
        "- Metadados registrados: `reranker_provider`, `reranker_model`, `reranker_score`, `pre_rerank_rank`, `pre_rerank_score`, `pre_rerank_sources`.",
        "",
        "## Consultas",
        "",
        *(summary_lines or ["Consultas não executadas.", ""]),
        "## Resultados agregados",
        "",
        f"- Documentos mais recuperados: `{report['most_retrieved_documents']}`",
        f"- Tipos de chunk mais recuperados: `{report['most_retrieved_chunk_types']}`",
        f"- Mudanças de ranking: `{report['ranking_changes']}`",
        f"- Erro ou bloqueio: {report['retrieval_error'] or 'nenhuma ocorrência'}",
        "",
        "## Validações executadas",
        "",
        "```bash",
        'python scripts/pipeline/query_reranked_retriever.py "O que é o batismo?" --top-k 5',
        'python scripts/pipeline/query_reranked_retriever.py "O que é eleição?" --top-k 5',
        'python scripts/pipeline/query_reranked_retriever.py "O que é justificação?" --top-k 5',
        "python scripts/pipeline/query_reranked_retriever.py --write-report",
        "python -m py_compile src/aia/retrieval/cross_encoder_reranker.py",
        "python -m py_compile src/aia/retrieval/reranked_retriever.py",
        "python -m py_compile scripts/pipeline/query_reranked_retriever.py",
        "python -m pytest tests/test_reranker_retriever.py",
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
        "- parent/hierarchical retrieval",
        "- política de recusa baseada em evidência",
    ]
    STAGE_REPORT.write_text("\n".join(stage_lines) + "\n", encoding="utf-8")


def render_query_summary(report: dict[str, Any]) -> list[str]:
    """Renderiza resumo das consultas em tabela."""
    if not report["validation_queries"]:
        return []
    lines = [
        "| Consulta | Candidatos híbridos | Resultados finais | Documentos | Tipos de chunk |",
        "| --- | ---: | ---: | --- | --- |",
    ]
    for item in report["validation_queries"]:
        lines.append(
            "| "
            f"{item['query']} | "
            f"{item['hybrid_candidates_count']} | "
            f"{item['results_count']} | "
            f"{', '.join(item['documents']) or 'nenhum'} | "
            f"{', '.join(item['chunk_types']) or 'nenhum'} |"
        )
    lines.append("")
    return lines


def render_query_details(report: dict[str, Any]) -> list[str]:
    """Renderiza resultados reranqueados por consulta."""
    lines: list[str] = []
    for item in report["validation_queries"]:
        lines.extend(
            [
                f"### {item['query']}",
                "",
                f"- Candidatos híbridos: `{item['hybrid_candidates_count']}`",
                f"- Resultados finais: `{item['results_count']}`",
                "",
                "| Rank | Chunk | Documento | Tipo | Páginas | Pré-rank | RRF | Reranker |",
                "| ---: | --- | --- | --- | --- | ---: | ---: | ---: |",
            ]
        )
        for row in item["results"]:
            lines.append(
                "| "
                f"{row['final_rank']} | "
                f"`{row['chunk_id']}` | "
                f"`{row['document_id']}` | "
                f"`{row['chunk_type']}` | "
                f"{row['page_start']}-{row['page_end']} | "
                f"{row['pre_rerank_rank']} | "
                f"{row['pre_rerank_score']} | "
                f"{row['reranker_score']} |"
            )
        lines.append("")
    return lines


def build_parser() -> argparse.ArgumentParser:
    """Cria parser CLI."""
    parser = argparse.ArgumentParser(description="Consulta o retriever com reranking neural.")
    parser.add_argument("query", nargs="?", help="Pergunta doutrinária a consultar.")
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    parser.add_argument("--hybrid-k", type=int, default=DEFAULT_HYBRID_K)
    parser.add_argument("--reranker-model", default=DEFAULT_RERANKER_MODEL)
    parser.add_argument("--max-text-chars", type=int, default=DEFAULT_MAX_TEXT_CHARS)
    parser.add_argument("--document-id")
    parser.add_argument("--chunk-type")
    parser.add_argument("--write-report", action="store_true")
    return parser


def main() -> int:
    """Ponto de entrada CLI."""
    args = build_parser().parse_args()

    if args.write_report:
        report = run_validation_report(args)
        print(f"Relatório de reranking concluído com status {report['status']}.")
        if report["retrieval_error"]:
            print(f"- bloqueio: {report['retrieval_error']}")
        return 0 if report["status"] in {"PASS", "PARTIAL"} else 1

    if not args.query:
        print("Informe uma pergunta ou use --write-report.", file=sys.stderr)
        return 2

    try:
        results = run_single_query(args)
    except CrossEncoderRerankerError as exc:
        print(f"A consulta com reranking não pôde ser executada: {exc}", file=sys.stderr)
        return 1

    print_results(args.query, results, hybrid_k=args.hybrid_k)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
