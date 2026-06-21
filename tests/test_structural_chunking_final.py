import hashlib
import json
from pathlib import Path


DOCUMENT_CHUNK_FILES = {
    "confissao-fe-westminster": Path("corpus/processed/chunks/reformed/confissao-fe-westminster.chunks.jsonl"),
    "canones-de-dort": Path("corpus/processed/chunks/reformed/canones-de-dort.chunks.jsonl"),
    "catecismo-heidelberg": Path("corpus/processed/chunks/reformed/catecismo-heidelberg.chunks.jsonl"),
    "confissao-batista-londres-1689": Path(
        "corpus/processed/chunks/reformed/confissao-batista-londres-1689.chunks.jsonl"
    ),
}
ALL_CHUNKS_PATH = Path("corpus/processed/chunks/reformed/all_chunks.jsonl")
EXPECTED_DOCUMENT_IDS = set(DOCUMENT_CHUNK_FILES)
REQUIRED_FIELDS = {
    "chunk_id",
    "schema_version",
    "corpus_id",
    "retrieval_namespace",
    "document_id",
    "document",
    "document_type",
    "tradition_family",
    "tradition_branch",
    "language",
    "chunk_type",
    "content_role",
    "is_doctrinal",
    "section_title",
    "section_reference",
    "chapter_title",
    "chapter_reference",
    "page_start",
    "page_end",
    "text",
    "embedding_text",
    "source_path",
    "normalized_source",
    "text_hash",
    "warnings",
}


def read_jsonl(path: Path) -> list[dict]:
    chunks = []
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            assert line.strip(), f"blank line at {path}:{line_number}"
            chunks.append(json.loads(line))
    return chunks


def test_chunking_script_exists():
    assert Path("scripts/pipeline/chunk_reformed_corpus.py").exists()


def test_final_chunk_files_exist():
    for path in DOCUMENT_CHUNK_FILES.values():
        assert path.exists()
    assert ALL_CHUNKS_PATH.exists()


def test_jsonl_files_are_valid_and_have_required_fields():
    for path in [*DOCUMENT_CHUNK_FILES.values(), ALL_CHUNKS_PATH]:
        chunks = read_jsonl(path)
        assert chunks
        for chunk in chunks:
            assert REQUIRED_FIELDS.issubset(chunk)
            assert chunk["schema_version"] == "reformed-structural-chunk-v1"
            assert chunk["corpus_id"] == "reformed"
            assert chunk["retrieval_namespace"] == "reformed_confessional"
            assert chunk["document_id"] in EXPECTED_DOCUMENT_IDS
            assert chunk["source_path"].startswith("corpus/raw/reformed/")
            assert "evaluation_sets" not in chunk["source_path"]
            assert chunk["normalized_source"].startswith("corpus/processed/normalized/reformed/")
            assert chunk["text"].strip()
            assert chunk["embedding_text"].strip()
            assert chunk["text_hash"] == hashlib.sha256(chunk["text"].encode("utf-8")).hexdigest()
            assert isinstance(chunk["warnings"], list)


def test_no_duplicate_chunk_ids_in_document_files_or_consolidated_file():
    for path in DOCUMENT_CHUNK_FILES.values():
        chunks = read_jsonl(path)
        chunk_ids = [chunk["chunk_id"] for chunk in chunks]
        assert len(chunk_ids) == len(set(chunk_ids))

    all_chunks = read_jsonl(ALL_CHUNKS_PATH)
    all_chunk_ids = [chunk["chunk_id"] for chunk in all_chunks]
    assert len(all_chunk_ids) == len(set(all_chunk_ids))


def test_all_expected_documents_are_present():
    all_chunks = read_jsonl(ALL_CHUNKS_PATH)
    assert {chunk["document_id"] for chunk in all_chunks} == EXPECTED_DOCUMENT_IDS


def test_consolidated_count_matches_document_sum():
    per_document_chunks = {
        document_id: read_jsonl(path)
        for document_id, path in DOCUMENT_CHUNK_FILES.items()
    }
    all_chunks = read_jsonl(ALL_CHUNKS_PATH)

    assert len(all_chunks) == sum(len(chunks) for chunks in per_document_chunks.values())
    assert {
        document_id: sum(1 for chunk in all_chunks if chunk["document_id"] == document_id)
        for document_id in EXPECTED_DOCUMENT_IDS
    } == {document_id: len(chunks) for document_id, chunks in per_document_chunks.items()}


def test_expected_chunk_types_are_present_by_document():
    chunks_by_document = {
        document_id: read_jsonl(path)
        for document_id, path in DOCUMENT_CHUNK_FILES.items()
    }

    assert "confessional_section" in {chunk["chunk_type"] for chunk in chunks_by_document["confissao-fe-westminster"]}
    assert {"doctrinal_article", "error_refutation"}.issubset(
        {chunk["chunk_type"] for chunk in chunks_by_document["canones-de-dort"]}
    )
    assert "catechism_question_answer" in {
        chunk["chunk_type"] for chunk in chunks_by_document["catecismo-heidelberg"]
    }
    assert "confessional_paragraph" in {
        chunk["chunk_type"] for chunk in chunks_by_document["confissao-batista-londres-1689"]
    }


def test_westminster_chunks_preserve_sections_and_special_layout():
    chunks = read_jsonl(DOCUMENT_CHUNK_FILES["confissao-fe-westminster"])
    section_chunks = [chunk for chunk in chunks if chunk["chunk_type"] == "confessional_section"]
    layout_chunks = [chunk for chunk in chunks if chunk["chunk_type"] == "special_layout"]

    assert len(section_chunks) == 172
    assert len(layout_chunks) == 1
    assert all(chunk["is_doctrinal"] for chunk in section_chunks)
    assert all(not chunk["is_doctrinal"] for chunk in layout_chunks)
    assert any(chunk["section_reference"] == "Seção I" for chunk in section_chunks)
    assert any("DA ESCRITURA SAGRADA" in chunk["text"] for chunk in section_chunks)
    assert "ANTIGO TESTAMENTO" in layout_chunks[0]["text"]
    assert "NOVO TESTAMENTO" in layout_chunks[0]["text"]


def test_london_chunks_preserve_paragraphs_references_and_special_layouts():
    chunks = read_jsonl(DOCUMENT_CHUNK_FILES["confissao-batista-londres-1689"])
    paragraph_chunks = [chunk for chunk in chunks if chunk["chunk_type"] == "confessional_paragraph"]
    layout_chunks = [chunk for chunk in chunks if chunk["chunk_type"] == "special_layout"]

    assert len(paragraph_chunks) == 157
    assert len(layout_chunks) == 2
    assert all(chunk["is_doctrinal"] for chunk in paragraph_chunks)
    assert all(not chunk["is_doctrinal"] for chunk in layout_chunks)

    chapter_two_first = next(
        chunk
        for chunk in paragraph_chunks
        if chunk["chapter_number"] == "2" and chunk["paragraph_number"] == "1"
    )
    assert chapter_two_first["reference_associations"]["1"] == ["1Co.8.4,6", "Dt.6.4"]
    assert "Referências bíblicas:" in chapter_two_first["text"]
    assert "O VELHO TESTAMENTO" in layout_chunks[0]["text"]
    assert "O NOVO TESTAMENTO" in layout_chunks[1]["text"]


def test_non_doctrinal_chunks_are_contextual_or_structural():
    all_chunks = read_jsonl(ALL_CHUNKS_PATH)
    for chunk in all_chunks:
        if not chunk["is_doctrinal"]:
            assert chunk["chunk_type"] in {"introductory_context", "special_layout"}
            assert chunk["content_role"] in {"contextual", "structural"}


def test_spec_003b_reports_exist_and_record_known_warnings():
    report_path = Path("corpus/reports/chunking/SPEC-003B-chunking-report.json")
    spec_report_path = Path("reports/specs/SPEC-003B-structural-chunking-final.md")

    assert report_path.exists()
    assert spec_report_path.exists()

    report = json.loads(report_path.read_text(encoding="utf-8"))
    westminster = next(item for item in report["summaries"] if item["document_id"] == "confissao-fe-westminster")
    heidelberg = next(item for item in report["summaries"] if item["document_id"] == "catecismo-heidelberg")

    assert "westminster_page_1_without_extractable_text_in_spec_002" in westminster["document_warnings"]
    assert heidelberg["warning_chunks"]
    assert report["consolidation"]["chunk_count"] == len(read_jsonl(ALL_CHUNKS_PATH))
