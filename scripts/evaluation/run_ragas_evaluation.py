"""Executa avaliação automática com RAGAS sobre o JSONL do AIA."""

from __future__ import annotations

import argparse
import csv
import importlib.metadata
import inspect
import json
import math
import os
import sys
import warnings
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None


ROOT_DIR = Path(__file__).resolve().parents[2]

RAGAS_COLUMNS = ["question", "answer", "contexts", "ground_truth"]
SCOPE_COLUMNS = [
    "id",
    "categoria",
    "documentos_esperados",
    "escopo_esperado",
    "mistura_permitida",
    "referencia_esperada",
    "deve_responder",
    "observacao",
]
CSV_BASE_COLUMNS = [
    *SCOPE_COLUMNS,
    "ragas_evaluation_scope",
    "question",
    "answer",
    "ground_truth",
    "context_count",
    "source_count",
    "error",
    "warning",
    "ragas_skipped_reason",
]
RAGAS_DATASET_ALIASES = {
    "question",
    "answer",
    "contexts",
    "ground_truth",
    "user_input",
    "response",
    "retrieved_contexts",
    "reference",
}
DEFAULT_METRICS = [
    "faithfulness",
    "answer_relevancy",
    "context_precision",
    "context_recall",
]
DATASET_COLUMN_MAPPING = {
    "question": "question ou user_input",
    "answer": "answer ou response",
    "contexts": "contexts ou retrieved_contexts",
    "ground_truth": "ground_truth ou reference",
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            text = line.strip()
            if not text:
                continue
            try:
                item = json.loads(text)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Linha JSONL inválida {line_number}: {exc}") from exc
            if not isinstance(item, dict):
                raise ValueError(f"Linha JSONL {line_number} não contém um objeto JSON.")
            rows.append(item)
    return rows


def validate_required_fields(rows: list[dict[str, Any]]) -> None:
    missing_by_row: list[str] = []
    for index, row in enumerate(rows, start=1):
        missing = [column for column in RAGAS_COLUMNS if column not in row]
        if missing:
            row_id = row.get("id") or f"linha {index}"
            missing_by_row.append(f"{row_id}: {', '.join(missing)}")
    if missing_by_row:
        raise ValueError("JSONL sem campos obrigatórios do RAGAS: " + "; ".join(missing_by_row))


def prepare_eval_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[int], list[str | None]]:
    eval_rows: list[dict[str, Any]] = []
    eval_indexes: list[int] = []
    skip_reasons: list[str | None] = []
    for index, row in enumerate(rows):
        row["ragas_evaluation_scope"] = ragas_evaluation_scope(row)
        reason = skip_reason(row)
        skip_reasons.append(reason)
        if reason is not None:
            continue
        eval_rows.append(
            {
                "question": row["question"],
                "answer": row["answer"],
                "contexts": row["contexts"],
                "ground_truth": row["ground_truth"],
            }
        )
        eval_indexes.append(index)
    return eval_rows, eval_indexes, skip_reasons


def skip_reason(row: dict[str, Any]) -> str | None:
    if row.get("error"):
        return "linha possui erro da execução do chatbot"
    if not str(row.get("question") or "").strip():
        return "question vazio"
    if not str(row.get("answer") or "").strip():
        return "answer vazio"
    if should_exclude_from_primary_ragas(row):
        return (
            "fora da média RAGAS principal: "
            f"deve_responder = {str(row.get('deve_responder') or '').strip() or 'não informado'}"
        )
    if not isinstance(row.get("contexts"), list):
        return "contexts não é lista"
    if not row.get("contexts"):
        return "contexts vazio"
    if not str(row.get("ground_truth") or "").strip():
        return "ground_truth vazio"
    return None


def ragas_evaluation_scope(row: dict[str, Any]) -> str:
    """Classifica a linha para métricas principais ou avaliação comportamental."""
    return (
        "primary_answerable"
        if normalize_flag(row.get("deve_responder")) == "sim"
        else "behavioral_ambiguous_or_out_of_scope"
    )


def should_exclude_from_primary_ragas(row: dict[str, Any]) -> bool:
    """Remove ambíguas e fora do escopo das médias RAGAS de resposta/contexto."""
    return ragas_evaluation_scope(row) != "primary_answerable"


def normalize_flag(value: Any) -> str:
    return str(value or "").strip().lower()


def load_ragas_metrics(
    metric_names: list[str],
    llm: Any | None = None,
    embeddings: Any | None = None,
) -> list[Any]:
    metrics = []
    missing = []
    for name in metric_names:
        metric = load_collection_metric(name, llm=llm, embeddings=embeddings)
        if metric is None:
            metric = load_legacy_metric(name)
        if metric is None:
            missing.append(name)
            continue
        metrics.append(metric)
    if missing:
        raise ValueError("Métricas RAGAS não encontradas: " + ", ".join(missing))
    return metrics


def load_collection_metric(
    name: str,
    llm: Any | None,
    embeddings: Any | None,
) -> Any | None:
    """Carrega métricas da API nova do RAGAS quando o runtime é compatível."""
    try:
        from ragas.metrics import collections
    except ImportError:
        return None

    collection_module = getattr(collections, name, None)
    metric_module = getattr(collection_module, "metric", None)
    if metric_module is None:
        return None

    class_names = {
        "context_precision": "ContextPrecision",
        "context_recall": "ContextRecall",
        "faithfulness": "Faithfulness",
        "answer_relevancy": "AnswerRelevancy",
    }
    metric_class = getattr(metric_module, class_names.get(name, ""), None)
    if metric_class is None:
        return None

    try:
        if name == "answer_relevancy":
            return metric_class(llm=llm, embeddings=embeddings)
        return metric_class(llm=llm)
    except (TypeError, ValueError):
        return None


def load_legacy_metric(name: str) -> Any | None:
    """Fallback para RAGAS 0.4.x com aviso de depreciação silenciado."""
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=r"Importing .* from 'ragas.metrics' is deprecated.*",
            category=DeprecationWarning,
        )
        import ragas.metrics as ragas_metrics

        return getattr(ragas_metrics, name, None)


def evaluate_rows(args: argparse.Namespace, eval_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if load_dotenv is not None:
        load_dotenv(ROOT_DIR / ".env")

    from datasets import Dataset
    from ragas import evaluate

    llm, embeddings, model_config = build_ragas_model_config()
    metrics = load_ragas_metrics(args.metrics, llm=llm, embeddings=embeddings)
    dataset = Dataset.from_list(eval_rows)
    result = evaluate(**build_evaluate_kwargs(evaluate, dataset, metrics, llm, embeddings, args))
    records = result_to_records(result)
    for record in records:
        record["_ragas_model_config"] = model_config
    return records


def build_evaluate_kwargs(
    evaluate_func: Any,
    dataset: Any,
    metrics: list[Any],
    llm: Any | None,
    embeddings: Any | None,
    args: argparse.Namespace,
) -> dict[str, Any]:
    supported = set(inspect.signature(evaluate_func).parameters)
    candidates = {
        "dataset": dataset,
        "metrics": metrics,
        "llm": llm,
        "embeddings": embeddings,
        "raise_exceptions": args.raise_exceptions,
        "show_progress": not args.no_progress,
        "batch_size": args.batch_size,
    }
    return {
        key: value
        for key, value in candidates.items()
        if key in supported and value is not None
    }


def build_ragas_model_config() -> tuple[Any | None, Any | None, dict[str, Any]]:
    llm_model = first_env_value("RAGAS_LLM_MODEL", "OPENAI_CHAT_MODEL")
    embedding_model = first_env_value("RAGAS_EMBEDDING_MODEL", "OPENAI_EMBEDDING_MODEL")
    config = {
        "llm_model": llm_model,
        "embedding_model": embedding_model,
        "llm_source": env_source("RAGAS_LLM_MODEL", "OPENAI_CHAT_MODEL"),
        "embedding_source": env_source("RAGAS_EMBEDDING_MODEL", "OPENAI_EMBEDDING_MODEL"),
        "explicit_clients": False,
    }
    llm = None
    embeddings = None
    if not os.getenv("OPENAI_API_KEY", "").strip():
        return llm, embeddings, config

    try:
        from langchain_openai import ChatOpenAI, OpenAIEmbeddings
    except ImportError:
        return llm, embeddings, config

    if llm_model:
        llm = ChatOpenAI(model=llm_model, temperature=0)
    if embedding_model:
        embeddings = OpenAIEmbeddings(model=embedding_model)
    config["explicit_clients"] = bool(llm or embeddings)
    return llm, embeddings, config


def first_env_value(*names: str) -> str | None:
    for name in names:
        value = os.getenv(name, "").strip()
        if value:
            return value
    return None


def env_source(*names: str) -> str | None:
    for name in names:
        if os.getenv(name, "").strip():
            return name
    return None


def result_to_records(result: Any) -> list[dict[str, Any]]:
    if hasattr(result, "to_pandas"):
        dataframe = result.to_pandas()
        return [
            {key: normalize_json_value(value) for key, value in record.items()}
            for record in dataframe.to_dict(orient="records")
        ]
    if hasattr(result, "scores"):
        scores = result.scores
        if isinstance(scores, list):
            return [
                {key: normalize_json_value(value) for key, value in score.items()}
                for score in scores
            ]
    if isinstance(result, dict):
        return [{key: normalize_json_value(value) for key, value in result.items()}]
    raise TypeError(f"Não foi possível converter resultado RAGAS: {type(result).__name__}")


def merge_results(
    original_rows: list[dict[str, Any]],
    eval_indexes: list[int],
    skip_reasons: list[str | None],
    ragas_records: list[dict[str, Any]],
    setup_error: str | None = None,
) -> list[dict[str, Any]]:
    merged = [dict(row) for row in original_rows]
    for index, reason in enumerate(skip_reasons):
        merged[index]["ragas_skipped_reason"] = reason
    if setup_error:
        for row in merged:
            row["ragas_error"] = setup_error
        return merged

    if len(ragas_records) != len(eval_indexes):
        message = (
            f"RAGAS retornou {len(ragas_records)} linhas para {len(eval_indexes)} "
            "linhas avaliáveis."
        )
        for row in merged:
            row["ragas_error"] = message
        return merged

    for original_index, ragas_record in zip(eval_indexes, ragas_records):
        ragas_record.pop("_ragas_model_config", None)
        score_values = {
            key: value
            for key, value in ragas_record.items()
            if key not in RAGAS_DATASET_ALIASES
        }
        merged[original_index].update(score_values)
        merged[original_index]["ragas_skipped_reason"] = None
    return merged


def normalize_json_value(value: Any) -> Any:
    if isinstance(value, float) and math.isnan(value):
        return None
    if hasattr(value, "item"):
        try:
            return normalize_json_value(value.item())
        except Exception:
            return str(value)
    if isinstance(value, dict):
        return {key: normalize_json_value(inner) for key, inner in value.items()}
    if isinstance(value, list):
        return [normalize_json_value(inner) for inner in value]
    return value


def score_columns(rows: list[dict[str, Any]]) -> list[str]:
    excluded = {
        *CSV_BASE_COLUMNS,
        "contexts",
        "retrieved_sources",
        "ragas_error",
        "chatbot_status",
        "raw_response",
        "_ragas_model_config",
        "ragas_metric_warning",
    }
    result: list[str] = []
    for row in rows:
        for key, value in row.items():
            if key in excluded or key in result:
                continue
            if isinstance(value, (int, float)) or value is None:
                result.append(key)
    return result


def requested_score_columns(rows: list[dict[str, Any]], metric_names: list[str]) -> list[str]:
    existing = score_columns(rows)
    result = []
    for metric in metric_names:
        if metric not in result:
            result.append(metric)
    for metric in existing:
        if metric not in result:
            result.append(metric)
    return result


def aggregate_scores(rows: list[dict[str, Any]], scores: list[str]) -> dict[str, float | None]:
    aggregates: dict[str, float | None] = {}
    for score in scores:
        values = [
            float(row[score])
            for row in rows
            if isinstance(row.get(score), (int, float)) and row.get(score) is not None
        ]
        aggregates[score] = sum(values) / len(values) if values else None
    return aggregates


def metrics_by_category(rows: list[dict[str, Any]], scores: list[str]) -> dict[str, dict[str, Any]]:
    categories = sorted({str(row.get("categoria") or "sem_categoria") for row in rows})
    result: dict[str, dict[str, Any]] = {}
    for category in categories:
        category_rows = [
            row
            for row in rows
            if str(row.get("categoria") or "sem_categoria") == category
            and not row.get("ragas_skipped_reason")
        ]
        result[category] = {
            "count": len(category_rows),
            **aggregate_scores(category_rows, scores),
        }
    return result


def behavioral_evaluation_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Resume linhas avaliadas fora das médias RAGAS principais."""
    behavioral_rows = [
        row
        for row in rows
        if row.get("ragas_evaluation_scope") == "behavioral_ambiguous_or_out_of_scope"
    ]
    by_category: dict[str, int] = {}
    by_expected_behavior: dict[str, int] = {}
    by_chatbot_status: dict[str, int] = {}
    items: list[dict[str, Any]] = []
    for row in behavioral_rows:
        category = str(row.get("categoria") or "sem_categoria")
        expected_behavior = str(row.get("deve_responder") or "não informado")
        chatbot_status = str(row.get("chatbot_status") or "não informado")
        by_category[category] = by_category.get(category, 0) + 1
        by_expected_behavior[expected_behavior] = by_expected_behavior.get(expected_behavior, 0) + 1
        by_chatbot_status[chatbot_status] = by_chatbot_status.get(chatbot_status, 0) + 1
        items.append(
            {
                "id": row.get("id"),
                "categoria": category,
                "deve_responder": expected_behavior,
                "chatbot_status": chatbot_status,
                "context_count": len(row.get("contexts") or []),
                "source_count": len(row.get("retrieved_sources") or []),
                "ragas_skipped_reason": row.get("ragas_skipped_reason"),
                "error": row.get("error") or row.get("ragas_error"),
                "warning": row.get("warning"),
            }
        )
    return {
        "count": len(behavioral_rows),
        "by_category": by_category,
        "by_expected_behavior": by_expected_behavior,
        "by_chatbot_status": by_chatbot_status,
        "items": items,
    }


def mark_metric_warnings(rows: list[dict[str, Any]], metric_names: list[str]) -> None:
    for row in rows:
        if row.get("ragas_skipped_reason") or row.get("ragas_error"):
            continue
        missing = [
            metric
            for metric in metric_names
            if metric not in row or row.get(metric) is None
        ]
        if missing:
            row["ragas_metric_warning"] = (
                "Métricas sem valor para esta linha: " + ", ".join(missing)
            )


def ragas_environment_summary(ragas_records: list[dict[str, Any]]) -> dict[str, Any]:
    model_config = {}
    for record in ragas_records:
        if isinstance(record.get("_ragas_model_config"), dict):
            model_config = record["_ragas_model_config"]
            break
    try:
        ragas_version = importlib.metadata.version("ragas")
    except importlib.metadata.PackageNotFoundError:
        ragas_version = None
    return {
        "ragas_version": ragas_version,
        "dataset_column_mapping": DATASET_COLUMN_MAPPING,
        "model_config": model_config,
    }


def format_ragas_setup_error(exc: Exception) -> str:
    if (
        isinstance(exc, ModuleNotFoundError)
        and exc.name == "langchain_community.chat_models.vertexai"
    ):
        return (
            "ModuleNotFoundError: langchain_community.chat_models.vertexai. "
            "A versão instalada do RAGAS importa esse módulo legado de VertexAI "
            "mesmo quando a avaliação usa OpenAI. Use um ambiente de avaliação "
            "com versões compatíveis, por exemplo `pip install -r requirements-eval.txt`."
        )
    return f"{type(exc).__name__}: {exc}"


def write_json(
    rows: list[dict[str, Any]],
    output_path: Path,
    input_path: Path,
    metric_names: list[str],
    setup_error: str | None,
    environment: dict[str, Any],
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    scores = requested_score_columns(rows, metric_names)
    payload = {
        "input_jsonl": str(input_path),
        "metricas_solicitadas": metric_names,
        "ragas_environment": environment,
        "total_linhas": len(rows),
        "linhas_avaliadas": sum(
            1
            for row in rows
            if not row.get("ragas_skipped_reason") and not row.get("ragas_error")
        ),
        "linhas_puladas": sum(
            1 for row in rows if row.get("ragas_skipped_reason") or row.get("ragas_error")
        ),
        "linhas_fora_da_media_principal": sum(
            1
            for row in rows
            if row.get("ragas_evaluation_scope") == "behavioral_ambiguous_or_out_of_scope"
        ),
        "setup_error": setup_error,
        "aggregate_scores": aggregate_scores(rows, scores),
        "behavioral_evaluation": behavioral_evaluation_summary(rows),
        "results": rows,
    }
    output_path.write_text(
        json.dumps(normalize_json_value(payload), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_summary(
    rows: list[dict[str, Any]],
    output_path: Path,
    input_path: Path,
    metric_names: list[str],
    setup_error: str | None,
    environment: dict[str, Any],
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    scores = requested_score_columns(rows, metric_names)
    payload = {
        "input_jsonl": str(input_path),
        "total_items": len(rows),
        "items_evaluated": sum(
            1
            for row in rows
            if not row.get("ragas_skipped_reason") and not row.get("ragas_error")
        ),
        "items_skipped": sum(
            1 for row in rows if row.get("ragas_skipped_reason") or row.get("ragas_error")
        ),
        "items_excluded_from_primary_metrics": sum(
            1
            for row in rows
            if row.get("ragas_evaluation_scope") == "behavioral_ambiguous_or_out_of_scope"
        ),
        "skipped_items": [
            {
                "id": row.get("id"),
                "categoria": row.get("categoria"),
                "reason": row.get("ragas_skipped_reason") or row.get("ragas_error"),
            }
            for row in rows
            if row.get("ragas_skipped_reason") or row.get("ragas_error")
        ],
        "overall_metrics": aggregate_scores(rows, scores),
        "metrics_by_category": metrics_by_category(rows, scores),
        "behavioral_evaluation": behavioral_evaluation_summary(rows),
        "requested_metrics": metric_names,
        "setup_error": setup_error,
        "ragas_environment": environment,
    }
    output_path.write_text(
        json.dumps(normalize_json_value(payload), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_csv(rows: list[dict[str, Any]], output_path: Path, metric_names: list[str]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    scores = requested_score_columns(rows, metric_names)
    fieldnames = [*CSV_BASE_COLUMNS, "ragas_error", "ragas_metric_warning", *scores]
    with output_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    **{column: row.get(column) for column in CSV_BASE_COLUMNS},
                    "context_count": len(row.get("contexts") or []),
                    "source_count": len(row.get("retrieved_sources") or []),
                    "ragas_error": row.get("ragas_error"),
                    "ragas_metric_warning": row.get("ragas_metric_warning"),
                    **{score: row.get(score) for score in scores},
                }
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Executa RAGAS sobre o JSONL gerado pela avaliação do chatbot."
    )
    parser.add_argument("--input-jsonl", type=Path, default=Path("reports/evaluation/rag_eval_run.jsonl"))
    parser.add_argument("--output-csv", type=Path, default=Path("reports/evaluation/ragas_results.csv"))
    parser.add_argument("--output-json", type=Path, default=Path("reports/evaluation/ragas_results.json"))
    parser.add_argument("--summary-json", type=Path, default=Path("reports/evaluation/ragas_summary.json"))
    parser.add_argument(
        "--metrics",
        nargs="+",
        default=DEFAULT_METRICS,
        help="Lista de métricas RAGAS. Padrão: %(default)s",
    )
    parser.add_argument("--batch-size", type=int)
    parser.add_argument("--raise-exceptions", action="store_true")
    parser.add_argument("--no-progress", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        rows = load_jsonl(args.input_jsonl)
        validate_required_fields(rows)
        eval_rows, eval_indexes, skip_reasons = prepare_eval_rows(rows)
    except Exception as exc:
        print(f"Falha ao preparar JSONL: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    setup_error = None
    ragas_records: list[dict[str, Any]] = []
    environment: dict[str, Any] = {}
    if eval_rows:
        try:
            ragas_records = evaluate_rows(args, eval_rows)
            environment = ragas_environment_summary(ragas_records)
        except Exception as exc:  # pragma: no cover - depende da instalação/LLM
            setup_error = format_ragas_setup_error(exc)
            print(f"Falha ao executar RAGAS: {setup_error}", file=sys.stderr)
            environment = ragas_environment_summary([])
    else:
        setup_error = "Nenhuma linha avaliável para o RAGAS."
        print(setup_error, file=sys.stderr)
        environment = ragas_environment_summary([])

    merged = merge_results(rows, eval_indexes, skip_reasons, ragas_records, setup_error)
    mark_metric_warnings(merged, args.metrics)
    write_json(merged, args.output_json, args.input_jsonl, args.metrics, setup_error, environment)
    write_csv(merged, args.output_csv, args.metrics)
    write_summary(merged, args.summary_json, args.input_jsonl, args.metrics, setup_error, environment)

    print(f"Total de linhas: {len(rows)}")
    print(f"Linhas avaliáveis: {len(eval_rows)}")
    print(f"Linhas puladas: {len(rows) - len(eval_rows)}")
    if setup_error:
        print(f"Erro RAGAS: {setup_error}")
    print(f"Arquivo JSON salvo em: {args.output_json}")
    print(f"Arquivo CSV salvo em: {args.output_csv}")
    print(f"Resumo JSON salvo em: {args.summary_json}")
    return 0 if setup_error is None else 1


if __name__ == "__main__":
    raise SystemExit(main())
