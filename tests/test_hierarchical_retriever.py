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
    Path("src/sola_bot/retrieval/parent_context.py"),
    Path("src/sola_bot/retrieval/hierarchical_retriever.py"),
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
    from sola_bot.retrieval.retrieval_result import RetrievalResult

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
    from sola_bot.retrieval.parent_context import build_parent_key

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


def test_parent_context_builder_loads_chunks_and_groups_without_mixing_documents(tmp_path):
    from sola_bot.retrieval.parent_context import ParentContextBuilder, build_parent_key

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
    from sola_bot.retrieval.parent_context import ParentContextBuilder

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
    from sola_bot.retrieval.parent_context import ParentContextBuilder

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

    from sola_bot.retrieval.hierarchical_retriever import HierarchicalRetriever

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
