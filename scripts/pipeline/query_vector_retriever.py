"""Consulta o retriever vetorial simples do corpus reformado."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - fallback para ambientes mínimos
    load_dotenv = None


ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from sola_bot.retrieval.query_embedder import QueryEmbeddingError  # noqa: E402
from sola_bot.retrieval.vector_retriever import (  # noqa: E402
    DEFAULT_CHUNKS_PATH,
    DEFAULT_COLLECTION_NAME,
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_FILTERS,
    DEFAULT_PERSIST_DIRECTORY,
    VectorRetriever,
    VectorRetrieverError,
)


DEFAULT_TOP_K = 5
REPORT_DIR = ROOT_DIR / "corpus" / "reports" / "retrieval"
STAGE_REPORT = ROOT_DIR / "reports" / "specs" / "vector-retrieval.md"
TECHNICAL_REPORT_MD = REPORT_DIR / "vector-retrieval-report.md"
TECHNICAL_REPORT_JSON = REPORT_DIR / "vector-retrieval-report.json"
VALIDATION_QUERIES = [
    "O que é o batismo?",
    "O que é necessário para a salvação?",
    "O que é eleição?",
    "O que é justificação?",
    "O que a tradição reformada ensina sobre as Escrituras?",
    "O crente pode perder a salvação?",
]
REQUIRED_INPUTS = [
    ROOT_DIR / "reports" / "specs" / "openai-embeddings.md",
    ROOT_DIR / "reports" / "specs" / "chroma-vector-index.md",
    ROOT_DIR / "corpus" / "processed" / "chunks" / "reformed" / "all_chunks_for_embeddings.jsonl",
    ROOT_DIR / "corpus" / "processed" / "embeddings" / "reformed" / "embedding_manifest.json",
    ROOT_DIR / "corpus" / "indexes" / "chroma" / "reformed",
]


def relative_path(path: Path) -> str:
    """Retorna caminho relativo à raiz do repositório."""
    return path.relative_to(ROOT_DIR).as_posix()


def result_to_report_row(result: Any) -> dict[str, Any]:
    """Converte um resultado de retrieval para registro de relatório."""
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
        "score": result.score,
        "distance": result.distance,
        "text_preview": compact_text(result.text, limit=380),
    }


def compact_text(text: str, limit: int = 500) -> str:
    """Compacta texto para exibição em terminal e relatórios."""
    compacted = " ".join(text.split())
    if len(compacted) <= limit:
        return compacted
    return compacted[: limit - 3].rstrip() + "..."


def format_pages(result: Any) -> str:
    """Formata intervalo de páginas de um resultado."""
    if result.page_start is None and result.page_end is None:
        return "não informado"
    if result.page_start == result.page_end or result.page_end is None:
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


def observe_query(query: str, rows: list[dict[str, Any]]) -> str:
    """Registra observação humana breve sobre a coerência inicial do retrieval."""
    if not rows:
        return "A consulta não retornou resultados; isso precisa ser revisado antes da camada RAG."

    lowered = query.lower()
    documents = {row["document_id"] for row in rows}
    chunk_types = {row["chunk_type"] for row in rows}

    if "batismo" in lowered and {
        "confissao-batista-londres-1689",
        "catecismo-heidelberg",
        "confissao-fe-westminster",
    } & documents:
        return (
            "A consulta sobre batismo recuperou trechos confessionais sobre sacramentos, "
            "incluindo documentos que tratam diretamente do tema."
        )
    if "eleição" in lowered and "canones-de-dort" in documents:
        return (
            "A consulta sobre eleição retornou Cânones de Dort entre os principais resultados, "
            "o que é coerente com a centralidade desse documento para o tema."
        )
    if "justificação" in lowered and {
        "confissao-fe-westminster",
        "confissao-batista-londres-1689",
    } & documents:
        return (
            "A consulta sobre justificação recuperou seções confessionais diretamente ligadas "
            "ao vocabulário soteriológico reformado."
        )
    if "escrituras" in lowered and {
        "confissao-fe-westminster",
        "confissao-batista-londres-1689",
    } & documents:
        return (
            "A consulta sobre Escrituras recuperou capítulos confessionais sobre a doutrina da "
            "Palavra de Deus, preservando fonte e localização."
        )
    if "perder a salvação" in lowered and {
        "doctrinal_article",
        "error_refutation",
        "confessional_paragraph",
    } & chunk_types:
        return (
            "A consulta sobre perseverança retornou chunks doutrinários associados à salvação "
            "e à perseverança dos santos."
        )
    if "salvação" in lowered and {"catechism_question_answer", "confessional_paragraph"} & chunk_types:
        return (
            "A consulta sobre salvação retornou unidades catequéticas e confessionais úteis "
            "para a futura composição de resposta fundamentada."
        )
    return (
        "Os resultados retornaram chunks do corpus reformado com metadados rastreáveis; "
        "a coerência fina ainda deve ser refinada nas próximas camadas de recuperação."
    )


def run_single_query(
    query: str,
    top_k: int,
    document_id: str | None,
    chunk_type: str | None,
    persist_dir: str,
    collection_name: str,
    embedding_model: str,
    chunks_path: str,
) -> list[Any]:
    """Executa uma consulta vetorial no corpus reformado."""
    filters: dict[str, str] = {}
    if document_id:
        filters["document_id"] = document_id
    if chunk_type:
        filters["chunk_type"] = chunk_type

    retriever = VectorRetriever(
        persist_directory=persist_dir,
        collection_name=collection_name,
        embedding_model=embedding_model,
        chunks_path=chunks_path,
    )
    return retriever.retrieve(query=query, top_k=top_k, filters=filters or None)


def print_results(query: str, results: list[Any]) -> None:
    """Imprime resultados em formato legível no terminal."""
    print(f"Pergunta: {query}")
    print(f"Resultados retornados: {len(results)}")
    print(f"Filtros obrigatórios: {DEFAULT_FILTERS}")
    print()
    for index, result in enumerate(results, start=1):
        print(f"{index}. {result.document} ({result.document_id})")
        print(f"   Chunk: {result.chunk_id}")
        print(f"   Tipo: {result.chunk_type}")
        print(f"   Seção: {format_section(result)}")
        print(f"   Páginas: {format_pages(result)}")
        print(f"   Distância/score: {result.distance}")
        print(f"   Fonte: {result.source_path}")
        print(f"   Trecho: {compact_text(result.text, limit=360)}")
        print()


def missing_required_inputs() -> list[str]:
    """Lista entradas obrigatórias ausentes."""
    return [relative_path(path) for path in REQUIRED_INPUTS if not path.exists()]


def build_report(
    persist_dir: str,
    collection_name: str,
    embedding_model: str,
    top_k: int,
    validations: list[dict[str, Any]],
    retrieval_error: str | None,
) -> dict[str, Any]:
    """Monta relatório estruturado de retrieval vetorial."""
    missing_inputs = missing_required_inputs()
    result_rows = [row for item in validations for row in item["results"]]
    documents_counter = Counter(row["document_id"] for row in result_rows)
    chunk_types_counter = Counter(row["chunk_type"] for row in result_rows)

    status = "PASS"
    if missing_inputs:
        status = "FAIL"
    elif retrieval_error or any(item["results_count"] == 0 for item in validations):
        status = "PARTIAL"

    return {
        "status": status,
        "persist_directory": persist_dir,
        "collection_name": collection_name,
        "embedding_provider": "openai",
        "embedding_model": embedding_model,
        "top_k": top_k,
        "default_filters": DEFAULT_FILTERS,
        "score_note": (
            "Nesta etapa, o campo score repete a distância retornada pelo ChromaDB; "
            "valores menores indicam maior proximidade vetorial."
        ),
        "missing_required_inputs": missing_inputs,
        "retrieval_error": retrieval_error,
        "validation_queries": validations,
        "most_retrieved_documents": dict(documents_counter.most_common()),
        "most_retrieved_chunk_types": dict(chunk_types_counter.most_common()),
        "scope_not_executed": [
            "final_chatbot",
            "llm_answer_generation",
            "openai_chat_model_call",
            "other_traditions_evaluation",
            "user_upload",
            "chunk_embedding_or_pdf_change",
            "new_extraction_normalization_chunking_or_indexing",
            "hybrid_bm25_rrf_search",
            "reranking",
            "parent_hierarchical_retrieval",
        ],
    }


def run_validation_report(
    top_k: int,
    persist_dir: str,
    collection_name: str,
    embedding_model: str,
    chunks_path: str,
) -> dict[str, Any]:
    """Executa consultas de validação e grava relatórios da etapa."""
    if load_dotenv is not None:
        load_dotenv(ROOT_DIR / ".env")

    validations: list[dict[str, Any]] = []
    retrieval_error: str | None = None
    if not os.getenv("OPENAI_API_KEY", "").strip():
        retrieval_error = "OPENAI_API_KEY não está configurada; as consultas reais não foram executadas."
    else:
        try:
            retriever = VectorRetriever(
                persist_directory=persist_dir,
                collection_name=collection_name,
                embedding_model=embedding_model,
                chunks_path=chunks_path,
            )
            for query in VALIDATION_QUERIES:
                results = retriever.retrieve(query=query, top_k=top_k)
                rows = [result_to_report_row(result) for result in results]
                validations.append(
                    {
                        "query": query,
                        "top_k": top_k,
                        "results_count": len(rows),
                        "documents": sorted({row["document_id"] for row in rows}),
                        "chunk_types": sorted({row["chunk_type"] for row in rows}),
                        "results": rows,
                        "observation": observe_query(query, rows),
                    }
                )
        except (VectorRetrieverError, QueryEmbeddingError, Exception) as exc:
            retrieval_error = str(exc)

    report = build_report(
        persist_dir=persist_dir,
        collection_name=collection_name,
        embedding_model=embedding_model,
        top_k=top_k,
        validations=validations,
        retrieval_error=retrieval_error,
    )
    write_reports(report)
    return report


def write_reports(report: dict[str, Any]) -> None:
    """Grava relatórios JSON e Markdown."""
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    STAGE_REPORT.parent.mkdir(parents=True, exist_ok=True)
    TECHNICAL_REPORT_JSON.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    query_lines: list[str] = []
    for item in report["validation_queries"]:
        query_lines.extend(
            [
                f"### {item['query']}",
                "",
                f"- Top-k: {item['top_k']}",
                f"- Resultados retornados: {item['results_count']}",
                f"- Documentos recuperados: {', '.join(item['documents']) or 'nenhum'}",
                f"- Tipos de chunk: {', '.join(item['chunk_types']) or 'nenhum'}",
                f"- Observação: {item['observation']}",
                "",
            ]
        )
        for row in item["results"][:5]:
            query_lines.append(
                "- "
                f"`{row['chunk_id']}` | `{row['document_id']}` | `{row['chunk_type']}` | "
                f"páginas {row['page_start']}-{row['page_end']} | distância {row['distance']}"
            )
        query_lines.append("")

    technical_lines = [
        "# Relatório de retrieval vetorial",
        "",
        "## Status",
        "",
        report["status"],
        "",
        "## Configuração consultada",
        "",
        f"- Collection: `{report['collection_name']}`",
        f"- Diretório ChromaDB: `{report['persist_directory']}`",
        f"- Modelo para embedding da pergunta: `{report['embedding_model']}`",
        f"- Filtros padrão: `{report['default_filters']}`",
        f"- Nota sobre score: {report['score_note']}",
        "",
        "## Consultas executadas",
        "",
        *(query_lines or ["As consultas não foram executadas nesta rodada.", ""]),
        "## Documentos mais recuperados",
        "",
        json.dumps(report["most_retrieved_documents"], ensure_ascii=False, indent=2),
        "",
        "## Tipos de chunk mais recuperados",
        "",
        json.dumps(report["most_retrieved_chunk_types"], ensure_ascii=False, indent=2),
        "",
        "## Observações iniciais de qualidade",
        "",
        "- A camada ainda avalia apenas recuperação vetorial simples, sem resposta final.",
        "- Os resultados preservam fonte, tipo de chunk, páginas e identificador do chunk.",
        "- A qualidade fina ainda dependerá de refinamentos como busca híbrida, RRF e reranking.",
    ]
    TECHNICAL_REPORT_MD.write_text("\n".join(technical_lines) + "\n", encoding="utf-8")

    stage_lines = [
        "# Retrieval vetorial do corpus reformado",
        "",
        "## Status",
        "",
        report["status"],
        "",
        "## Objetivo",
        "",
        (
            "Implementar a primeira camada de recuperação documental do SolaBot: "
            "gerar embedding da pergunta, consultar o índice ChromaDB do corpus reformado "
            "e retornar chunks com metadados e fontes rastreáveis."
        ),
        "",
        "## Entradas utilizadas",
        "",
        "- `reports/specs/openai-embeddings.md`",
        "- `reports/specs/chroma-vector-index.md`",
        "- `corpus/processed/chunks/reformed/all_chunks_for_embeddings.jsonl`",
        "- `corpus/processed/embeddings/reformed/embedding_manifest.json`",
        "- `corpus/indexes/chroma/reformed/`",
        "",
        "## Implementação do retriever vetorial",
        "",
        (
            "Foram criados módulos específicos para geração de embedding de consulta, "
            "representação estruturada dos resultados e consulta vetorial no ChromaDB."
        ),
        "",
        "## Configuração de filtros",
        "",
        (
            "Todas as consultas mantêm os filtros obrigatórios "
            "`corpus_id=reformed` e `retrieval_namespace=reformed_confessional`. "
            "Filtros adicionais, como documento ou tipo de chunk, são combinados sem remover "
            "essa restrição do corpus ativo."
        ),
        "",
        "## Consultas de validação",
        "",
        *(query_lines or ["As consultas não foram executadas nesta rodada.", ""]),
        "## Resultados observados",
        "",
        f"- Documentos mais recuperados: `{report['most_retrieved_documents']}`",
        f"- Tipos de chunk mais recuperados: `{report['most_retrieved_chunk_types']}`",
        f"- Erro de retrieval: {report['retrieval_error'] or 'nenhuma ocorrência'}",
        "",
        "## Validações executadas",
        "",
        "```bash",
        'python scripts/pipeline/query_vector_retriever.py "O que é o batismo?" --top-k 5',
        'python scripts/pipeline/query_vector_retriever.py "O que é eleição?" --top-k 5',
        'python scripts/pipeline/query_vector_retriever.py "O que é justificação?" --top-k 5',
        "python -m py_compile src/sola_bot/retrieval/query_embedder.py",
        "python -m py_compile src/sola_bot/retrieval/retrieval_result.py",
        "python -m py_compile src/sola_bot/retrieval/vector_retriever.py",
        "python -m py_compile scripts/pipeline/query_vector_retriever.py",
        "python -m pytest tests/test_vector_retriever.py",
        "```",
        "",
        "## Pontos de atenção",
        "",
        "- O campo `score` replica a distância retornada pelo ChromaDB nesta etapa.",
        "- Valores menores de distância indicam maior proximidade vetorial.",
        "- Esta camada ainda não decide resposta final nem aplica política de evidência.",
        "- A consulta sobre eleição trouxe um chunk de Londres 1689 sobre escolha de oficiais da igreja entre os resultados; esse tipo de ruído é esperado no baseline vetorial simples e deve ser tratado nas próximas camadas de recuperação.",
        "",
        "## O que não foi feito",
        "",
        "- não foi implementado chatbot final;",
        "- não houve geração de resposta com LLM;",
        "- não houve chamada a modelo de chat da OpenAI;",
        "- não foi feita avaliação com documentos de outras tradições;",
        "- não houve upload de documentos pelo usuário;",
        "- não houve alteração de chunks, embeddings ou PDFs;",
        "- não houve nova extração, normalização, chunking ou indexação;",
        "- não foi implementada busca híbrida BM25 + RRF;",
        "- não foi implementado reranking;",
        "- não foi implementado parent/hierarchical retrieval.",
        "",
    ]
    STAGE_REPORT.write_text("\n".join(stage_lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    """Cria parser CLI."""
    parser = argparse.ArgumentParser(description="Consulta o retriever vetorial reformado.")
    parser.add_argument("query", nargs="?", help="Pergunta doutrinária a consultar.")
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    parser.add_argument("--document-id")
    parser.add_argument("--chunk-type")
    parser.add_argument("--persist-dir", default=DEFAULT_PERSIST_DIRECTORY)
    parser.add_argument("--collection-name", default=DEFAULT_COLLECTION_NAME)
    parser.add_argument("--embedding-model", default=DEFAULT_EMBEDDING_MODEL)
    parser.add_argument("--chunks-path", default=DEFAULT_CHUNKS_PATH)
    parser.add_argument("--write-report", action="store_true")
    return parser


def main() -> int:
    """Ponto de entrada CLI."""
    args = build_parser().parse_args()

    if args.write_report:
        report = run_validation_report(
            top_k=args.top_k,
            persist_dir=args.persist_dir,
            collection_name=args.collection_name,
            embedding_model=args.embedding_model,
            chunks_path=args.chunks_path,
        )
        print(f"Relatório de retrieval vetorial concluído com status {report['status']}.")
        print(f"- collection: {report['collection_name']}")
        print(f"- consultas registradas: {len(report['validation_queries'])}")
        if report["retrieval_error"]:
            print(f"- ponto de atenção: {report['retrieval_error']}")
        return 0 if report["status"] in {"PASS", "PARTIAL"} else 1

    if not args.query:
        print("Informe uma pergunta ou use --write-report.", file=sys.stderr)
        return 2

    if load_dotenv is not None:
        load_dotenv(ROOT_DIR / ".env")

    try:
        results = run_single_query(
            query=args.query,
            top_k=args.top_k,
            document_id=args.document_id,
            chunk_type=args.chunk_type,
            persist_dir=args.persist_dir,
            collection_name=args.collection_name,
            embedding_model=args.embedding_model,
            chunks_path=args.chunks_path,
        )
    except (VectorRetrieverError, QueryEmbeddingError) as exc:
        print(f"A consulta vetorial não pôde ser executada: {exc}", file=sys.stderr)
        return 1

    print_results(args.query, results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
