import importlib.util
import json
from pathlib import Path


EMBEDDINGS_PATH = Path("corpus/processed/embeddings/alliance/openai_embeddings.jsonl")
PERSIST_DIR = Path("corpus/indexes/chroma/alliance")
COLLECTION_NAME = "solabot_alliance_v1"


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            assert line.strip(), f"blank line at {path}:{line_number}"
            rows.append(json.loads(line))
    return rows


def test_chroma_index_script_exists():
    assert Path("scripts/pipeline/build_reformed_chroma_index.py").exists()


def test_embeddings_file_exists_and_is_valid_jsonl():
    assert EMBEDDINGS_PATH.exists()
    rows = read_jsonl(EMBEDDINGS_PATH)

    assert rows
    for row in rows:
        assert row["chunk_id"]
        assert row["document_id"]
        assert row["embedding"]
        assert row["embedding_dimensions"] == len(row["embedding"])


def test_persist_directory_exists():
    assert PERSIST_DIR.exists()
    assert any(PERSIST_DIR.iterdir())


def test_vector_index_reports_exist():
    assert Path("corpus/reports/vector_index/chroma-vector-index-report.json").exists()
    assert Path("corpus/reports/vector_index/chroma-vector-index-report.md").exists()
    assert Path("reports/specs/chroma-vector-index.md").exists()


def test_chroma_collection_has_documents_if_chromadb_available():
    if importlib.util.find_spec("chromadb") is None:
        report = json.loads(
            Path("corpus/reports/vector_index/chroma-vector-index-report.json").read_text(
                encoding="utf-8"
            )
        )
        assert report["status"] in {"PARTIAL", "FAIL"}
        assert report["chromadb_available"] is False
        return

    import chromadb

    client = chromadb.PersistentClient(path=str(PERSIST_DIR))
    collection = client.get_collection(COLLECTION_NAME)

    assert collection.count() > 0


def test_vector_report_records_successful_validation_query():
    report = json.loads(
        Path("corpus/reports/vector_index/chroma-vector-index-report.json").read_text(
            encoding="utf-8"
        )
    )

    assert report["collection_name"] == COLLECTION_NAME
    assert report["chunks_indexed"] > 0
    assert report["collection_count"] == report["chunks_indexed"]
    assert report["validation_queries"]
    assert any(item["results_count"] > 0 for item in report["validation_queries"])


def test_vector_report_records_alliance_normative_validation_queries():
    report = json.loads(
        Path("corpus/reports/vector_index/chroma-vector-index-report.json").read_text(
            encoding="utf-8"
        )
    )
    queries = {item["query"] for item in report["validation_queries"]}

    assert "O que a Confissão de Fé Congregacional ensina sobre justificação?" in queries
    assert "Quais os critérios para emancipação de campos missionários?" in queries
