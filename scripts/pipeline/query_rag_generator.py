"""Consulta a geração RAG com fontes do corpus reformado."""

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

from sola_bot.generation.citation_formatter import format_citations  # noqa: E402
from sola_bot.generation.rag_answer import RagAnswer  # noqa: E402
from sola_bot.generation.rag_generator import DEFAULT_CHAT_MODEL, RagGenerator  # noqa: E402


REPORT_DIR = ROOT_DIR / "corpus" / "reports" / "generation"
STAGE_REPORT = ROOT_DIR / "reports" / "specs" / "rag-answer-generation.md"
TECHNICAL_REPORT_MD = REPORT_DIR / "rag-answer-generation-report.md"
TECHNICAL_REPORT_JSON = REPORT_DIR / "rag-answer-generation-report.json"
DEFAULT_TEMPERATURE = 0.1
DEFAULT_MAX_OUTPUT_TOKENS = 1200
MAIN_VALIDATION_QUERIES = [
    "O que é o batismo?",
    "O que é necessário para a salvação?",
    "O que é eleição?",
    "O que é justificação?",
    "O que a tradição reformada ensina sobre as Escrituras?",
    "O crente pode perder a salvação?",
    "O que é regeneração?",
    "O que é expiação?",
]
REFUSAL_VALIDATION_QUERIES = [
    "O que a tradição reformada ensina sobre a sucessão papal?",
    "Qual é a posição reformada sobre um documento que não está no corpus?",
    "Segundo os documentos reformados disponíveis, qual é a doutrina da assunção de Maria?",
]
REQUIRED_INPUTS = [
    ROOT_DIR / "reports" / "specs" / "retrieval-pipeline.md",
    ROOT_DIR / "corpus" / "reports" / "retrieval" / "retrieval-pipeline-report.md",
    ROOT_DIR / "corpus" / "reports" / "retrieval" / "retrieval-pipeline-report.json",
    ROOT_DIR / "corpus" / "processed" / "chunks" / "reformed" / "all_chunks_for_embeddings.jsonl",
    ROOT_DIR / "corpus" / "processed" / "embeddings" / "reformed" / "embedding_manifest.json",
    ROOT_DIR / "corpus" / "indexes" / "chroma" / "reformed",
    ROOT_DIR / "config" / "retrieval_config.example.yaml",
    ROOT_DIR / "requirements.txt",
]


def relative_path(path: Path) -> str:
    return path.relative_to(ROOT_DIR).as_posix()


def load_environment() -> None:
    if load_dotenv is not None:
        load_dotenv(ROOT_DIR / ".env")


def dependency_status() -> dict[str, bool]:
    load_environment()
    return {
        "openai_available": importlib.util.find_spec("openai") is not None,
        "sentence_transformers_available": importlib.util.find_spec("sentence_transformers") is not None,
        "rank_bm25_available": importlib.util.find_spec("rank_bm25") is not None,
        "chromadb_available": importlib.util.find_spec("chromadb") is not None,
        "openai_api_key_configured": bool(os.getenv("OPENAI_API_KEY", "").strip()),
        "openai_chat_model_configured": bool(os.getenv("OPENAI_CHAT_MODEL", "").strip()),
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
    if not status["openai_available"]:
        raise RuntimeError("openai não está instalado.")
    if not status["sentence_transformers_available"]:
        raise RuntimeError("sentence-transformers não está instalado.")
    if not status["rank_bm25_available"]:
        raise RuntimeError("rank-bm25 não está instalado.")
    if not status["chromadb_available"]:
        raise RuntimeError("chromadb não está instalado.")
    if not status["openai_api_key_configured"]:
        raise RuntimeError("OPENAI_API_KEY não está configurada.")


def make_generator(args: argparse.Namespace) -> RagGenerator:
    return RagGenerator(
        model=args.model,
        temperature=args.temperature,
        max_output_tokens=args.max_output_tokens,
    )


def run_single_query(args: argparse.Namespace) -> RagAnswer:
    check_runtime_requirements()
    generator = make_generator(args)
    return generator.answer(
        query=args.query,
        filters=build_filters(args.document_id, args.chunk_type),
    )


def print_answer(answer: RagAnswer) -> None:
    print(f"Pergunta: {answer.query}")
    print(f"Status: {answer.status}")
    print(f"Modelo: {answer.model}")
    print(f"Contextos usados: {answer.used_context_count}")
    print(f"Documentos usados: {', '.join(answer.used_documents) or 'nenhum'}")
    if answer.refusal_reason:
        print(f"Motivo de recusa: {answer.refusal_reason}")
    print()
    print(answer.answer)
    if answer.citations:
        print()
        print("Fontes usadas:")
        for line in format_citations(answer.citations):
            print(f"- {line}")


def answer_to_report_row(answer: RagAnswer, query_type: str) -> dict[str, Any]:
    retrieval_package = answer.metadata.get("retrieval_package", {})
    evidence_decision = answer.metadata.get("evidence_decision", {})
    return {
        "query": answer.query,
        "query_type": query_type,
        "status": answer.status,
        "model": answer.model,
        "used_documents": answer.used_documents,
        "used_context_count": answer.used_context_count,
        "total_context_chars": retrieval_package.get("total_context_chars", 0),
        "citations": [citation.to_dict() for citation in answer.citations],
        "used_sources": answer.used_sources,
        "refused": answer.status == "refused",
        "refusal_reason": answer.refusal_reason,
        "answer": answer.answer,
        "technical_error": answer.metadata.get("openai_error") or answer.metadata.get("retrieval_error"),
        "evidence_decision": evidence_decision,
    }


def run_validation_report(args: argparse.Namespace) -> dict[str, Any]:
    status = dependency_status()
    missing_inputs = missing_required_inputs()
    validation_rows: list[dict[str, Any]] = []
    setup_error: str | None = None
    model = args.model or os.getenv("OPENAI_CHAT_MODEL") or DEFAULT_CHAT_MODEL

    if missing_inputs:
        setup_error = "Entradas obrigatórias ausentes: " + ", ".join(missing_inputs)
    elif not status["openai_available"]:
        setup_error = "openai não está instalado."
    elif not status["sentence_transformers_available"]:
        setup_error = "sentence-transformers não está instalado."
    elif not status["rank_bm25_available"]:
        setup_error = "rank-bm25 não está instalado."
    elif not status["chromadb_available"]:
        setup_error = "chromadb não está instalado."
    elif not status["openai_api_key_configured"]:
        setup_error = "OPENAI_API_KEY não está configurada."
    else:
        generator = make_generator(args)
        filters = build_filters(args.document_id, args.chunk_type)
        for query in MAIN_VALIDATION_QUERIES:
            validation_rows.append(answer_to_report_row(generator.answer(query, filters=filters), "main"))
        for query in REFUSAL_VALIDATION_QUERIES:
            validation_rows.append(answer_to_report_row(generator.answer(query, filters=filters), "refusal"))

    status_value = report_status(setup_error, validation_rows)
    documents_counter = Counter(
        document for row in validation_rows for document in row["used_documents"]
    )
    status_counter = Counter(row["status"] for row in validation_rows)
    report = {
        "status": status_value,
        "configuration": {
            "provider": "openai",
            "model": model,
            "temperature": args.temperature,
            "max_output_tokens": args.max_output_tokens,
            "require_citations": True,
            "answer_language": "pt-BR",
            "use_retrieval_pipeline": True,
            "default_filters": {
                "corpus_id": "reformed",
                "retrieval_namespace": "reformed_confessional",
            },
        },
        "dependency_status": status,
        "missing_required_inputs": missing_inputs,
        "setup_error": setup_error,
        "validation_queries": validation_rows,
        "status_counts": dict(status_counter.most_common()),
        "documents_used": dict(documents_counter.most_common()),
        "generated_answers_count": sum(1 for row in validation_rows if row["status"] == "answered"),
        "refusals_count": sum(1 for row in validation_rows if row["status"] == "refused"),
        "errors_count": sum(1 for row in validation_rows if row["status"] == "error"),
        "methodology_notes": {
            "evidence_policy": "general_documentary_sufficiency_criteria",
            "topic_specific_hardcoded_refusals": False,
            "official_generation_path": [
                "RagGenerator",
                "RetrievalPipeline",
                "EvidencePolicy",
                "PromptBuilder",
                "CitationFormatter",
                "OpenAI",
                "RagAnswer",
            ],
            "refusal_criteria": [
                "no_context",
                "missing_source_map",
                "context_too_short",
                "only_introductory_context",
                "no_doctrinal_context",
                "insufficient_query_context_overlap",
                "requested_material_outside_active_corpus",
            ],
            "tests_updated_for_generic_refusal_policy": True,
        },
        "scope_not_executed": [
            "web_interface",
            "user_document_upload",
            "other_traditions_evaluation",
            "ragas_or_ares_evaluation",
            "chunk_embedding_pdf_change",
            "new_extraction_normalization_chunking_or_indexing",
            "model_training_or_fine_tuning",
        ],
    }
    write_reports(report)
    return report


def report_status(setup_error: str | None, rows: list[dict[str, Any]]) -> str:
    if setup_error and "Entradas obrigatórias" in setup_error:
        return "FAIL"
    if setup_error:
        return "PARTIAL"
    if not rows:
        return "PARTIAL"
    if any(row["status"] == "error" for row in rows):
        return "PARTIAL"
    main_rows = [row for row in rows if row["query_type"] == "main"]
    refusal_rows = [row for row in rows if row["query_type"] == "refusal"]
    if not main_rows or any(row["status"] != "answered" for row in main_rows):
        return "PARTIAL"
    if not refusal_rows or not any(row["status"] == "refused" for row in refusal_rows):
        return "PARTIAL"
    return "PASS"


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
        "# Geração RAG com fontes do corpus reformado",
        "",
        "## Status",
        "",
        report["status"],
        "",
        "## Entradas",
        "",
        "- `reports/specs/retrieval-pipeline.md`",
        "- `corpus/reports/retrieval/retrieval-pipeline-report.md`",
        "- `corpus/reports/retrieval/retrieval-pipeline-report.json`",
        "- `corpus/processed/chunks/reformed/all_chunks_for_embeddings.jsonl`",
        "- `corpus/processed/embeddings/reformed/embedding_manifest.json`",
        "- `corpus/indexes/chroma/reformed/`",
        "- `config/retrieval_config.example.yaml`",
        "- `requirements.txt`",
        "",
        "## Código",
        "",
        "- `src/sola_bot/generation/prompt_builder.py`",
        "- `src/sola_bot/generation/evidence_policy.py`",
        "- `src/sola_bot/generation/citation_formatter.py`",
        "- `src/sola_bot/generation/rag_answer.py`",
        "- `src/sola_bot/generation/rag_generator.py`",
        "- `scripts/pipeline/query_rag_generator.py`",
        "",
        "## Configuração",
        "",
        f"- Provider: `{report['configuration']['provider']}`",
        f"- Modelo: `{report['configuration']['model']}`",
        f"- Temperature: `{report['configuration']['temperature']}`",
        f"- Max output tokens: `{report['configuration']['max_output_tokens']}`",
        f"- Filtros: `{report['configuration']['default_filters']}`",
        "",
        "## Implementação",
        "",
        "- O caminho oficial de geração é `RagGenerator -> RetrievalPipeline -> EvidencePolicy -> PromptBuilder -> CitationFormatter -> OpenAI -> RagAnswer`.",
        "- `RagGenerator` chama a `RetrievalPipeline`, aplica `EvidencePolicy`, monta prompt e chama OpenAI quando permitido.",
        "- `EvidencePolicy` bloqueia geração sem contexto suficiente, sem source_map, apenas introdutória, sem contexto doutrinário ou sem sobreposição mínima com a pergunta.",
        "- A política de evidência foi generalizada; não há recusa por lista fixa de temas específicos.",
        "- `CitationFormatter` transforma `source_map` em citações rastreáveis.",
        "- `RagAnswer` registra resposta, status, fontes, recusas e metadados técnicos.",
        "",
        "## Consultas",
        "",
        *(summary_lines or ["Consultas não executadas.", ""]),
        "## Resultados agregados",
        "",
        f"- Respostas geradas: `{report['generated_answers_count']}`",
        f"- Recusas geradas: `{report['refusals_count']}`",
        f"- Erros técnicos: `{report['errors_count']}`",
        f"- Status por consulta: `{report['status_counts']}`",
        f"- Documentos usados: `{report['documents_used']}`",
        f"- Erro de preparação: `{report['setup_error'] or 'nenhum'}`",
        "",
        "## Validações executadas",
        "",
        "```bash",
        'python scripts/pipeline/query_rag_generator.py "O que é o batismo?"',
        'python scripts/pipeline/query_rag_generator.py "O que é eleição?"',
        'python scripts/pipeline/query_rag_generator.py "O que é justificação?"',
        'python scripts/pipeline/query_rag_generator.py "Segundo os documentos reformados disponíveis, qual é a doutrina da assunção de Maria?"',
        "python scripts/pipeline/query_rag_generator.py --write-report",
        "python -m py_compile src/sola_bot/generation/prompt_builder.py",
        "python -m py_compile src/sola_bot/generation/evidence_policy.py",
        "python -m py_compile src/sola_bot/generation/citation_formatter.py",
        "python -m py_compile src/sola_bot/generation/rag_answer.py",
        "python -m py_compile src/sola_bot/generation/rag_generator.py",
        "python -m py_compile src/sola_bot/generation/rag_chain.py",
        "python -m py_compile src/sola_bot/generation/source_grounded_prompt.py",
        "python -m py_compile scripts/pipeline/query_rag_generator.py",
        "python -m pytest tests/test_rag_answer_generation.py",
        "```",
        "",
        "## Pontos de atenção",
        "",
        f"- Dependências: `{report['dependency_status']}`",
        f"- Entradas ausentes: `{report['missing_required_inputs']}`",
        f"- Bloqueio: `{report['setup_error'] or 'nenhum'}`",
        "- As recusas são aplicadas por critérios documentais gerais e registram a razão técnica da decisão.",
        "- Os testes cobrem recusa sem contexto, sem source_map, apenas introdutória, por baixa aderência entre pergunta e contexto e por pedido explicitamente fora do corpus.",
        "",
        "## Fora do escopo",
        "",
        "- interface web",
        "- upload de documentos pelo usuário",
        "- avaliação com documentos de outras tradições",
        "- avaliação automática com RAGAS ou ARES",
        "- alteração de chunks, embeddings ou PDFs",
        "- nova extração, normalização, chunking ou indexação",
        "- treinamento ou fine-tuning de modelo",
    ]
    STAGE_REPORT.write_text("\n".join(stage_lines) + "\n", encoding="utf-8")

    technical_lines = [
        "# Relatório de geração RAG com fontes",
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
        f"- Respostas geradas: `{report['generated_answers_count']}`",
        f"- Recusas geradas: `{report['refusals_count']}`",
        f"- Erros técnicos: `{report['errors_count']}`",
        "",
        "Documentos usados:",
        "",
        json.dumps(report["documents_used"], ensure_ascii=False, indent=2),
        "",
        "Status por consulta:",
        "",
        json.dumps(report["status_counts"], ensure_ascii=False, indent=2),
        "",
        "## Notas técnicas",
        "",
        "- A geração usa OpenAI apenas após decisão positiva da política de evidência.",
        "- Recusas não chamam o modelo de chat.",
        "- As citações são derivadas do `source_map` do pacote final de retrieval.",
        "- A política de evidência usa critérios documentais gerais; regras hardcoded por tema específico foram removidas.",
        "- O caminho oficial de geração é `RagGenerator` com `PromptBuilder`; `rag_chain.py` e `source_grounded_prompt.py` permanecem apenas como compatibilidade.",
        "",
        "## Limitações",
        "",
        "- A política de recusa é inicial e baseada em metadados, tamanho de contexto e sobreposição lexical.",
        "- A etapa não faz avaliação automática de qualidade.",
    ]
    TECHNICAL_REPORT_MD.write_text("\n".join(technical_lines) + "\n", encoding="utf-8")


def render_query_summary(report: dict[str, Any]) -> list[str]:
    if not report["validation_queries"]:
        return []
    lines = [
        "| Consulta | Tipo | Status | Contextos | Documentos | Recusa | Modelo |",
        "| --- | --- | --- | ---: | --- | --- | --- |",
    ]
    for item in report["validation_queries"]:
        lines.append(
            "| "
            f"{item['query']} | "
            f"{item['query_type']} | "
            f"{item['status']} | "
            f"{item['used_context_count']} | "
            f"{', '.join(item['used_documents']) or 'nenhum'} | "
            f"{item['refusal_reason'] or 'não'} | "
            f"{item['model']} |"
        )
    lines.append("")
    return lines


def render_query_details(report: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    for item in report["validation_queries"]:
        citation_lines = [
            f"{citation['source_id']}: {citation['document']} ({citation['pages'] or 'página não informada'})"
            for citation in item["citations"]
        ]
        answer_preview = " ".join(item["answer"].split())[:600]
        lines.extend(
            [
                f"### {item['query']}",
                "",
                f"- Tipo: `{item['query_type']}`",
                f"- Status: `{item['status']}`",
                f"- Modelo: `{item['model']}`",
                f"- Contextos usados: `{item['used_context_count']}`",
                f"- Total de caracteres de contexto: `{item['total_context_chars']}`",
                f"- Documentos usados: `{item['used_documents']}`",
                f"- Fontes citadas: `{citation_lines}`",
                f"- Recusa: `{item['refused']}`",
                f"- Motivo de recusa: `{item['refusal_reason'] or 'nenhum'}`",
                f"- Erro técnico: `{item['technical_error'] or 'nenhum'}`",
                f"- Prévia da resposta: {answer_preview}",
                "",
            ]
        )
    return lines


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Gera resposta RAG com fontes do corpus reformado.")
    parser.add_argument("query", nargs="?", help="Pergunta doutrinária a consultar.")
    parser.add_argument("--document-id")
    parser.add_argument("--chunk-type")
    parser.add_argument("--model", default=None)
    parser.add_argument("--temperature", type=float, default=DEFAULT_TEMPERATURE)
    parser.add_argument("--max-output-tokens", type=int, default=DEFAULT_MAX_OUTPUT_TOKENS)
    parser.add_argument("--write-report", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()

    if args.write_report:
        report = run_validation_report(args)
        print(f"Relatório de geração RAG concluído com status {report['status']}.")
        if report["setup_error"]:
            print(f"- bloqueio: {report['setup_error']}")
        return 0 if report["status"] in {"PASS", "PARTIAL"} else 1

    if not args.query:
        print("Informe uma pergunta ou use --write-report.", file=sys.stderr)
        return 2

    try:
        answer = run_single_query(args)
    except Exception as exc:
        print(f"A geração RAG não pôde ser executada: {exc}", file=sys.stderr)
        return 1

    print_answer(answer)
    return 0 if answer.status in {"answered", "refused", "partial"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
