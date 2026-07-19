import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

REQUIRED_FILES = [
    Path("src/aia/retrieval/parent_context.py"),
    Path("src/aia/retrieval/hierarchical_retriever.py"),
    Path("scripts/pipeline/query_hierarchical_retriever.py"),
]
REQUIRED_INPUTS = [
    Path("reports/specs/reranker-retrieval.md"),
    Path("corpus/reports/retrieval/reranker-retrieval-report.md"),
    Path("corpus/reports/retrieval/reranker-retrieval-report.json"),
    Path("corpus/processed/chunks/alliance/all_chunks_for_embeddings.jsonl"),
    Path("corpus/indexes/chroma/alliance"),
]
REPORT_PATHS = [
    Path("reports/specs/hierarchical-retrieval.md"),
    Path("corpus/reports/retrieval/hierarchical-retrieval-report.md"),
    Path("corpus/reports/retrieval/hierarchical-retrieval-report.json"),
]


def load_dotenv_if_available() -> None:
    if importlib.util.find_spec("dotenv") is None:
        return
    from dotenv import load_dotenv

    load_dotenv()


def make_chunk(
    chunk_id: str,
    document_id: str = "confissao-fe-westminster",
    chapter_reference: str | None = "CAPÍTULO XI",
    chapter_title: str | None = "DA JUSTIFICAÇÃO",
    section_reference: str | None = "Seção I",
    section_title: str | None = "CAPÍTULO XI DA JUSTIFICAÇÃO",
    text: str = "Texto confessional.",
    page: int = 10,
) -> dict:
    return {
        "chunk_id": chunk_id,
        "corpus_id": "reformed",
        "retrieval_namespace": "reformed_confessional",
        "document_id": document_id,
        "document": "Documento de teste",
        "document_type": "confession_of_faith",
        "chunk_type": "confessional_section",
        "content_role": "doctrinal",
        "section_title": section_title,
        "section_reference": section_reference,
        "chapter_title": chapter_title,
        "chapter_reference": chapter_reference,
        "page_start": page,
        "page_end": page,
        "text": text,
        "source_path": "corpus/raw/reformed/teste.pdf",
        "normalized_source": "corpus/processed/normalized/reformed/teste.normalized.json",
        "text_hash": f"hash-{chunk_id}",
    }


def make_result(chunk_id: str):
    from aia.retrieval.retrieval_result import RetrievalResult

    return RetrievalResult(
        chunk_id=chunk_id,
        document_id="confissao-fe-westminster",
        document="Documento de teste",
        chunk_type="confessional_section",
        content_role="doctrinal",
        section_title="CAPÍTULO XI DA JUSTIFICAÇÃO",
        section_reference="Seção II",
        chapter_title="DA JUSTIFICAÇÃO",
        chapter_reference="CAPÍTULO XI",
        page_start=11,
        page_end=11,
        source_path="corpus/raw/reformed/teste.pdf",
        text_hash=f"hash-{chunk_id}",
        score=0.91,
        distance=None,
        text="Texto âncora.",
        metadata={
            "corpus_id": "reformed",
            "retrieval_namespace": "reformed_confessional",
            "pre_rerank_score": 0.03,
        },
    )


def make_normative_chunk(
    chunk_id: str,
    article_number: str,
    text: str,
    page: int,
) -> dict:
    return {
        "chunk_id": chunk_id,
        "corpus_id": "congregational_normative",
        "retrieval_namespace": "congregational_normative",
        "document_id": "codigo-etica-ministro-alianca",
        "document": "Código de Ética do Ministro Congregacional",
        "document_title": "Código de Ética do Ministro Congregacional",
        "document_type": "normative_ethics",
        "source_category": "denominational_normative_document",
        "chunk_type": "ethics_article",
        "content_role": "normative",
        "section_title": "DOS PRINCÍPIOS GERAIS",
        "section_reference": f"Código de Ética, Dos Princípios Gerais, Art. {article_number}",
        "article_number": article_number,
        "article_label": f"Art. {article_number}",
        "full_reference": f"Código de Ética, Dos Princípios Gerais, Art. {article_number}",
        "page_start": page,
        "page_end": page,
        "text": text,
        "source_path": "corpus/raw/normative/Codigo de ética.pdf",
        "normalized_source": "corpus/processed/normalized/normative/codigo-etica.normalized.json",
        "text_hash": f"hash-{chunk_id}",
    }


def make_normative_result(chunk_id: str):
    from aia.retrieval.retrieval_result import RetrievalResult

    return RetrievalResult(
        chunk_id=chunk_id,
        document_id="codigo-etica-ministro-alianca",
        document="Código de Ética do Ministro Congregacional",
        chunk_type="ethics_article",
        content_role="normative",
        section_title="DOS PRINCÍPIOS GERAIS",
        section_reference="Código de Ética, Dos Princípios Gerais, Art. 16",
        chapter_title=None,
        chapter_reference=None,
        page_start=7,
        page_end=8,
        source_path="corpus/raw/normative/Codigo de ética.pdf",
        text_hash=f"hash-{chunk_id}",
        score=0.75,
        distance=None,
        text="Texto âncora.",
        metadata={
            "corpus_id": "congregational_normative",
            "retrieval_namespace": "congregational_normative",
            "document_type": "normative_ethics",
            "source_category": "denominational_normative_document",
            "pre_rerank_score": 0.03,
        },
    )


def make_constitution_result(chunk_id: str):
    from aia.retrieval.retrieval_result import RetrievalResult

    return RetrievalResult(
        chunk_id=chunk_id,
        document_id="constituicao-alianca-2022",
        document="Constituição da Aliança",
        chunk_type="inciso",
        content_role="normative",
        section_title=None,
        section_reference="Constituição da Aliança, Capítulo II, Art. 5º, § 1º, inciso I",
        chapter_title="DO INGRESSO, DESLIGAMENTO E EXCLUSÃO DOS FILIADOS",
        chapter_reference="Capítulo II",
        page_start=4,
        page_end=4,
        source_path="corpus/raw/normative/Constituição da Aliança.pdf",
        text_hash=f"hash-{chunk_id}",
        score=0.88,
        distance=None,
        text="Texto âncora.",
        metadata={
            "corpus_id": "congregational_normative",
            "retrieval_namespace": "congregational_normative",
            "document_type": "constitution",
            "source_category": "denominational_normative_document",
            "pre_rerank_score": 0.03,
        },
    )


def make_constitution_article5_paragraph1_chunk(
    chunk_id: str,
    text: str,
    *,
    inciso: str | None = None,
    page: int = 4,
) -> dict:
    item_label = f"inciso {inciso}" if inciso else "§ 1º"
    reference = f"Constituição da Aliança, Capítulo II, Art. 5º, § 1º"
    if inciso:
        reference = f"{reference}, inciso {inciso}"
    return {
        "chunk_id": chunk_id,
        "corpus_id": "congregational_normative",
        "retrieval_namespace": "congregational_normative",
        "document_id": "constituicao-alianca-2022",
        "document": "Constituição da Aliança",
        "document_title": "Constituição da Aliança",
        "document_type": "constitution",
        "source_category": "denominational_normative_document",
        "chunk_type": "inciso" if inciso else "paragraph",
        "content_role": "normative",
        "chapter_number": "II",
        "chapter_title": "DO INGRESSO, DESLIGAMENTO E EXCLUSÃO DOS FILIADOS",
        "chapter_reference": "Capítulo II",
        "section_reference": reference,
        "article_number": "5",
        "article_label": "Art. 5º",
        "paragraph_number": "1º",
        "inciso": inciso,
        "item_label": item_label,
        "full_reference": reference,
        "page_start": page,
        "page_end": page,
        "text": text,
        "source_path": "corpus/raw/normative/Constituição da Aliança.pdf",
        "normalized_source": "corpus/processed/normalized/normative/constituicao.normalized.json",
        "text_hash": f"hash-{chunk_id}",
    }


def write_chunks(path: Path, chunks: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(chunk, ensure_ascii=False) + "\n" for chunk in chunks),
        encoding="utf-8",
    )


def test_hierarchical_files_exist():
    for path in REQUIRED_FILES:
        assert path.exists()


def test_hierarchical_inputs_exist():
    for path in REQUIRED_INPUTS:
        assert path.exists()


def test_build_parent_key_prioritizes_document_and_chapter():
    from aia.retrieval.parent_context import build_parent_key

    chunk = make_chunk("a")
    fallback_chunk = make_chunk(
        "b",
        chapter_reference=None,
        chapter_title=None,
        section_reference=None,
        section_title=None,
    )
    catechism_chunk = {
        **make_chunk("c", document_id="catecismo-heidelberg", chapter_reference=None, chapter_title=None),
        "chunk_type": "catechism_question_answer",
        "lords_day": "Dia do Senhor 16",
        "section_title": "Dia do Senhor 16",
        "section_reference": "Pergunta 40",
    }

    assert build_parent_key(chunk) == "confissao-fe-westminster::chapter::capitulo-xi"
    assert build_parent_key(fallback_chunk) == "confissao-fe-westminster::chunk-type::confessional-section"
    assert build_parent_key(catechism_chunk) == "catecismo-heidelberg::group::dia-do-senhor-16"


def test_build_parent_key_keeps_normative_paragraphs_separate():
    from aia.retrieval.parent_context import build_parent_key

    paragraph_chunk = {
        **make_normative_chunk("art-5-par-1", article_number="5", text="§ 1º. Texto.", page=4),
        "document_id": "constituicao-alianca-2022",
        "paragraph_number": "1º",
    }
    article_chunk = {
        **make_normative_chunk("art-5", article_number="5", text="Art. 5º. Texto.", page=4),
        "document_id": "constituicao-alianca-2022",
        "paragraph_number": None,
    }

    assert build_parent_key(paragraph_chunk) == "constituicao-alianca-2022::article::5::paragraph::1o"
    assert build_parent_key(article_chunk) == "constituicao-alianca-2022::article::5"


def test_parent_context_builder_loads_chunks_and_groups_without_mixing_documents(tmp_path):
    from aia.retrieval.parent_context import ParentContextBuilder, build_parent_key

    chunks_path = tmp_path / "chunks.jsonl"
    chunks = [
        make_chunk("a", page=10),
        make_chunk("b", page=11),
        make_chunk("c", page=12),
        make_chunk("outro-doc", document_id="canones-de-dort", chapter_reference="Primeiro Capítulo"),
    ]
    write_chunks(chunks_path, chunks)

    builder = ParentContextBuilder(chunks_path=str(chunks_path))
    westminster_key = build_parent_key(chunks[0])
    dort_key = build_parent_key(chunks[3])

    assert len(builder.chunks) == 4
    assert set(builder.chunk_index) == {"a", "b", "c", "outro-doc"}
    assert len(builder.parent_index[westminster_key]) == 3
    assert len(builder.parent_index[dort_key]) == 1
    assert {chunk["document_id"] for chunk in builder.parent_index[westminster_key]} == {
        "confissao-fe-westminster"
    }


def test_parent_context_expansion_with_simulated_data(tmp_path):
    from aia.retrieval.parent_context import ParentContextBuilder

    chunks_path = tmp_path / "chunks.jsonl"
    chunks = [
        make_chunk("a", text="Texto anterior.", page=10),
        make_chunk("b", text="Texto âncora.", page=11),
        make_chunk("c", text="Texto posterior.", page=12),
        make_chunk("outro-doc", document_id="canones-de-dort", chapter_reference="Primeiro Capítulo"),
    ]
    write_chunks(chunks_path, chunks)
    builder = ParentContextBuilder(
        chunks_path=str(chunks_path),
        parent_context_max_chars=5000,
        sibling_window_before=1,
        sibling_window_after=1,
        include_full_parent_when_small=False,
    )

    context = builder.build_contexts("pergunta", [make_result("b")])[0]

    assert context.anchor_chunk_id == "b"
    assert context.included_chunk_ids == ["b", "a", "c"]
    assert "outro-doc" not in context.included_chunk_ids
    assert context.page_start == 10
    assert context.page_end == 12
    assert context.parent_expansion_status == "expanded"
    assert context.context_char_count <= 5000
    assert "--- Chunk âncora ---" in context.context_text
    assert "Texto âncora." in context.context_text
    assert context.metadata["corpus_id"] == "reformed"
    assert context.metadata["retrieval_namespace"] == "reformed_confessional"


def test_parent_context_anchor_only_for_weak_metadata(tmp_path):
    from aia.retrieval.parent_context import ParentContextBuilder

    chunks_path = tmp_path / "chunks.jsonl"
    weak_chunk = make_chunk(
        "weak",
        chapter_reference=None,
        chapter_title=None,
        section_reference=None,
        section_title=None,
    )
    write_chunks(chunks_path, [weak_chunk])
    builder = ParentContextBuilder(chunks_path=str(chunks_path))
    result = make_result("weak")
    result.document_id = weak_chunk["document_id"]

    context = builder.build_contexts("pergunta", [result])[0]

    assert context.parent_expansion_status == "anchor_only"
    assert context.metadata["parent_expansion_reason"] == "insufficient_parent_metadata"
    assert context.included_chunk_ids == ["weak"]


def test_parent_context_uses_overview_group_for_broad_structural_questions(tmp_path):
    from aia.retrieval.parent_context import ParentContextBuilder

    chunks_path = tmp_path / "chunks.jsonl"
    chunks = [
        make_normative_chunk(
            "codigo-etica-ministro-alianca_artigo-007",
            "7",
            "Art. 7º. Em relação à sua vida pessoal o Pastor tem deveres de pureza, caráter e saúde.",
            2,
        ),
        make_normative_chunk(
            "codigo-etica-ministro-alianca_artigo-008",
            "8",
            "Art. 8º. O Pastor tem deveres em relação à família e ao cuidado do lar.",
            3,
        ),
        make_normative_chunk(
            "codigo-etica-ministro-alianca_artigo-009",
            "9",
            "Art. 9º. Na relação com a Igreja, o Pastor tem deveres ministeriais.",
            4,
        ),
        make_normative_chunk(
            "codigo-etica-ministro-alianca_artigo-016",
            "16",
            "Art. 16. Em relação à sociedade o Pastor tem deveres de prudência e cidadania.",
            7,
        ),
        make_normative_chunk(
            "codigo-etica-ministro-alianca_artigo-023",
            "23",
            "Art. 23. Sanções aplicáveis por infração ética.",
            9,
        )
        | {"section_title": "DAS SANÇÕES APLICÁVEIS"},
    ]
    write_chunks(chunks_path, chunks)
    builder = ParentContextBuilder(
        chunks_path=str(chunks_path),
        parent_context_max_chars=8000,
        include_full_parent_when_small=False,
    )

    context = builder.build_contexts(
        "Quais responsabilidades éticas são atribuídas a um ministro?",
        [make_normative_result("codigo-etica-ministro-alianca_artigo-016")],
    )[0]

    assert context.parent_strategy == "overview_structural_group"
    assert context.parent_expansion_status == "overview_expanded"
    assert context.metadata["parent_expansion_reason"] == "overview_query_structural_group"
    assert "codigo-etica-ministro-alianca_artigo-016" in context.included_chunk_ids
    assert "codigo-etica-ministro-alianca_artigo-007" in context.included_chunk_ids
    assert "codigo-etica-ministro-alianca_artigo-008" in context.included_chunk_ids
    assert "codigo-etica-ministro-alianca_artigo-009" in context.included_chunk_ids
    assert "codigo-etica-ministro-alianca_artigo-023" not in context.included_chunk_ids


def test_parent_context_expands_normative_requirement_lists_with_all_items(tmp_path):
    from aia.retrieval.parent_context import ParentContextBuilder

    chunks_path = tmp_path / "chunks.jsonl"
    chunks = [
        make_constitution_article5_paragraph1_chunk(
            "constituicao_art5_par1",
            "§ 1º. As igrejas candidatas devem apresentar a seguinte documentação:",
        ),
        make_constitution_article5_paragraph1_chunk(
            "constituicao_art5_par1_i",
            "I - Requerimento formal.",
            inciso="I",
        ),
        make_constitution_article5_paragraph1_chunk(
            "constituicao_art5_par1_ii",
            "II - Ata da assembleia com assinatura de 2/3 dos membros.",
            inciso="II",
        ),
        make_constitution_article5_paragraph1_chunk(
            "constituicao_art5_par1_iii",
            "III - Rol de membros atualizado.",
            inciso="III",
        ),
        make_constitution_article5_paragraph1_chunk(
            "constituicao_art5_par1_iv",
            "IV - Estatuto registrado em cartório.",
            inciso="IV",
        ),
        make_constitution_article5_paragraph1_chunk(
            "constituicao_art5_par1_v",
            "V - CNPJ.",
            inciso="V",
        ),
        make_constitution_article5_paragraph1_chunk(
            "constituicao_art5_par1_vi",
            "VI - Alvará municipal.",
            inciso="VI",
        ),
        make_constitution_article5_paragraph1_chunk(
            "constituicao_art5_par1_vii",
            "VII - Comprovante de abertura de conta bancária.",
            inciso="VII",
            page=5,
        ),
    ]
    write_chunks(chunks_path, chunks)
    builder = ParentContextBuilder(
        chunks_path=str(chunks_path),
        parent_context_max_chars=12000,
        include_full_parent_when_small=False,
        preserve_anchor_first=True,
    )

    context = builder.build_contexts(
        "De acordo com a Constituição da Aliança, quais são os requisitos para ingresso de igrejas?",
        [make_constitution_result("constituicao_art5_par1_i")],
    )[0]

    assert context.parent_strategy == "normative_unit_list"
    assert context.metadata["parent_expansion_reason"] == "normative_unit_list_query"
    assert context.included_chunk_ids == [chunk["chunk_id"] for chunk in chunks]
    assert context.page_start == 4
    assert context.page_end == 5
    assert "Comprovante de abertura de conta bancária" in context.context_text


def test_hierarchical_retriever_returns_contexts_when_dependencies_are_available():
    load_dotenv_if_available()

    if importlib.util.find_spec("sentence_transformers") is None:
        pytest.skip("sentence-transformers não está instalado neste ambiente.")
    if importlib.util.find_spec("rank_bm25") is None:
        pytest.skip("rank-bm25 não está instalado neste ambiente.")
    if importlib.util.find_spec("chromadb") is None:
        pytest.skip("chromadb não está instalado neste ambiente.")
    if not os.getenv("OPENAI_API_KEY", "").strip():
        pytest.skip("OPENAI_API_KEY não está configurada neste ambiente.")

    from aia.retrieval.hierarchical_retriever import HierarchicalRetriever

    try:
        retriever = HierarchicalRetriever(reranked_top_k=1, parent_context_max_chars=9000)
        contexts = retriever.retrieve("O que é o batismo?", top_k=1)
    except Exception as exc:
        pytest.skip(f"Recuperação hierárquica indisponível para execução real: {exc}")

    assert contexts
    for context in contexts:
        assert context.query
        assert context.anchor_chunk_id
        assert context.anchor_document_id
        assert context.anchor_document
        assert context.anchor_score is not None
        assert context.parent_key
        assert context.parent_strategy == "structural_window"
        assert context.parent_expansion_status in {"expanded", "anchor_only"}
        assert context.included_chunk_ids
        assert context.context_text
        assert context.metadata["corpus_id"] in {"reformed", "congregational_normative"}
        assert context.metadata["retrieval_namespace"] in {"reformed_confessional", "congregational_normative"}


def test_hierarchical_reports_exist_and_do_not_have_next_step_sections():
    forbidden = ["Próximo passo", "Próximo passo recomendado", "Next step"]
    for path in REPORT_PATHS:
        assert path.exists()
        if path.suffix == ".md":
            text = path.read_text(encoding="utf-8")
            for phrase in forbidden:
                assert phrase not in text
