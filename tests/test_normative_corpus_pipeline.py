import hashlib
import json
from pathlib import Path


EXPECTED_DOCUMENT_IDS = {
    "codigo-etica-ministro-alianca",
    "confissao-fe-congregacional-alianca",
    "constituicao-alianca-2022",
    "resolucao-alianca-01-2020",
    "regimento-interno-alianca-2022",
}
EXPECTED_ARTICLE_COUNTS = {
    "codigo-etica-ministro-alianca": 24,
    "confissao-fe-congregacional-alianca": 0,
    "constituicao-alianca-2022": 93,
    "resolucao-alianca-01-2020": 4,
    "regimento-interno-alianca-2022": 151,
}
DOCUMENT_CHUNK_FILES = {
    document_id: Path(f"corpus/processed/chunks/normative/{document_id}.chunks.jsonl")
    for document_id in EXPECTED_DOCUMENT_IDS
}
ALL_CHUNKS_PATH = Path("corpus/processed/chunks/normative/all_chunks.jsonl")
MAX_CHUNK_CHARS = 3200
REQUIRED_FIELDS = {
    "chunk_id",
    "doc_id",
    "document_id",
    "document_title",
    "denomination",
    "tradition",
    "document_type",
    "source_category",
    "resolution_number",
    "resolution_date",
    "page_start",
    "page_end",
    "text",
    "normalized_text",
    "section_title",
    "subsection_title",
    "chapter_number",
    "chapter_title",
    "section_number",
    "article_number",
    "paragraph_number",
    "inciso",
    "alinea",
    "full_reference",
    "document_structure_type",
    "biblical_references",
    "paragraph_label",
    "paragraph_number_roman",
    "footnote_markers",
    "topic",
    "subtopic",
}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            assert line.strip(), f"blank line at {path}:{line_number}"
            rows.append(json.loads(line))
    return rows


def test_normative_manifest_configs_and_scripts_exist():
    assert Path("corpus/raw/normative_manifest.json").exists()
    assert Path("config/normative_taxonomy.json").exists()
    assert Path("config/normative_topic_map.json").exists()
    assert Path("scripts/pipeline/extract_normative_corpus.py").exists()
    assert Path("scripts/pipeline/normalize_normative_corpus.py").exists()
    assert Path("scripts/pipeline/chunk_normative_corpus.py").exists()
    assert Path("scripts/pipeline/audit_normative_corpus.py").exists()


def test_normative_artifact_files_exist():
    for document_id in EXPECTED_DOCUMENT_IDS:
        assert Path(f"corpus/processed/extracted/normative/{document_id}.extracted.json").exists()
        assert Path(f"corpus/processed/normalized/normative/{document_id}.normalized.json").exists()
        assert DOCUMENT_CHUNK_FILES[document_id].exists()
    assert ALL_CHUNKS_PATH.exists()
    assert Path("corpus/reports/normative/normative-audit-report.json").exists()


def test_normative_chunks_have_required_metadata_and_hashes():
    for path in [*DOCUMENT_CHUNK_FILES.values(), ALL_CHUNKS_PATH]:
        chunks = read_jsonl(path)
        assert chunks
        for chunk in chunks:
            assert REQUIRED_FIELDS.issubset(chunk)
            assert chunk["schema_version"] == "normative-structural-chunk-v1"
            assert chunk["corpus_id"] == "congregational_normative"
            assert chunk["retrieval_namespace"] == "congregational_normative"
            assert chunk["doc_id"] == chunk["document_id"]
            assert chunk["document_id"] in EXPECTED_DOCUMENT_IDS
            assert chunk["source_path"].startswith("corpus/raw/normative/")
            assert chunk["normalized_source"].startswith("corpus/processed/normalized/normative/")
            assert chunk["text"].strip()
            assert chunk["normalized_text"].strip()
            assert chunk["full_reference"].strip()
            assert chunk["topic"].strip()
            assert chunk["subtopic"].strip()
            assert len(chunk["text"]) <= MAX_CHUNK_CHARS
            assert chunk["text_hash"] == hashlib.sha256(chunk["text"].encode("utf-8")).hexdigest()


def test_normative_consolidated_file_matches_document_files():
    per_document = {
        document_id: read_jsonl(path)
        for document_id, path in DOCUMENT_CHUNK_FILES.items()
    }
    all_chunks = read_jsonl(ALL_CHUNKS_PATH)

    assert {chunk["document_id"] for chunk in all_chunks} == EXPECTED_DOCUMENT_IDS
    assert len(all_chunks) == sum(len(chunks) for chunks in per_document.values())
    assert len({chunk["chunk_id"] for chunk in all_chunks}) == len(all_chunks)
    assert {
        document_id: sum(1 for chunk in all_chunks if chunk["document_id"] == document_id)
        for document_id in EXPECTED_DOCUMENT_IDS
    } == {document_id: len(chunks) for document_id, chunks in per_document.items()}


def test_normative_preambles_articles_and_biblical_references_are_preserved():
    ethics_chunks = read_jsonl(DOCUMENT_CHUNK_FILES["codigo-etica-ministro-alianca"])
    confession_chunks = read_jsonl(DOCUMENT_CHUNK_FILES["confissao-fe-congregacional-alianca"])
    constitution_chunks = read_jsonl(DOCUMENT_CHUNK_FILES["constituicao-alianca-2022"])
    resolution_chunks = read_jsonl(DOCUMENT_CHUNK_FILES["resolucao-alianca-01-2020"])
    regiment_chunks = read_jsonl(DOCUMENT_CHUNK_FILES["regimento-interno-alianca-2022"])

    assert any(chunk["document_structure_type"] == "preamble" for chunk in ethics_chunks)
    assert any(chunk["document_structure_type"] == "preamble" for chunk in constitution_chunks)
    assert any(chunk["document_structure_type"] == "ethics_article" for chunk in ethics_chunks)
    assert any(chunk["document_structure_type"] == "confession_paragraph" for chunk in confession_chunks)
    assert any(chunk["document_structure_type"] == "canon_books_table" for chunk in confession_chunks)
    assert any(chunk["document_structure_type"] == "numbered_doctrinal_point" for chunk in confession_chunks)
    assert any(chunk["document_structure_type"] == "resolution_ementa" for chunk in resolution_chunks)
    assert sum(1 for chunk in resolution_chunks if chunk["document_structure_type"] == "resolution_considerando") == 3
    assert any(chunk["chapter_number"] == "II" and chunk["article_number"] == "5" for chunk in constitution_chunks)
    assert any(chunk["chapter_number"] == "I" and chunk["section_number"] == "I" for chunk in regiment_chunks)
    assert any(chunk["biblical_references"] for chunk in ethics_chunks)
    assert any(chunk["biblical_references"] for chunk in confession_chunks)


def test_confession_reference_tables_and_numbered_points_are_preserved():
    chunks = read_jsonl(DOCUMENT_CHUNK_FILES["confissao-fe-congregacional-alianca"])
    confession_paragraphs = [chunk for chunk in chunks if chunk["document_structure_type"] == "confession_paragraph"]
    numbered_points = [chunk for chunk in chunks if chunk["document_structure_type"] == "numbered_doctrinal_point"]
    canon_tables = [chunk for chunk in chunks if chunk["document_structure_type"] == "canon_books_table"]

    assert len({chunk["chapter_number"] for chunk in confession_paragraphs if chunk["chapter_number"]}) == 34
    assert len(confession_paragraphs) == 188
    assert len(canon_tables) == 1
    assert sorted({int(chunk["numbered_point"]) for chunk in numbered_points}) == list(range(1, 28))
    assert any("ANTIGO TESTAMENTO" in chunk["text"] for chunk in canon_tables)
    assert any("NOVO TESTAMENTO" in chunk["text"] for chunk in canon_tables)

    linked_paragraphs = [chunk for chunk in confession_paragraphs if chunk["footnote_markers"]]
    assert linked_paragraphs
    for chunk in linked_paragraphs:
        assert set(chunk["footnote_markers"]) == set((chunk.get("biblical_reference_map") or {}).keys())
        assert chunk.get("biblical_reference_links")


def test_resolution_structure_is_preserved():
    chunks = read_jsonl(DOCUMENT_CHUNK_FILES["resolucao-alianca-01-2020"])
    chunk_types = {chunk["document_structure_type"] for chunk in chunks}

    assert {
        "resolution_heading",
        "resolution_ementa",
        "resolution_intro",
        "resolution_considerando",
        "resolution_article",
        "signature",
    }.issubset(chunk_types)
    assert [chunk["article_number"] for chunk in chunks if chunk["article_number"]] == ["1", "2", "3", "4"]
    assert all(chunk["resolution_number"] == "01/2020" for chunk in chunks)
    assert all(chunk["resolution_date"] == "23 de novembro de 2020" for chunk in chunks)


def test_normative_audit_reports_no_lost_or_duplicate_articles():
    report = read_json(Path("corpus/reports/normative/normative-audit-report.json"))
    assert report["status"] in {"PASS", "PARTIAL"}
    assert report["max_chunk_chars"] == MAX_CHUNK_CHARS

    for document in report["documents"]:
        assert document["articles_detected"] == EXPECTED_ARTICLE_COUNTS[document["document_id"]]
        assert not document["missing_article_chunks"]
        assert not document["duplicate_article_numbers_detected"]
        assert not document["chunks_above_expected_limit"]
        assert not document["empty_chunks"]
        assert not document["chunks_missing_doc_id"]
        assert not document["chunks_missing_full_reference"]
        assert not document["invalid_topic_assignments"]
        assert not document["chunk_validation_issues"]
        assert not document["document_specific_issues"]

    confession = next(
        document for document in report["documents"] if document["document_id"] == "confissao-fe-congregacional-alianca"
    )
    assert confession["confession_paragraphs_detected"] == 188
    assert confession["canon_books_table_count"] == 1
    assert confession["numbered_doctrinal_points_detected"] == [str(number) for number in range(1, 28)]
    assert not confession["missing_numbered_doctrinal_points"]
    assert not confession["confession_reference_issues"]

    resolution = next(document for document in report["documents"] if document["document_id"] == "resolucao-alianca-01-2020")
    assert resolution["resolution_considerandos_detected"] == 3
