"""Consulta o retriever hierárquico do corpus reformado."""

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

from aia.retrieval.hierarchical_retriever import HierarchicalRetriever  # noqa: E402
from aia.retrieval.parent_context import DEFAULT_PARENT_STRATEGY, ParentContext  # noqa: E402


REPORT_DIR = ROOT_DIR / "corpus" / "reports" / "retrieval"
STAGE_REPORT = ROOT_DIR / "reports" / "specs" / "hierarchical-retrieval.md"
TECHNICAL_REPORT_MD = REPORT_DIR / "hierarchical-retrieval-report.md"
TECHNICAL_REPORT_JSON = REPORT_DIR / "hierarchical-retrieval-report.json"
CHUNKS_PATH = ROOT_DIR / "corpus" / "processed" / "chunks" / "reformed" / "all_chunks_for_embeddings.jsonl"
DEFAULT_TOP_K = 5
DEFAULT_PARENT_MAX_CHARS = 9000
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
    ROOT_DIR / "reports" / "specs" / "reranker-retrieval.md",
    ROOT_DIR / "corpus" / "reports" / "retrieval" / "reranker-retrieval-report.md",
    ROOT_DIR / "corpus" / "reports" / "retrieval" / "reranker-retrieval-report.json",
    ROOT_DIR / "corpus" / "processed" / "chunks" / "reformed" / "all_chunks.jsonl",
    CHUNKS_PATH,
    ROOT_DIR / "corpus" / "processed" / "embeddings" / "reformed" / "embedding_manifest.json",
    ROOT_DIR / "corpus" / "indexes" / "chroma" / "reformed",
    ROOT_DIR / "config" / "retrieval_config.example.yaml",
    ROOT_DIR / "requirements.txt",
]


def relative_path(path: Path) -> str:
    return path.relative_to(ROOT_DIR).as_posix()


def compact_text(text: str, limit: int = 420) -> str:
    compacted = " ".join(text.split())
    if len(compacted) <= limit:
        return compacted
    return compacted[: limit - 3].rstrip() + "..."


def dependency_status() -> dict[str, bool]:
    if load_dotenv is not None:
        load_dotenv(ROOT_DIR / ".env")
    return {
        "sentence_transformers_available": importlib.util.find_spec("sentence_transformers") is not None,
        "rank_bm25_available": importlib.util.find_spec("rank_bm25") is not None,
        "chromadb_available": importlib.util.find_spec("chromadb") is not None,
        "openai_api_key_configured": bool(os.getenv("OPENAI_API_KEY", "").strip()),
    }


def missing_required_inputs() -> list[str]:
    return [relative_path(path) for path in REQUIRED_INPUTS if not path.exists()]


def build_filters(document_id: str | None, chunk_type: str | None) -> dict[str, str] | None:
    filters: dict[str, str] = {}
    if document_id:
        filters["document_id"] = document_id
    if chunk_type:
        filters["chunk_type"] = chunk_type
    return filters or None


def check_runtime_requirements() -> None:
    status = dependency_status()
    if not status["sentence_transformers_available"]:
        raise RuntimeError("sentence-transformers não está instalado.")
    if not status["rank_bm25_available"]:
        raise RuntimeError("rank-bm25 não está instalado.")
    if not status["chromadb_available"]:
        raise RuntimeError("chromadb não está instalado.")
    if not status["openai_api_key_configured"]:
        raise RuntimeError("OPENAI_API_KEY não está configurada.")


def run_single_query(args: argparse.Namespace) -> list[ParentContext]:
    check_runtime_requirements()
    retriever = HierarchicalRetriever(
        reranked_top_k=args.top_k,
        parent_context_max_chars=args.parent_max_chars,
        sibling_window_before=args.sibling_before,
        sibling_window_after=args.sibling_after,
    )
    return retriever.retrieve(
        query=args.query,
        top_k=args.top_k,
        filters=build_filters(args.document_id, args.chunk_type),
    )


def print_contexts(query: str, contexts: list[ParentContext]) -> None:
    print(f"Pergunta: {query}")
    print(f"Chunks âncora: {len(contexts)}")
    print(f"Contextos gerados: {len(contexts)}")
    print()
    for rank, context in enumerate(contexts, start=1):
        print(f"{rank}. {context.anchor_document} ({context.anchor_document_id})")
        print(f"   Unidade superior: {context.parent_title or context.parent_key}")
        print(f"   Chunk âncora: {context.anchor_chunk_id}")
        print(f"   Score reranker: {context.anchor_score}")
        print(f"   Score RRF antes: {context.anchor_pre_rerank_score}")
        print(f"   Chunks no contexto: {context.included_chunk_count}")
        print(f"   Páginas: {_format_pages(context.page_start, context.page_end)}")
        print(f"   Estratégia: {context.parent_strategy}")
        print(f"   Status: {context.parent_expansion_status}")
        print(f"   Trecho: {compact_text(context.context_text)}")
        print()


def context_to_row(context: ParentContext, rank: int) -> dict[str, Any]:
    anchor = context.anchor_result
    return {
        "rank": rank,
        "anchor_chunk_id": context.anchor_chunk_id,
        "anchor_document_id": context.anchor_document_id,
        "anchor_document": context.anchor_document,
        "anchor_chunk_type": anchor.chunk_type if anchor else None,
        "anchor_score": context.anchor_score,
        "anchor_pre_rerank_score": context.anchor_pre_rerank_score,
        "parent_key": context.parent_key,
        "parent_title": context.parent_title,
        "parent_strategy": context.parent_strategy,
        "parent_expansion_status": context.parent_expansion_status,
        "included_chunk_ids": context.included_chunk_ids,
        "included_chunk_count": context.included_chunk_count,
        "page_start": context.page_start,
        "page_end": context.page_end,
        "context_char_count": context.context_char_count,
        "metadata": context.metadata,
    }


def load_chunk_stats() -> dict[str, int]:
    chunks_loaded = 0
    parent_keys: set[str] = set()
    if not CHUNKS_PATH.exists():
        return {"chunks_loaded": 0, "parent_groups": 0}
    from aia.retrieval.parent_context import build_parent_key

    with CHUNKS_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            chunk = json.loads(line)
            chunks_loaded += 1
            parent_keys.add(build_parent_key(chunk))
    return {"chunks_loaded": chunks_loaded, "parent_groups": len(parent_keys)}


def run_validation_report(args: argparse.Namespace) -> dict[str, Any]:
    status = dependency_status()
    missing_inputs = missing_required_inputs()
    retrieval_error: str | None = None
    validations: list[dict[str, Any]] = []
    chunk_stats = load_chunk_stats()

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
            retriever = HierarchicalRetriever(
                reranked_top_k=args.top_k,
                parent_context_max_chars=args.parent_max_chars,
                sibling_window_before=args.sibling_before,
                sibling_window_after=args.sibling_after,
            )
            filters = build_filters(args.document_id, args.chunk_type)
            for query in VALIDATION_QUERIES:
                contexts = retriever.retrieve(query=query, top_k=args.top_k, filters=filters)
                rows = [context_to_row(context, rank) for rank, context in enumerate(contexts, start=1)]
                validations.append(
                    {
                        "query": query,
                        "anchor_top_k": args.top_k,
                        "contexts_count": len(rows),
                        "documents": sorted({row["anchor_document_id"] for row in rows}),
                        "parent_keys": sorted({row["parent_key"] for row in rows}),
                        "anchor_chunk_ids": [row["anchor_chunk_id"] for row in rows],
                        "expansion_statuses": sorted({row["parent_expansion_status"] for row in rows}),
                        "results": rows,
                    }
                )
        except Exception as exc:
            retrieval_error = f"{type(exc).__name__}: {exc}"

    rows = [row for item in validations for row in item["results"]]
    documents_counter = Counter(row["anchor_document_id"] for row in rows)
    chunk_types_counter = Counter(row["anchor_chunk_type"] for row in rows if row["anchor_chunk_type"])
    statuses_counter = Counter(row["parent_expansion_status"] for row in rows)
    report_status = "PASS"
    if missing_inputs:
        report_status = "FAIL"
    elif retrieval_error or not validations:
        report_status = "PARTIAL"

    report = {
        "status": report_status,
        "configuration": {
            "strategy": DEFAULT_PARENT_STRATEGY,
            "anchor_source": "reranked_retriever",
            "reranked_top_k": args.top_k,
            "parent_context_max_chars": args.parent_max_chars,
            "sibling_window_before": args.sibling_before,
            "sibling_window_after": args.sibling_after,
            "include_full_parent_when_small": True,
            "full_parent_max_chars": 7000,
            "include_metadata_header": True,
            "preserve_anchor_first": True,
            "default_filters": {
                "corpus_id": "reformed",
                "retrieval_namespace": "reformed_confessional",
            },
        },
        "dependency_status": status,
        "missing_required_inputs": missing_inputs,
        "retrieval_error": retrieval_error,
        "chunks_path": relative_path(CHUNKS_PATH),
        "chunks_loaded": chunk_stats["chunks_loaded"],
        "parent_groups": chunk_stats["parent_groups"],
        "validation_queries": validations,
        "most_retrieved_documents": dict(documents_counter.most_common()),
        "anchor_chunk_types": dict(chunk_types_counter.most_common()),
        "expansion_statuses": dict(statuses_counter.most_common()),
        "scope_not_executed": [
            "final_chatbot",
            "llm_answer_generation",
            "openai_chat_model_call",
            "other_traditions_evaluation",
            "user_upload",
            "chunk_embedding_pdf_change",
            "new_extraction_normalization_chunking_or_indexing",
            "evidence_based_refusal_policy",
        ],
    }
    write_reports(report)
    return report


def write_reports(report: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    STAGE_REPORT.parent.mkdir(parents=True, exist_ok=True)
    TECHNICAL_REPORT_JSON.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    query_summary = render_query_summary(report)
    query_details = render_query_details(report)
    stage_lines = [
        "# Recuperação hierárquica do corpus reformado",
        "",
        "## Status",
        "",
        report["status"],
        "",
        "## Entradas",
        "",
        "- `reports/specs/reranker-retrieval.md`",
        "- `corpus/reports/retrieval/reranker-retrieval-report.md`",
        "- `corpus/reports/retrieval/reranker-retrieval-report.json`",
        "- `corpus/processed/chunks/reformed/all_chunks.jsonl`",
        "- `corpus/processed/chunks/reformed/all_chunks_for_embeddings.jsonl`",
        "- `corpus/processed/embeddings/reformed/embedding_manifest.json`",
        "- `corpus/indexes/chroma/reformed/`",
        "- `config/retrieval_config.example.yaml`",
        "- `requirements.txt`",
        "",
        "## Código",
        "",
        "- `src/aia/retrieval/parent_context.py`",
        "- `src/aia/retrieval/hierarchical_retriever.py`",
        "- `scripts/pipeline/query_hierarchical_retriever.py`",
        "",
        "## Configuração",
        "",
        f"- Estratégia: `{report['configuration']['strategy']}`",
        f"- Anchor source: `{report['configuration']['anchor_source']}`",
        f"- Reranked top-k: `{report['configuration']['reranked_top_k']}`",
        f"- Parent max chars: `{report['configuration']['parent_context_max_chars']}`",
        f"- Janela de irmãos: `{report['configuration']['sibling_window_before']}` antes, `{report['configuration']['sibling_window_after']}` depois",
        f"- Filtros: `{report['configuration']['default_filters']}`",
        "",
        "## Implementação",
        "",
        "- `ParentContextBuilder` carrega os chunks e cria índices por `chunk_id` e `parent_key`.",
        "- `HierarchicalRetriever` chama o `RerankedRetriever` e expande cada chunk âncora.",
        "- O contexto preserva chunk âncora, chunks incluídos, páginas, fonte e scores anteriores.",
        "",
        "## Consultas",
        "",
        *(query_summary or ["Consultas não executadas.", ""]),
        "## Resultados agregados",
        "",
        f"- Chunks carregados: `{report['chunks_loaded']}`",
        f"- Grupos estruturais: `{report['parent_groups']}`",
        f"- Documentos: `{report['most_retrieved_documents']}`",
        f"- Tipos de chunk âncora: `{report['anchor_chunk_types']}`",
        f"- Status das expansões: `{report['expansion_statuses']}`",
        f"- Erro ou bloqueio: {report['retrieval_error'] or 'nenhuma ocorrência'}",
        "",
        "## Validações executadas",
        "",
        "```bash",
        'python scripts/pipeline/query_hierarchical_retriever.py "O que é o batismo?" --top-k 5',
        'python scripts/pipeline/query_hierarchical_retriever.py "O que é eleição?" --top-k 5',
        'python scripts/pipeline/query_hierarchical_retriever.py "O que é justificação?" --top-k 5',
        "python scripts/pipeline/query_hierarchical_retriever.py --write-report",
        "python -m py_compile src/aia/retrieval/parent_context.py",
        "python -m py_compile src/aia/retrieval/hierarchical_retriever.py",
        "python -m py_compile scripts/pipeline/query_hierarchical_retriever.py",
        "python -m pytest tests/test_hierarchical_retriever.py",
        "```",
        "",
        "## Pontos de atenção",
        "",
        f"- Dependências: `{report['dependency_status']}`",
        f"- Entradas ausentes: `{report['missing_required_inputs']}`",
        f"- Bloqueio: `{report['retrieval_error'] or 'nenhum'}`",
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
        "- política de recusa baseada em evidência",
    ]
    STAGE_REPORT.write_text("\n".join(stage_lines) + "\n", encoding="utf-8")

    technical_lines = [
        "# Relatório de recuperação hierárquica",
        "",
        "## Status",
        "",
        report["status"],
        "",
        "## Configuração",
        "",
        json.dumps(report["configuration"], ensure_ascii=False, indent=2),
        "",
        "## Corpus hierárquico",
        "",
        f"- Arquivo de chunks: `{report['chunks_path']}`",
        f"- Chunks carregados: `{report['chunks_loaded']}`",
        f"- Grupos estruturais identificados: `{report['parent_groups']}`",
        "",
        "## Consultas",
        "",
        *(query_details or ["Consultas não executadas.", ""]),
        "## Agregados",
        "",
        "Documentos:",
        "",
        json.dumps(report["most_retrieved_documents"], ensure_ascii=False, indent=2),
        "",
        "Tipos de chunk âncora:",
        "",
        json.dumps(report["anchor_chunk_types"], ensure_ascii=False, indent=2),
        "",
        "Status de expansão:",
        "",
        json.dumps(report["expansion_statuses"], ensure_ascii=False, indent=2),
        "",
        "## Notas técnicas",
        "",
        f"- Execução real do RerankedRetriever: `{'não executada' if report['retrieval_error'] else 'executada'}`.",
        f"- Bloqueio: `{report['retrieval_error'] or 'nenhum'}`.",
        "- A expansão usa apenas chunks do mesmo documento e da mesma chave estrutural.",
        "- O chunk âncora é colocado antes dos trechos relacionados.",
        "",
        "## Limitações",
        "",
        "- A chave estrutural depende dos metadados já presentes nos chunks.",
        "- A expansão usa janela estrutural simples, sem sumarização e sem geração textual.",
        "- Contextos longos são limitados por caracteres.",
    ]
    TECHNICAL_REPORT_MD.write_text("\n".join(technical_lines) + "\n", encoding="utf-8")


def render_query_summary(report: dict[str, Any]) -> list[str]:
    if not report["validation_queries"]:
        return []
    lines = [
        "| Consulta | Âncoras | Contextos | Documentos | Status |",
        "| --- | ---: | ---: | --- | --- |",
    ]
    for item in report["validation_queries"]:
        lines.append(
            "| "
            f"{item['query']} | "
            f"{item['anchor_top_k']} | "
            f"{item['contexts_count']} | "
            f"{', '.join(item['documents']) or 'nenhum'} | "
            f"{', '.join(item['expansion_statuses']) or 'nenhum'} |"
        )
    lines.append("")
    return lines


def render_query_details(report: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for item in report["validation_queries"]:
        lines.extend(
            [
                f"### {item['query']}",
                "",
                f"- Top-k de âncoras: `{item['anchor_top_k']}`",
                f"- Contextos gerados: `{item['contexts_count']}`",
                "",
                "| Rank | Âncora | Documento | Unidade | Chunks | Páginas | Status |",
                "| ---: | --- | --- | --- | ---: | --- | --- |",
            ]
        )
        for row in item["results"]:
            lines.append(
                "| "
                f"{row['rank']} | "
                f"`{row['anchor_chunk_id']}` | "
                f"`{row['anchor_document_id']}` | "
                f"`{row['parent_title'] or row['parent_key']}` | "
                f"{row['included_chunk_count']} | "
                f"{_format_pages(row['page_start'], row['page_end'])} | "
                f"`{row['parent_expansion_status']}` |"
            )
        lines.append("")
    return lines


def _format_pages(page_start: Any, page_end: Any) -> str:
    if page_start is None and page_end is None:
        return "não informado"
    if page_end is None or page_start == page_end:
        return str(page_start)
    return f"{page_start}-{page_end}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Consulta o retriever hierárquico.")
    parser.add_argument("query", nargs="?", help="Pergunta doutrinária a consultar.")
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    parser.add_argument("--parent-max-chars", type=int, default=DEFAULT_PARENT_MAX_CHARS)
    parser.add_argument("--sibling-before", type=int, default=1)
    parser.add_argument("--sibling-after", type=int, default=1)
    parser.add_argument("--document-id")
    parser.add_argument("--chunk-type")
    parser.add_argument("--write-report", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()

    if args.write_report:
        report = run_validation_report(args)
        print(f"Relatório de recuperação hierárquica concluído com status {report['status']}.")
        if report["retrieval_error"]:
            print(f"- bloqueio: {report['retrieval_error']}")
        return 0 if report["status"] in {"PASS", "PARTIAL"} else 1

    if not args.query:
        print("Informe uma pergunta ou use --write-report.", file=sys.stderr)
        return 2

    try:
        contexts = run_single_query(args)
    except Exception as exc:
        print(f"A consulta hierárquica não pôde ser executada: {exc}", file=sys.stderr)
        return 1

    print_contexts(args.query, contexts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
