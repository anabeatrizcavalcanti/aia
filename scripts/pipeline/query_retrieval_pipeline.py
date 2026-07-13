"""Consulta a pipeline final de retrieval do corpus reformado."""

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

from sola_bot.retrieval.context_consolidator import ContextConsolidator  # noqa: E402
from sola_bot.retrieval.final_context import (  # noqa: E402
    RetrievalContextPackage,
    build_context_package_text,
)
from sola_bot.retrieval.retrieval_pipeline import RetrievalPipeline  # noqa: E402


REPORT_DIR = ROOT_DIR / "corpus" / "reports" / "retrieval"
STAGE_REPORT = ROOT_DIR / "reports" / "specs" / "retrieval-pipeline.md"
TECHNICAL_REPORT_MD = REPORT_DIR / "retrieval-pipeline-report.md"
TECHNICAL_REPORT_JSON = REPORT_DIR / "retrieval-pipeline-report.json"
CHUNKS_PATH = ROOT_DIR / "corpus" / "processed" / "chunks" / "reformed" / "all_chunks_for_embeddings.jsonl"
DEFAULT_FINAL_TOP_K = 4
DEFAULT_MAX_TOTAL_CHARS = 18000
DEFAULT_MAX_CONTEXT_CHARS_PER_PARENT = 9000
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
    ROOT_DIR / "reports" / "specs" / "hierarchical-retrieval.md",
    ROOT_DIR / "corpus" / "reports" / "retrieval" / "hierarchical-retrieval-report.md",
    ROOT_DIR / "corpus" / "reports" / "retrieval" / "hierarchical-retrieval-report.json",
    CHUNKS_PATH,
    ROOT_DIR / "corpus" / "processed" / "embeddings" / "reformed" / "embedding_manifest.json",
    ROOT_DIR / "corpus" / "indexes" / "chroma" / "reformed",
    ROOT_DIR / "config" / "retrieval_config.example.yaml",
    ROOT_DIR / "requirements.txt",
]


def relative_path(path: Path) -> str:
    return path.relative_to(ROOT_DIR).as_posix()


def compact_text(text: str, limit: int = 520) -> str:
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


def make_pipeline(args: argparse.Namespace) -> RetrievalPipeline:
    consolidator = ContextConsolidator(
        final_context_top_k=args.final_top_k,
        max_total_context_chars=args.max_total_chars,
        max_context_chars_per_parent=args.max_context_chars_per_parent,
    )
    return RetrievalPipeline(
        final_context_top_k=args.final_top_k,
        max_total_context_chars=args.max_total_chars,
        max_context_chars_per_parent=args.max_context_chars_per_parent,
        context_consolidator=consolidator,
    )


def run_single_query(args: argparse.Namespace) -> RetrievalContextPackage:
    check_runtime_requirements()
    pipeline = make_pipeline(args)
    return pipeline.retrieve(
        query=args.query,
        filters=build_filters(args.document_id, args.chunk_type),
    )


def print_package(package: RetrievalContextPackage) -> None:
    print(f"Pergunta: {package.query}")
    print(f"Contextos finais: {package.context_count}")
    print(f"Total de caracteres: {package.total_context_chars}")
    print(f"Documentos: {', '.join(package.documents) or 'nenhum'}")
    print(f"Parent keys: {', '.join(context.parent_key for context in package.contexts)}")
    print()
    for context in package.contexts:
        print(f"{context.rank}. {context.document} ({context.document_id})")
        print(f"   Parent key: {context.parent_key}")
        print(f"   Unidade: {context.parent_title or 'não informado'}")
        print(f"   Chunks âncora: {', '.join(context.anchor_chunk_ids)}")
        print(f"   Chunks incluídos: {', '.join(context.included_chunk_ids)}")
        print(f"   Status: {context.context_status}")
        print(f"   Prioridade: {context.content_priority}")
        print(f"   Decisão anchor_only: {context.metadata.get('anchor_only_handling')}")
        print(f"   Decisão de consolidação: {context.metadata.get('consolidation_decision')}")
        print(f"   Páginas: {_format_pages(context.page_start, context.page_end)}")
        print()
    print("Trecho do pacote:")
    print(compact_text(build_context_package_text(package)))


def package_to_report_row(package: RetrievalContextPackage, hierarchical_count: int) -> dict[str, Any]:
    contexts = [context.to_dict() for context in package.contexts]
    contexts_fused = package.metadata.get("contexts_fused_by_parent_key", 0)
    dedupe = package.metadata.get("deduplication", {})
    removed = package.metadata.get("removed_contexts", {})
    anchor_only_decisions = Counter(
        context.metadata.get("anchor_only_handling") for context in package.contexts
    )
    introductory_contexts = [
        context.parent_key for context in package.contexts if context.content_priority == "introductory"
    ]
    return {
        "query": package.query,
        "hierarchical_contexts_received": hierarchical_count,
        "final_context_count": package.context_count,
        "parent_keys_selected": [context.parent_key for context in package.contexts],
        "parent_keys_removed_or_fused": {
            "fused_count": contexts_fused,
            "removed": removed,
            "dropped_by_limit": package.metadata.get("char_limits", {}).get("dropped_by_limit", []),
        },
        "documents": package.documents,
        "anchor_chunk_ids": [chunk_id for context in package.contexts for chunk_id in context.anchor_chunk_ids],
        "included_chunk_ids": [chunk_id for context in package.contexts for chunk_id in context.included_chunk_ids],
        "total_context_chars": package.total_context_chars,
        "anchor_only_decisions": dict(anchor_only_decisions),
        "introductory_contexts": introductory_contexts,
        "deduplicated_chunk_count": dedupe.get("deduplicated_chunk_count", 0),
        "contexts": contexts,
        "source_map": package.source_map,
    }


def run_validation_report(args: argparse.Namespace) -> dict[str, Any]:
    status = dependency_status()
    missing_inputs = missing_required_inputs()
    retrieval_error: str | None = None
    validations: list[dict[str, Any]] = []

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
            pipeline = make_pipeline(args)
            filters = build_filters(args.document_id, args.chunk_type)
            for query in VALIDATION_QUERIES:
                parent_contexts = pipeline.hierarchical_retriever.retrieve(query=query, filters=filters)
                package = pipeline.context_consolidator.consolidate(
                    query=query,
                    parent_contexts=parent_contexts,
                    filters=filters,
                )
                validations.append(package_to_report_row(package, len(parent_contexts)))
        except Exception as exc:
            retrieval_error = f"{type(exc).__name__}: {exc}"

    final_rows = [context for item in validations for context in item["contexts"]]
    documents_counter = Counter(context["document_id"] for context in final_rows)
    chunk_types_counter = Counter(
        chunk_type
        for context in final_rows
        for chunk_type in context["metadata"].get("anchor_chunk_types", [])
    )
    report_status = "PASS"
    if missing_inputs:
        report_status = "FAIL"
    elif retrieval_error or not validations:
        report_status = "PARTIAL"

    report = {
        "status": report_status,
        "configuration": {
            "source": "hierarchical_retriever",
            "final_context_top_k": args.final_top_k,
            "max_total_context_chars": args.max_total_chars,
            "max_context_chars_per_parent": args.max_context_chars_per_parent,
            "consolidate_by_parent_key": True,
            "deduplicate_included_chunks": True,
            "prefer_expanded_contexts": True,
            "reduce_introductory_context_for_doctrinal_queries": True,
            "keep_anchor_only_when_no_expanded_alternative": True,
            "preserve_document_diversity": True,
            "max_contexts_per_parent_key": 1,
            "include_context_package_header": True,
            "include_source_map": True,
            "default_filters": {
                "corpus_id": "reformed",
                "retrieval_namespace": "reformed_confessional",
            },
        },
        "dependency_status": status,
        "missing_required_inputs": missing_inputs,
        "retrieval_error": retrieval_error,
        "validation_queries": validations,
        "documents_preserved": dict(documents_counter.most_common()),
        "anchor_chunk_types_preserved": dict(chunk_types_counter.most_common()),
        "total_hierarchical_contexts_received": sum(
            item["hierarchical_contexts_received"] for item in validations
        ),
        "total_final_contexts": sum(item["final_context_count"] for item in validations),
        "total_contexts_fused": sum(
            item["parent_keys_removed_or_fused"]["fused_count"] for item in validations
        ),
        "total_deduplicated_chunks": sum(item["deduplicated_chunk_count"] for item in validations),
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

    summary_lines = render_query_summary(report)
    detail_lines = render_query_details(report)
    stage_lines = [
        "# Pipeline final de retrieval do corpus reformado",
        "",
        "## Status",
        "",
        report["status"],
        "",
        "## Entradas",
        "",
        "- `reports/specs/hierarchical-retrieval.md`",
        "- `corpus/reports/retrieval/hierarchical-retrieval-report.md`",
        "- `corpus/reports/retrieval/hierarchical-retrieval-report.json`",
        "- `corpus/processed/chunks/reformed/all_chunks_for_embeddings.jsonl`",
        "- `corpus/processed/embeddings/reformed/embedding_manifest.json`",
        "- `corpus/indexes/chroma/reformed/`",
        "- `config/retrieval_config.example.yaml`",
        "- `requirements.txt`",
        "",
        "## Código",
        "",
        "- `src/sola_bot/retrieval/final_context.py`",
        "- `src/sola_bot/retrieval/context_consolidator.py`",
        "- `src/sola_bot/retrieval/retrieval_pipeline.py`",
        "- `scripts/pipeline/query_retrieval_pipeline.py`",
        "",
        "## Configuração",
        "",
        f"- Final top-k: `{report['configuration']['final_context_top_k']}`",
        f"- Limite total de caracteres: `{report['configuration']['max_total_context_chars']}`",
        f"- Limite por parent: `{report['configuration']['max_context_chars_per_parent']}`",
        f"- Consolidação por parent_key: `{report['configuration']['consolidate_by_parent_key']}`",
        f"- Filtros: `{report['configuration']['default_filters']}`",
        "",
        "## Implementação",
        "",
        "- `FinalContext` e `RetrievalContextPackage` representam a saída consolidada.",
        "- `ContextConsolidator` agrupa por `parent_key`, deduplica chunks e aplica limites de tamanho.",
        "- `RetrievalPipeline` chama o `HierarchicalRetriever` e entrega o pacote final.",
        "",
        "## Consultas",
        "",
        *(summary_lines or ["Consultas não executadas.", ""]),
        "## Resultados agregados",
        "",
        f"- Contextos hierárquicos recebidos: `{report['total_hierarchical_contexts_received']}`",
        f"- Contextos finais: `{report['total_final_contexts']}`",
        f"- Contextos fundidos por parent_key: `{report['total_contexts_fused']}`",
        f"- Chunks deduplicados: `{report['total_deduplicated_chunks']}`",
        f"- Documentos preservados: `{report['documents_preserved']}`",
        f"- Tipos de chunk preservados: `{report['anchor_chunk_types_preserved']}`",
        f"- Erro ou bloqueio: {report['retrieval_error'] or 'nenhuma ocorrência'}",
        "",
        "## Validações executadas",
        "",
        "```bash",
        'python scripts/pipeline/query_retrieval_pipeline.py "O que é o batismo?"',
        'python scripts/pipeline/query_retrieval_pipeline.py "O que é eleição?"',
        'python scripts/pipeline/query_retrieval_pipeline.py "O que é justificação?"',
        'python scripts/pipeline/query_retrieval_pipeline.py "O que é expiação?"',
        "python scripts/pipeline/query_retrieval_pipeline.py --write-report",
        "python -m py_compile src/sola_bot/retrieval/final_context.py",
        "python -m py_compile src/sola_bot/retrieval/context_consolidator.py",
        "python -m py_compile src/sola_bot/retrieval/retrieval_pipeline.py",
        "python -m py_compile scripts/pipeline/query_retrieval_pipeline.py",
        "python -m pytest tests/test_retrieval_pipeline.py",
        "```",
        "",
        "## Pontos de atenção",
        "",
        f"- Dependências: `{report['dependency_status']}`",
        f"- Entradas ausentes: `{report['missing_required_inputs']}`",
        f"- Bloqueio: `{report['retrieval_error'] or 'nenhum'}`",
        "- A ordenação final usa heurística operacional documentada no JSON do relatório.",
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
        "# Relatório da pipeline final de retrieval",
        "",
        "## Status",
        "",
        report["status"],
        "",
        "## Configuração",
        "",
        json.dumps(report["configuration"], ensure_ascii=False, indent=2),
        "",
        "## Consultas",
        "",
        *(detail_lines or ["Consultas não executadas.", ""]),
        "## Agregados",
        "",
        f"- Contextos hierárquicos recebidos: `{report['total_hierarchical_contexts_received']}`",
        f"- Contextos finais após consolidação: `{report['total_final_contexts']}`",
        f"- Contextos removidos ou fundidos: `{report['total_contexts_fused']}`",
        f"- Chunks deduplicados: `{report['total_deduplicated_chunks']}`",
        "",
        "Documentos preservados:",
        "",
        json.dumps(report["documents_preserved"], ensure_ascii=False, indent=2),
        "",
        "Tipos de chunk preservados:",
        "",
        json.dumps(report["anchor_chunk_types_preserved"], ensure_ascii=False, indent=2),
        "",
        "## Notas técnicas",
        "",
        "- A deduplicação por `parent_key` reduz repetições de capítulo ou unidade documental.",
        "- A deduplicação por `chunk_id` atua sobre os metadados do pacote final.",
        "- Contextos introdutórios perdem prioridade quando a consulta é classificada como doutrinária.",
        "- Contextos `anchor_only` são mantidos apenas quando passam pela ordenação e pelos limites do pacote.",
        "",
        "## Limitações",
        "",
        "- A pipeline não gera resposta textual ao usuário.",
        "- A diversidade documental não força inclusão de documento com baixa pontuação.",
        "- A consolidação usa metadados estruturais já presentes nos chunks.",
    ]
    TECHNICAL_REPORT_MD.write_text("\n".join(technical_lines) + "\n", encoding="utf-8")


def render_query_summary(report: dict[str, Any]) -> list[str]:
    if not report["validation_queries"]:
        return []
    lines = [
        "| Consulta | Hierárquicos | Finais | Fundidos | Dedup chunks | Caracteres | Documentos |",
        "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for item in report["validation_queries"]:
        lines.append(
            "| "
            f"{item['query']} | "
            f"{item['hierarchical_contexts_received']} | "
            f"{item['final_context_count']} | "
            f"{item['parent_keys_removed_or_fused']['fused_count']} | "
            f"{item['deduplicated_chunk_count']} | "
            f"{item['total_context_chars']} | "
            f"{', '.join(item['documents']) or 'nenhum'} |"
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
                f"- Contextos recebidos da camada hierárquica: `{item['hierarchical_contexts_received']}`",
                f"- Contextos finais: `{item['final_context_count']}`",
                f"- Total de caracteres: `{item['total_context_chars']}`",
                f"- Parent keys selecionados: `{item['parent_keys_selected']}`",
                f"- Parent keys removidos ou fundidos: `{item['parent_keys_removed_or_fused']}`",
                f"- Decisões sobre anchor_only: `{item['anchor_only_decisions']}`",
                f"- Contextos introdutórios preservados: `{item['introductory_contexts']}`",
                "",
                "| Rank | Parent key | Documento | Status | Prioridade | Chunks incluídos | Caracteres |",
                "| ---: | --- | --- | --- | --- | ---: | ---: |",
            ]
        )
        for context in item["contexts"]:
            lines.append(
                "| "
                f"{context['rank']} | "
                f"`{context['parent_key']}` | "
                f"`{context['document_id']}` | "
                f"`{context['context_status']}` | "
                f"`{context['content_priority']}` | "
                f"{len(context['included_chunk_ids'])} | "
                f"{context['context_char_count']} |"
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
    parser = argparse.ArgumentParser(description="Consulta a pipeline final de retrieval.")
    parser.add_argument("query", nargs="?", help="Pergunta doutrinária a consultar.")
    parser.add_argument("--document-id")
    parser.add_argument("--chunk-type")
    parser.add_argument("--max-total-chars", type=int, default=DEFAULT_MAX_TOTAL_CHARS)
    parser.add_argument("--max-context-chars-per-parent", type=int, default=DEFAULT_MAX_CONTEXT_CHARS_PER_PARENT)
    parser.add_argument("--final-top-k", type=int, default=DEFAULT_FINAL_TOP_K)
    parser.add_argument("--write-report", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()

    if args.write_report:
        report = run_validation_report(args)
        print(f"Relatório da pipeline final concluído com status {report['status']}.")
        if report["retrieval_error"]:
            print(f"- bloqueio: {report['retrieval_error']}")
        return 0 if report["status"] in {"PASS", "PARTIAL"} else 1

    if not args.query:
        print("Informe uma pergunta ou use --write-report.", file=sys.stderr)
        return 2

    try:
        package = run_single_query(args)
    except Exception as exc:
        print(f"A pipeline final não pôde ser executada: {exc}", file=sys.stderr)
        return 1

    print_package(package)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
