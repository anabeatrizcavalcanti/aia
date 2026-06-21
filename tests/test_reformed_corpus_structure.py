import json
from pathlib import Path


EXPECTED_DOCUMENT_IDS = {
    "confissao-fe-westminster",
    "canones-de-dort",
    "catecismo-heidelberg",
    "confissao-batista-londres-1689",
}


def test_reformed_raw_directory_exists():
    assert Path("corpus/raw/reformed").exists()


def test_spec_001_scripts_exist():
    assert Path("scripts/corpus/validate_reformed_raw_corpus.py").exists()
    assert Path("scripts/corpus/analyze_reformed_pdf_structure.py").exists()
    assert Path("scripts/pipeline/extract_reformed_corpus.py").exists()
    assert Path("scripts/pipeline/normalize_reformed_corpus.py").exists()
    assert Path("scripts/pipeline/chunk_reformed_corpus.py").exists()


def test_structure_analysis_directory_exists():
    assert Path("corpus/reports/structure_analysis").exists()


def test_reformed_manifest_is_valid_json():
    manifest_path = Path("corpus/raw/reformed_manifest.json")
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["corpus_id"] == "reformed"
    assert isinstance(manifest["documents"], list)


def test_reformed_manifest_contains_expected_documents():
    manifest = json.loads(Path("corpus/raw/reformed_manifest.json").read_text(encoding="utf-8"))
    document_ids = {document["document_id"] for document in manifest["documents"]}
    assert document_ids == EXPECTED_DOCUMENT_IDS


def test_structure_jsons_do_not_include_human_review_fields():
    forbidden_fields = {"recommended_chunking_strategy", "risks"}

    for structure_path in Path("corpus/reports/structure_analysis").glob("*.structure.json"):
        structure = json.loads(structure_path.read_text(encoding="utf-8"))
        assert forbidden_fields.isdisjoint(structure)


def test_structure_markdown_reports_do_not_include_chat_recommendations():
    forbidden_phrases = [
        "## Recomendação inicial de chunking",
        "## Próximo passo recomendado",
        "Essa recomendação deve ser revisada manualmente",
        "Revisar os padrões detectados neste relatório",
        "Próximo passo recomendado",
    ]

    report_paths = list(Path("corpus/reports/structure_analysis").glob("*.structure.md"))
    report_paths.append(Path("corpus/reports/structure_analysis/reformed_raw_validation.md"))

    for report_path in report_paths:
        report_text = report_path.read_text(encoding="utf-8")
        for phrase in forbidden_phrases:
            assert phrase not in report_text


def test_catechism_reference_lines_do_not_include_section_headers():
    structure_path = Path("corpus/reports/structure_analysis/catecismo-heidelberg.structure.json")
    assert structure_path.exists()
    structure = json.loads(structure_path.read_text(encoding="utf-8"))

    for unit in structure["catechism_units"]:
        joined_reference_lines = " ".join(unit["reference_lines"])
        assert "Dia do Senhor" not in joined_reference_lines
        assert "O Catecismo de Heidelberg" not in joined_reference_lines
        assert "Parte " not in joined_reference_lines


def test_catechism_lords_day_context_moves_to_next_question():
    structure = json.loads(
        Path("corpus/reports/structure_analysis/catecismo-heidelberg.structure.json").read_text(
            encoding="utf-8"
        )
    )
    units = {unit["question_number"]: unit for unit in structure["catechism_units"]}

    assert units[15]["lords_day"] == "Dia do Senhor 5"
    assert units[15]["trailing_section_lines_excluded"] == ["Dia do Senhor 6"]
    assert units[16]["lords_day"] == "Dia do Senhor 6"


def test_catechism_part_context_is_structured():
    structure = json.loads(
        Path("corpus/reports/structure_analysis/catecismo-heidelberg.structure.json").read_text(
            encoding="utf-8"
        )
    )
    units = {unit["question_number"]: unit for unit in structure["catechism_units"]}

    assert units[1]["part"] is None
    assert units[2]["part"] is None
    assert units[3]["part_label"] == "Parte I"
    assert units[3]["part_title"] == "NOSSOS PECADOS E MISÉRIA"
    assert units[3]["part"] == "Parte I NOSSOS PECADOS E MISÉRIA"
    assert units[11]["part"] == "Parte I NOSSOS PECADOS E MISÉRIA"
    assert units[12]["part"] == "Parte II NOSSA SALVAÇÃO"


def test_catechism_top_level_parts_are_merged():
    structure = json.loads(
        Path("corpus/reports/structure_analysis/catecismo-heidelberg.structure.json").read_text(
            encoding="utf-8"
        )
    )

    assert structure["parts"] == [
        {"page": 2, "text": "Parte I NOSSOS PECADOS E MISÉRIA"},
        {"page": 3, "text": "Parte II NOSSA SALVAÇÃO"},
        {"page": 19, "text": "Parte III A NOSSA GRATIDÃO"},
    ]


def test_catechism_top_level_page_classification_is_consistent():
    structure = json.loads(
        Path("corpus/reports/structure_analysis/catecismo-heidelberg.structure.json").read_text(
            encoding="utf-8"
        )
    )

    assert structure["introductory_pages"] == [1]
    assert structure["special_layout_pages"] == []


def test_catechism_introductory_context_is_structured():
    structure = json.loads(
        Path("corpus/reports/structure_analysis/catecismo-heidelberg.structure.json").read_text(
            encoding="utf-8"
        )
    )
    contexts = structure["introductory_contexts"]

    assert len(contexts) == 1
    context = contexts[0]
    assert context["chunk_type"] == "introductory_context"
    assert context["content_role"] == "contextual"
    assert context["is_doctrinal"] is False
    assert context["page_start"] == 1
    assert context["page_end"] == 1
    assert "O Catecismo de Heidelberg, o segundo dos padrões doutrinários" in context["text"]
    assert "Pedro Dathenus" in context["text"]
    assert "P.1." not in context["text"]
    assert "Dia do Senhor 1" not in context["text"]


def test_catechism_omits_irrelevant_generic_analysis_fields():
    structure = json.loads(
        Path("corpus/reports/structure_analysis/catecismo-heidelberg.structure.json").read_text(
            encoding="utf-8"
        )
    )

    irrelevant_fields = {
        "titles",
        "chapters",
        "articles",
        "questions",
        "answers",
        "rejections",
        "lords_days",
        "possible_bible_references_count",
        "notes_count",
        "possible_notes_examples",
        "pages",
        "recommended_chunking_strategy",
        "risks",
    }

    assert irrelevant_fields.isdisjoint(structure)


def test_catechism_infers_truncated_lords_day_heading():
    structure = json.loads(
        Path("corpus/reports/structure_analysis/catecismo-heidelberg.structure.json").read_text(
            encoding="utf-8"
        )
    )
    units = {unit["question_number"]: unit for unit in structure["catechism_units"]}

    assert units[116]["section_title"] == "A Oração"
    assert units[116]["lords_day"] == "Dia do Senhor 45"
    assert units[116]["lords_day_raw"] == "Dia do Senhor 4"
    assert units[116]["lords_day_inferred"] is True


def test_catechism_reference_parse_issues_are_explicit_without_inference():
    structure = json.loads(
        Path("corpus/reports/structure_analysis/catecismo-heidelberg.structure.json").read_text(
            encoding="utf-8"
        )
    )
    units = {unit["question_number"]: unit for unit in structure["catechism_units"]}

    assert units[47]["references"]["1"] == "Mt 28.20."
    assert units[47]["unresolved_answer_markers"] == []
    assert units[47]["reference_parse_issues"] == []

    assert units[60]["reference_parse_issues"] == [
        {
            "marker": "2",
            "raw_reference": "2. 3.9, 10.",
            "issue": "missing_bible_book",
            "status": "manual_review_required",
        }
    ]
    assert "2" not in units[60]["references"]
    assert units[60]["references"]["1"] == "Rm 3.21-28; Gl 2.16; Ef 2.8, 9; Fl 3.8-11."

    assert units[20]["reference_parse_issues"] == [
        {
            "marker": "2",
            "raw_reference": None,
            "issue": "missing_reference_entry",
            "status": "manual_review_required",
        }
    ]
    assert {
        "marker": "1",
        "raw_reference": "1. Mt 1.21; Hb 7.25.",
        "issue": "duplicated_reference_marker_suspected",
        "status": "manual_review_required",
    } in units[29]["reference_parse_issues"]

    assert units[63]["references"]["2"] == "Lc 17.10; 2 Tm 4.7, 8."
    assert units[72]["references"]["1"] == "Mt 3.11; 1Pe 3.21; 1 Jo 1.7."
    assert units[72]["reference_parse_issues"] == []

    for unit in structure["catechism_units"]:
        for issue in unit["reference_parse_issues"]:
            assert "possible_reference" not in issue


def test_westminster_top_level_page_classification_is_consistent():
    structure = json.loads(
        Path("corpus/reports/structure_analysis/confissao-fe-westminster.structure.json").read_text(
            encoding="utf-8"
        )
    )

    assert structure["introductory_pages"] == list(range(3, 18))
    assert structure["special_layout_pages"] == [18]


def test_westminster_omits_irrelevant_generic_analysis_fields():
    structure = json.loads(
        Path("corpus/reports/structure_analysis/confissao-fe-westminster.structure.json").read_text(
            encoding="utf-8"
        )
    )
    irrelevant_fields = {
        "titles",
        "chapters",
        "articles",
        "questions",
        "answers",
        "rejections",
        "lords_days",
        "parts",
        "possible_bible_references_count",
        "notes_count",
        "possible_notes_examples",
        "pages",
        "recommended_chunking_strategy",
        "risks",
    }

    assert irrelevant_fields.isdisjoint(structure)


def test_westminster_first_chapter_sections_are_structured():
    structure = json.loads(
        Path("corpus/reports/structure_analysis/confissao-fe-westminster.structure.json").read_text(
            encoding="utf-8"
        )
    )
    westminster = structure["westminster_structure"]
    chapter = westminster["chapters"][0]
    section_one = chapter["sections"][0]
    section_two = chapter["sections"][1]

    assert westminster["chapter_count"] == 33
    assert chapter["chapter_title"] == "CAPÍTULO I DA ESCRITURA SAGRADA"
    assert chapter["section_count"] == 10
    assert section_one["chunk_type"] == "confessional_section"
    assert section_one["section_number"] == "I"
    assert section_one["section_text"].startswith("Ainda que a luz da natureza")
    assert section_one["biblical_references"] == [
        "Rm 2:14,15",
        "Rm 1:19,20",
        "Rm 1:32",
        "Rm 2:1",
        "Sl 19:1-3",
        "1Co 1:21",
        "1Co 2:13,14",
        "Hb 1:1",
        "Pv 22:19-21",
        "Lc 1:3,4",
        "Rm 15:4",
        "Mt 4:4,7,10",
        "Is 8:19,20",
        "2Tm 3:15",
        "2Pe 1:19",
        "Hb 1:1,2",
    ]
    assert "ANTIGO TESTAMENTO" in section_two["section_text"]
    assert "NOVO TESTAMENTO" in section_two["section_text"]
    assert section_two["biblical_references"] == ["Lc 16:29,31", "Ef 2:20", "Ap 22:18,19", "2Tm 3:16"]


def test_westminster_special_layout_preserves_biblical_books_table():
    structure = json.loads(
        Path("corpus/reports/structure_analysis/confissao-fe-westminster.structure.json").read_text(
            encoding="utf-8"
        )
    )
    layout = structure["westminster_structure"]["special_layouts"][0]

    assert layout["page"] == 18
    assert layout["text"].startswith("ANTIGO TESTAMENTO\nGênesis (Gn), Êxodo (Ex)")
    assert "Malaquias (Ml)" in layout["text"]
    assert "NOVO TESTAMENTO\nMateus (Mt), Marcos (Mc)" in layout["text"]
    assert "Apocalipse (Ap)" in layout["text"]


def test_canons_of_dort_structure_contains_articles_and_rejections():
    structure = json.loads(
        Path("corpus/reports/structure_analysis/canones-de-dort.structure.json").read_text(
            encoding="utf-8"
        )
    )
    canons = structure["canons_structure"]

    assert canons["doctrinal_chapter_count"] == 4
    assert canons["article_count"] == 59
    assert canons["error_refutation_count"] == 34
    assert canons["has_conclusion"] is True


def test_canons_of_dort_top_level_page_classification_is_consistent():
    structure = json.loads(
        Path("corpus/reports/structure_analysis/canones-de-dort.structure.json").read_text(
            encoding="utf-8"
        )
    )

    assert structure["introductory_pages"] == [1]
    assert "possible_introductory_pages" not in structure
    assert structure["special_layout_pages"] == []


def test_canons_of_dort_omits_irrelevant_generic_analysis_fields():
    structure = json.loads(
        Path("corpus/reports/structure_analysis/canones-de-dort.structure.json").read_text(
            encoding="utf-8"
        )
    )

    irrelevant_fields = {
        "questions",
        "answers",
        "lords_days",
        "parts",
        "possible_bible_references_count",
        "notes_count",
        "possible_notes_examples",
        "pages",
        "recommended_chunking_strategy",
        "risks",
    }

    assert irrelevant_fields.isdisjoint(structure)


def test_canons_of_dort_article_has_text_and_references():
    structure = json.loads(
        Path("corpus/reports/structure_analysis/canones-de-dort.structure.json").read_text(
            encoding="utf-8"
        )
    )
    fifth_chapter = structure["canons_structure"]["doctrinal_chapters"][-1]
    article = next(item for item in fifth_chapter["articles"] if item["article_number"] == "12")

    assert article["article_title"] == "Esta certeza é um estímulo à piedade"
    assert article["article_text"].startswith("Esta certeza de perseverança")
    assert article["reference_in_text"] == []
    assert article["article_references"] == "Rm 12.1; Sl 56.12, 13; 116.12; Tt 2.11-14; 1Jo 3.3."
    assert article["chunk_type"] == "doctrinal_article"


def test_canons_of_dort_article_preserves_inline_references_in_text():
    structure = json.loads(
        Path("corpus/reports/structure_analysis/canones-de-dort.structure.json").read_text(
            encoding="utf-8"
        )
    )
    first_chapter = structure["canons_structure"]["doctrinal_chapters"][0]
    article = first_chapter["articles"][0]

    assert article["article_number"] == "1"
    assert "Deus” (Rm 3.19, 23)" in article["article_text"]
    assert "“o salário do pecado é a morte” (Rm 6.23)" in article["article_text"]
    assert article["reference_in_text"] == ["(Rm 3.19, 23)", "(Rm 6.23)"]
    assert article["article_references"] == "Rm 5.12; Rm 3.19, 23; Rm 6.23."
    assert "Deus”" not in article["article_references"]


def test_canons_of_dort_rejection_pairs_have_error_and_refutation():
    structure = json.loads(
        Path("corpus/reports/structure_analysis/canones-de-dort.structure.json").read_text(
            encoding="utf-8"
        )
    )
    first_chapter = structure["canons_structure"]["doctrinal_chapters"][0]
    first_pair = first_chapter["rejection_of_errors"]["pairs"][0]

    assert first_pair["chunk_type"] == "error_refutation"
    assert first_pair["error_heading"] == "Erro 1"
    assert first_pair["error_text"].startswith("— O completo e total decreto")
    assert first_pair["refutation_text"].startswith("— Esse erro é um engano")
    assert first_pair["refutation_references"] == ["Jo 17.6", "At 13.48", "Ef 1.4"]


def test_canons_of_dort_conclusion_is_structured():
    structure = json.loads(
        Path("corpus/reports/structure_analysis/canones-de-dort.structure.json").read_text(
            encoding="utf-8"
        )
    )
    conclusion = structure["canons_structure"]["conclusion"]

    assert conclusion["title"] == "Conclusão"
    assert conclusion["paragraphs"][0]["paragraph_type"] == "paragraph"
    assert conclusion["paragraphs"][1]["paragraph_type"] == "numbered_claim"
    assert conclusion["paragraphs"][1]["number"] == "1"


def test_london_baptist_top_level_page_classification_is_consistent():
    structure = json.loads(
        Path("corpus/reports/structure_analysis/confissao-batista-londres-1689.structure.json").read_text(
            encoding="utf-8"
        )
    )

    assert structure["introductory_pages"] == [1]
    assert structure["special_layout_pages"] == [3]


def test_london_baptist_omits_irrelevant_generic_analysis_fields():
    structure = json.loads(
        Path("corpus/reports/structure_analysis/confissao-batista-londres-1689.structure.json").read_text(
            encoding="utf-8"
        )
    )
    irrelevant_fields = {
        "titles",
        "chapters",
        "articles",
        "questions",
        "answers",
        "rejections",
        "lords_days",
        "parts",
        "possible_bible_references_count",
        "notes_count",
        "possible_notes_examples",
        "pages",
        "recommended_chunking_strategy",
        "risks",
    }

    assert irrelevant_fields.isdisjoint(structure)


def test_london_baptist_special_layouts_preserve_testament_tables():
    structure = json.loads(
        Path("corpus/reports/structure_analysis/confissao-batista-londres-1689.structure.json").read_text(
            encoding="utf-8"
        )
    )
    layouts = structure["london_baptist_structure"]["special_layouts"]

    assert layouts[0]["page"] == 3
    assert layouts[0]["text"].startswith("O VELHO TESTAMENTO\nGênesis 1 Reis Eclesiastes Obadias")
    assert "2 Samuel Provérbios Amós" in layouts[0]["text"]
    assert layouts[1]["text"].startswith("O NOVO TESTAMENTO\nMateus Efésios Hebreus")
    assert "Gálatas Filemom Apocalipse" in layouts[1]["text"]


def test_london_baptist_chapter_two_first_paragraph_is_structured():
    structure = json.loads(
        Path("corpus/reports/structure_analysis/confissao-batista-londres-1689.structure.json").read_text(
            encoding="utf-8"
        )
    )
    london = structure["london_baptist_structure"]
    chapter = next(item for item in london["chapters"] if item["chapter_number"] == "2")
    paragraph = next(item for item in chapter["paragraphs"] if item["paragraph_number"] == "1")

    assert london["chapter_count"] == 32
    assert chapter["chapter_title"] == "CAPÍTULO 2 DEUS E A SANTÍSSIMA TRINDADE"
    assert london["paragraph_count"] == 157
    assert paragraph["chunk_type"] == "confessional_paragraph"
    assert paragraph["paragraph_text"].startswith("O Senhor nosso Deus é somente um")
    assert paragraph["reference_in_text"] == [str(number) for number in range(1, 17)]
    assert paragraph["reference_associations"]["1"] == ["1Co.8.4,6", "Dt.6.4"]
    assert paragraph["reference_associations"]["2"] == ["Jr.10.10", "Is.48.12"]
    assert paragraph["reference_associations"]["3"] == ["Êx.3.14"]
    assert paragraph["reference_associations"]["7"] == ["1Rs.8.27", "Jr.23.23"]
    assert paragraph["reference_associations"]["16"] == ["Êx.34.7", "Na.1.2,3"]
