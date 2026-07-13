import json
from pathlib import Path


FILTERED_CHUNKS = Path("corpus/processed/chunks/alliance/all_chunks_for_embeddings.jsonl")
EMBEDDINGS_FILE = Path("corpus/processed/embeddings/alliance/openai_embeddings.jsonl")
EMBEDDING_REPORT_JSON = Path("corpus/reports/embeddings/openai-embedding-report.json")


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            assert line.strip() or path == EMBEDDINGS_FILE, f"blank line at {path}:{line_number}"
            if line.strip():
                rows.append(json.loads(line))
    return rows


def test_embedding_script_exists():
    assert Path("scripts/pipeline/generate_openai_embeddings.py").exists()


def test_filtered_chunks_file_exists_and_is_valid_jsonl():
    assert FILTERED_CHUNKS.exists()
    rows = read_jsonl(FILTERED_CHUNKS)

    assert rows
    for row in rows:
        assert "chunk_id" in row
        assert "embedding_eligible" in row
        assert "embedding_exclusion_reason" in row


def test_filtered_chunks_have_eligible_rows_with_embedding_text():
    rows = read_jsonl(FILTERED_CHUNKS)
    eligible_rows = [row for row in rows if row["embedding_eligible"]]

    assert eligible_rows
    assert all(row["embedding_text"].strip() for row in eligible_rows)


def test_excluded_chunks_record_reason():
    rows = read_jsonl(FILTERED_CHUNKS)
    excluded_rows = [row for row in rows if not row["embedding_eligible"]]

    assert excluded_rows
    assert all(row["embedding_exclusion_reason"] for row in excluded_rows)


def test_openai_embeddings_file_if_present_is_valid_jsonl():
    if not EMBEDDINGS_FILE.exists():
        return

    rows = read_jsonl(EMBEDDINGS_FILE)
    chunk_ids = [row["chunk_id"] for row in rows]
    assert len(chunk_ids) == len(set(chunk_ids))

    for row in rows:
        assert "embedding" in row
        assert "embedding_model" in row
        assert "embedding_dimensions" in row
        assert "chunk_id" in row
        assert "text_hash" in row
        assert isinstance(row["embedding"], list)
        assert row["embedding_dimensions"] == len(row["embedding"])


def test_embedding_manifest_exists():
    manifest_path = Path("corpus/processed/embeddings/alliance/embedding_manifest.json")
    assert manifest_path.exists()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["embedding_provider"] == "openai"
    assert manifest["embedding_model"] == "text-embedding-3-large"
    assert manifest["embedding_dimensions"] == 3072
    assert manifest["filtered_chunks_path"] == FILTERED_CHUNKS.as_posix()


def test_alliance_filtered_chunks_include_normative_documents_without_duplicates():
    rows = read_jsonl(FILTERED_CHUNKS)
    chunk_ids = [row["chunk_id"] for row in rows]
    document_ids = {row["document_id"] for row in rows}

    assert len(chunk_ids) == len(set(chunk_ids))
    assert "confissao-fe-congregacional-alianca" in document_ids
    assert "constituicao-alianca-2022" in document_ids
    assert "regimento-interno-alianca-2022" in document_ids
    assert "codigo-etica-ministro-alianca" in document_ids
    assert "resolucao-alianca-01-2020" in document_ids


def test_embedding_reports_exist():
    assert EMBEDDING_REPORT_JSON.exists()
    assert Path("corpus/reports/embeddings/openai-embedding-report.md").exists()
    assert Path("reports/specs/openai-embeddings.md").exists()

    report = json.loads(EMBEDDING_REPORT_JSON.read_text(encoding="utf-8"))
    assert report["total_chunks"] >= report["eligible_chunks"]
    assert report["excluded_chunks"] >= 0
