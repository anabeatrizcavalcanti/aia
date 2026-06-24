import json
from pathlib import Path


EXPECTED_DOCUMENT_IDS = {
    "confissao-fe-westminster",
    "canones-de-dort",
    "catecismo-heidelberg",
    "confissao-batista-londres-1689",
}

STRUCTURAL_MARKERS = {
    "confissao-fe-westminster": ["CAPÍTULO", "DA ESCRITURA SAGRADA", "I."],
    "canones-de-dort": ["Capítulo da Doutrina", "Artigo", "Rejeição de Erros", "Refutação"],
    "catecismo-heidelberg": ["Dia do Senhor", "P.", "R."],
    "confissao-batista-londres-1689": ["CAPÍTULO", "AS SAGRADAS ESCRITURAS", "1."],
}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def normalized_contains(text: str, marker: str) -> bool:
    return marker.casefold() in text.casefold()


def test_extraction_and_normalization_scripts_exist():
    assert Path("scripts/pipeline/extract_reformed_corpus.py").exists()
    assert Path("scripts/pipeline/normalize_reformed_corpus.py").exists()


def test_output_directories_exist():
    assert Path("corpus/processed/extracted/reformed").exists()
    assert Path("corpus/processed/normalized/reformed").exists()
    assert Path("corpus/reports/extraction").exists()
    assert Path("corpus/reports/normalization").exists()


def test_extracted_and_normalized_files_exist_for_expected_documents():
    for document_id in EXPECTED_DOCUMENT_IDS:
        assert Path(f"corpus/processed/extracted/reformed/{document_id}.extracted.json").exists()
        assert Path(f"corpus/processed/extracted/reformed/{document_id}.extracted.txt").exists()
        assert Path(f"corpus/processed/normalized/reformed/{document_id}.normalized.json").exists()
        assert Path(f"corpus/processed/normalized/reformed/{document_id}.normalized.txt").exists()


def test_extraction_and_normalization_reports_exist():
    assert Path("corpus/reports/extraction/extraction_report.json").exists()
    assert Path("corpus/reports/extraction/extraction_report.md").exists()
    assert Path("corpus/reports/normalization/normalization_report.json").exists()
    assert Path("corpus/reports/normalization/normalization_report.md").exists()
    assert Path("reports/specs/extraction-normalization.md").exists()


def test_extracted_jsons_are_valid_and_preserve_metadata():
    document_ids = set()

    for path in Path("corpus/processed/extracted/reformed").glob("*.extracted.json"):
        data = load_json(path)
        document_ids.add(data["document_id"])

        assert data["corpus_id"] == "reformed"
        assert data["raw_path"].startswith("corpus/raw/reformed/")
        assert "evaluation_sets" not in data["raw_path"]
        assert data["pages_count"] == len(data["pages"])
        assert data["pages_count"] > 0
        assert any(page["text"].strip() for page in data["pages"])
        assert all("page_number" in page for page in data["pages"])
        assert all(isinstance(page["is_empty"], bool) for page in data["pages"])

    assert document_ids == EXPECTED_DOCUMENT_IDS


def test_normalized_jsons_are_valid_and_match_extracted_pages():
    document_ids = set()

    for path in Path("corpus/processed/normalized/reformed").glob("*.normalized.json"):
        data = load_json(path)
        document_ids.add(data["document_id"])
        extracted = load_json(Path(data["input_extraction_file"]))

        assert data["corpus_id"] == "reformed"
        assert data["raw_path"].startswith("corpus/raw/reformed/")
        assert "evaluation_sets" not in data["raw_path"]
        assert data["document_id"] == extracted["document_id"]
        assert data["pages_count"] == extracted["pages_count"]
        assert data["pages_count"] == len(data["pages"])
        assert all("page_number" in page for page in data["pages"])
        assert all("normalization_actions" in page for page in data["pages"])
        assert all("page_zone" in page for page in data["pages"])

    assert document_ids == EXPECTED_DOCUMENT_IDS


def test_reports_contain_expected_document_ids():
    extraction_report = load_json(Path("corpus/reports/extraction/extraction_report.json"))
    normalization_report = load_json(Path("corpus/reports/normalization/normalization_report.json"))

    extracted_ids = {document["document_id"] for document in extraction_report["documents"]}
    normalized_ids = {document["document_id"] for document in normalization_report["documents"]}

    assert extracted_ids == EXPECTED_DOCUMENT_IDS
    assert normalized_ids == EXPECTED_DOCUMENT_IDS
    assert extraction_report["status"] in {"PASS", "PARTIAL"}
    assert normalization_report["status"] in {"PASS", "PARTIAL"}


def test_normalized_text_preserves_minimum_structural_markers():
    for document_id, markers in STRUCTURAL_MARKERS.items():
        data = load_json(Path(f"corpus/processed/normalized/reformed/{document_id}.normalized.json"))
        full_text = "\n".join(page["text"] for page in data["pages"])

        for marker in markers:
            assert normalized_contains(full_text, marker), f"{marker} ausente em {document_id}"
            assert data["marker_validation"][marker] is True


def test_no_normalized_source_points_outside_reformed_raw_corpus():
    for path in Path("corpus/processed/normalized/reformed").glob("*.normalized.json"):
        data = load_json(path)
        assert data["raw_path"].startswith("corpus/raw/reformed/")
        assert ".." not in Path(data["raw_path"]).parts
