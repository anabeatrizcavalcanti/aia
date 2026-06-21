import json
from pathlib import Path


EXPECTED_DOCUMENT_IDS = {"canones-de-dort", "catecismo-heidelberg"}
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
        for line in file:
            assert line.strip()
            chunks.append(json.loads(line))
    return chunks


def test_chunking_script_exists():
    assert Path("scripts/pipeline/chunk_reformed_corpus.py").exists()


def test_spec_003a_chunk_files_exist():
    assert Path("corpus/processed/chunks/reformed/canones-de-dort.chunks.jsonl").exists()
    assert Path("corpus/processed/chunks/reformed/catecismo-heidelberg.chunks.jsonl").exists()


def test_spec_003a_does_not_create_out_of_scope_chunk_files():
    report_text = Path("reports/specs/SPEC-003A-structural-chunking-base.md").read_text(encoding="utf-8")

    assert "Westminster ainda não foi chunkado" in report_text
    assert "Londres 1689 ainda não foi chunkado" in report_text
    assert "`all_chunks.jsonl` ainda não foi criado" in report_text


def test_jsonl_files_are_valid_and_have_no_duplicate_chunk_ids():
    all_chunk_ids = set()
    document_ids = set()

    for path in [
        Path("corpus/processed/chunks/reformed/canones-de-dort.chunks.jsonl"),
        Path("corpus/processed/chunks/reformed/catecismo-heidelberg.chunks.jsonl"),
    ]:
        chunks = read_jsonl(path)
        assert chunks
        file_chunk_ids = [chunk["chunk_id"] for chunk in chunks]
        assert len(file_chunk_ids) == len(set(file_chunk_ids))

        for chunk in chunks:
            assert chunk["chunk_id"] not in all_chunk_ids
            all_chunk_ids.add(chunk["chunk_id"])
            document_ids.add(chunk["document_id"])

    assert document_ids == EXPECTED_DOCUMENT_IDS


def test_all_chunks_have_required_fields_and_valid_source_paths():
    for path in [
        Path("corpus/processed/chunks/reformed/canones-de-dort.chunks.jsonl"),
        Path("corpus/processed/chunks/reformed/catecismo-heidelberg.chunks.jsonl"),
    ]:
        for chunk in read_jsonl(path):
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
            assert chunk["text_hash"]
            assert isinstance(chunk["warnings"], list)


def test_expected_chunk_types_are_present():
    canons = read_jsonl(Path("corpus/processed/chunks/reformed/canones-de-dort.chunks.jsonl"))
    catechism = read_jsonl(Path("corpus/processed/chunks/reformed/catecismo-heidelberg.chunks.jsonl"))

    canons_types = {chunk["chunk_type"] for chunk in canons}
    catechism_types = {chunk["chunk_type"] for chunk in catechism}

    assert "doctrinal_article" in canons_types
    assert "error_refutation" in canons_types
    assert "conclusion_paragraph" in canons_types
    assert "introductory_context" in canons_types
    assert catechism_types == {"introductory_context", "catechism_question_answer"}


def test_catechism_preserves_question_answer_units_and_reference_warnings():
    chunks = read_jsonl(Path("corpus/processed/chunks/reformed/catecismo-heidelberg.chunks.jsonl"))
    question_chunks = [chunk for chunk in chunks if chunk["chunk_type"] == "catechism_question_answer"]
    by_question = {chunk["question_number"]: chunk for chunk in question_chunks}

    assert len(chunks) == 130
    assert len(question_chunks) == 129
    assert "P.1." in by_question[1]["text"]
    assert "R." in by_question[1]["text"]
    assert by_question[101]["chunk_type"] == "catechism_question_answer"
    assert by_question[117]["lords_day"] == "Dia do Senhor 45"

    for question_number in (10, 20, 29, 60):
        assert by_question[question_number]["warnings"]
        assert by_question[question_number]["unresolved_answer_markers"]


def test_catechism_preserves_introductory_context_separately():
    chunks = read_jsonl(Path("corpus/processed/chunks/reformed/catecismo-heidelberg.chunks.jsonl"))
    structure = json.loads(
        Path("corpus/reports/structure_analysis/catecismo-heidelberg.structure.json").read_text(
            encoding="utf-8"
        )
    )
    intro_chunks = [chunk for chunk in chunks if chunk["chunk_type"] == "introductory_context"]

    assert len(intro_chunks) == 1
    intro = intro_chunks[0]
    assert intro["is_doctrinal"] is False
    assert intro["content_role"] == "contextual"
    assert intro["section_title"] == "Material introdutório"
    assert intro["page_start"] == 1
    assert "O Catecismo de Heidelberg, o segundo dos padrões doutrinários" in intro["text"]
    assert "Pedro Dathenus" in intro["text"]
    assert "P.1." not in intro["text"]
    assert "Dia do Senhor 1" not in intro["text"]
    assert intro["text"] == structure["introductory_contexts"][0]["text"]


def test_canons_preserves_articles_refutations_and_non_doctrinal_intro():
    chunks = read_jsonl(Path("corpus/processed/chunks/reformed/canones-de-dort.chunks.jsonl"))

    article_chunks = [chunk for chunk in chunks if chunk["chunk_type"] == "doctrinal_article"]
    refutation_chunks = [chunk for chunk in chunks if chunk["chunk_type"] == "error_refutation"]
    intro_chunks = [chunk for chunk in chunks if chunk["chunk_type"] == "introductory_context"]

    assert len(article_chunks) == 59
    assert len(refutation_chunks) == 34
    assert intro_chunks
    assert all(not chunk["is_doctrinal"] for chunk in intro_chunks)
    assert any(chunk["section_reference"] == "Artigo 1" for chunk in article_chunks)
    assert any("Refutação" in chunk["text"] for chunk in refutation_chunks)


def test_chunking_reports_exist():
    assert Path("corpus/reports/chunking/SPEC-003A-chunking-report.json").exists()
    assert Path("corpus/reports/chunking/SPEC-003A-chunking-report.md").exists()
    assert Path("reports/specs/SPEC-003A-structural-chunking-base.md").exists()
