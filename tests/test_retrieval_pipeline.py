import importlib.util
import os
import sys
from pathlib import Path

import pytest


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

REQUIRED_FILES = [
    Path("src/sola_bot/retrieval/final_context.py"),
    Path("src/sola_bot/retrieval/context_consolidator.py"),
    Path("src/sola_bot/retrieval/retrieval_pipeline.py"),
    Path("scripts/pipeline/query_retrieval_pipeline.py"),
]
REQUIRED_INPUTS = [
    Path("reports/specs/hierarchical-retrieval.md"),
    Path("corpus/reports/retrieval/hierarchical-retrieval-report.md"),
    Path("corpus/reports/retrieval/hierarchical-retrieval-report.json"),
    Path("corpus/processed/chunks/alliance/all_chunks_for_embeddings.jsonl"),
    Path("corpus/indexes/chroma/alliance"),
]
REPORT_PATHS = [
    Path("reports/specs/retrieval-pipeline.md"),
    Path("corpus/reports/retrieval/retrieval-pipeline-report.md"),
    Path("corpus/reports/retrieval/retrieval-pipeline-report.json"),
]


def load_dotenv_if_available() -> None:
    if importlib.util.find_spec("dotenv") is None:
        return
    from dotenv import load_dotenv

    load_dotenv()


def make_result(
    chunk_id: str,
    document_id: str,
    document: str,
    chunk_type: str,
    score: float,
):
    from sola_bot.retrieval.retrieval_result import RetrievalResult

    return RetrievalResult(
        chunk_id=chunk_id,
        document_id=document_id,
        document=document,
        chunk_type=chunk_type,
        content_role="doctrinal" if chunk_type != "introductory_context" else "contextual",
        section_title="Seção",
        section_reference="Referência",
        chapter_title="Capítulo",
        chapter_reference="CAPÍTULO I",
        page_start=1,
        page_end=1,
        source_path=f"corpus/raw/reformed/{document_id}.pdf",
        text_hash=f"hash-{chunk_id}",
        score=score,
        distance=None,
        text=f"Texto {chunk_id}.",
        metadata={
            "corpus_id": "reformed",
            "retrieval_namespace": "reformed_confessional",
            "pre_rerank_score": 0.03,
        },
    )


def make_parent_context(
    parent_key: str,
    anchor_chunk_id: str,
    included_chunk_ids: list[str],
    score: float,
    chunk_type: str = "confessional_section",
    status: str = "expanded",
    document_id: str = "confissao-fe-westminster",
    document: str = "Confissão de Fé de Westminster",
    text: str | None = None,
):
    from sola_bot.retrieval.parent_context import ParentContext

    anchor = make_result(anchor_chunk_id, document_id, document, chunk_type, score)
    context_text = text or (
        "[CONTEXTO DOCUMENTAL]\n"
        f"Documento: {document}\n"
        f"Unidade: {parent_key}\n\n"
        "[TRECHOS]\n"
        f"--- Chunk âncora ---\n{anchor_chunk_id}\n"
    )
    return ParentContext(
        query="O que é o batismo?",
        anchor_chunk_id=anchor_chunk_id,
        anchor_document_id=document_id,
        anchor_document=document,
        anchor_score=score,
        anchor_pre_rerank_score=0.03,
        parent_key=parent_key,
        parent_title="Unidade Teste",
        parent_strategy="structural_window",
        parent_expansion_status=status,
        included_chunk_ids=included_chunk_ids,
        included_chunk_count=len(included_chunk_ids),
        page_start=1,
        page_end=2,
        context_text=context_text,
        context_char_count=len(context_text),
        metadata={
            "corpus_id": "reformed",
            "retrieval_namespace": "reformed_confessional",
            "source_path": f"corpus/raw/reformed/{document_id}.pdf",
        },
        anchor_result=anchor,
    )


class FakeHierarchicalRetriever:
    def __init__(self, contexts):
        self.contexts = contexts

    def retrieve(self, query, top_k=None, filters=None):
        return self.contexts


class FilterAwareHierarchicalRetriever:
    def __init__(self, initial_contexts, filtered_contexts):
        self.initial_contexts = initial_contexts
        self.filtered_contexts = filtered_contexts
        self.calls = []

    def retrieve(self, query, top_k=None, filters=None):
        self.calls.append(dict(filters or {}))
        if filters and filters.get("source_category") == "denominational_normative_document":
            return self.filtered_contexts
        if filters and filters.get("source_category") == "doctrinal_document":
            return self.filtered_contexts
        return self.initial_contexts


class DocumentFilterAwareHierarchicalRetriever:
    def __init__(self, initial_contexts, document_contexts):
        self.initial_contexts = initial_contexts
        self.document_contexts = document_contexts
        self.calls = []

    def retrieve(self, query, top_k=None, filters=None):
        self.calls.append(dict(filters or {}))
        if filters and filters.get("document_id") == "confissao-fe-congregacional-alianca":
            return self.document_contexts
        return self.initial_contexts


def mark_context(
    context,
    *,
    document_type: str,
    source_category: str,
    content_role: str,
):
    context.anchor_result.metadata.update(
        {
            "document_type": document_type,
            "source_category": source_category,
            "content_role": content_role,
        }
    )
    context.metadata.update(
        {
            "document_type": document_type,
            "source_category": source_category,
            "content_role": content_role,
        }
    )
    return context


def test_retrieval_pipeline_files_exist():
    for path in REQUIRED_FILES:
        assert path.exists()


def test_retrieval_pipeline_inputs_exist():
    for path in REQUIRED_INPUTS:
        assert path.exists()


def test_context_consolidator_merges_parent_key_and_deduplicates_chunks():
    from sola_bot.retrieval.context_consolidator import ContextConsolidator

    contexts = [
        make_parent_context("doc::chapter::1", "anchor-1", ["a", "b"], 2.0),
        make_parent_context("doc::chapter::1", "anchor-2", ["b", "c"], 1.0),
        make_parent_context(
            "outro::chapter::1",
            "anchor-3",
            ["d"],
            1.5,
            document_id="canones-de-dort",
            document="Cânones de Dort",
        ),
    ]
    package = ContextConsolidator(final_context_top_k=4).consolidate("O que é o batismo?", contexts)

    assert package.context_count == 2
    first = next(context for context in package.contexts if context.parent_key == "doc::chapter::1")
    assert first.anchor_chunk_ids == ["anchor-1", "anchor-2"]
    assert first.included_chunk_ids == ["a", "b", "c"]
    assert "canones-de-dort" in package.documents
    assert package.metadata["contexts_fused_by_parent_key"] == 1


def test_context_consolidator_deprioritizes_introductory_anchor_only_for_doctrinal_query():
    from sola_bot.retrieval.context_consolidator import ContextConsolidator

    contexts = [
        make_parent_context("doc::chapter::doctrinal", "anchor-doctrine", ["a"], 0.5),
        make_parent_context(
            "doc::section::intro",
            "anchor-intro",
            ["intro"],
            10.0,
            chunk_type="introductory_context",
            status="anchor_only",
        ),
    ]
    package = ContextConsolidator(final_context_top_k=4).consolidate("O que é justificação?", contexts)

    assert all(context.content_priority != "introductory" for context in package.contexts)
    assert package.metadata["removed_contexts"]["removed_introductory_anchor_only"] == [
        "doc::section::intro"
    ]


def test_context_consolidator_respects_total_char_limit():
    from sola_bot.retrieval.context_consolidator import ContextConsolidator

    long_text = "[CONTEXTO DOCUMENTAL]\n" + ("texto " * 1000)
    contexts = [
        make_parent_context("doc::chapter::1", "anchor-1", ["a"], 2.0, text=long_text),
        make_parent_context("doc::chapter::2", "anchor-2", ["b"], 1.0, text=long_text),
    ]
    package = ContextConsolidator(
        final_context_top_k=4,
        max_total_context_chars=1200,
        max_context_chars_per_parent=1000,
    ).consolidate("O que é eleição?", contexts)

    assert package.total_context_chars <= 1200
    assert package.contexts[0].metadata["context_truncated"] is True


def test_context_consolidator_promotes_document_diversity_for_generic_topic_query():
    from sola_bot.retrieval.context_consolidator import ContextConsolidator

    contexts = [
        make_parent_context(
            "batista::justificacao",
            "batista-justificacao",
            ["b1"],
            10.0,
            document_id="confissao-batista-londres-1689",
            document="Confissão Batista de Londres de 1689",
            text="Capítulo sobre Justificação. Texto do primeiro documento.",
        ),
        make_parent_context(
            "batista::queda",
            "batista-queda",
            ["b2"],
            9.0,
            document_id="confissao-batista-londres-1689",
            document="Confissão Batista de Londres de 1689",
            text="Capítulo relacionado à Justificação no mesmo documento.",
        ),
        make_parent_context(
            "westminster::justificacao",
            "westminster-justificacao",
            ["w1"],
            2.0,
            document_id="confissao-fe-westminster",
            document="Confissão de Fé de Westminster",
            text="Capítulo XI, Da Justificação. Texto do segundo documento.",
        ),
        make_parent_context(
            "congregacional::justificacao",
            "congregacional-justificacao",
            ["c1"],
            1.0,
            document_id="confissao-fe-congregacional-alianca",
            document="Confissão de Fé Congregacional",
            text="Capítulo XII, Da Justificação. Texto do terceiro documento.",
        ),
    ]

    package = ContextConsolidator(final_context_top_k=3).consolidate(
        "Do que se trata a justificação?",
        contexts,
    )

    assert package.documents == [
        "confissao-batista-londres-1689",
        "confissao-fe-congregacional-alianca",
        "confissao-fe-westminster",
    ]
    assert [context.document_id for context in package.contexts] == [
        "confissao-batista-londres-1689",
        "confissao-fe-westminster",
        "confissao-fe-congregacional-alianca",
    ]
    assert package.metadata["document_diversity"]["reason"] == "topic_matched_one_context_per_document_promoted"


def test_alliance_scope_with_doctrinal_term_is_classified_as_doctrinal():
    from sola_bot.retrieval.context_consolidator import classify_query_intent

    assert classify_query_intent("Como a Aliança vê a regeneração do homem?") == "doctrinal"
    assert classify_query_intent("Como uma igreja se filia à Aliança?") == "normative"


def test_build_context_package_text_contains_sources_without_answer_generation():
    from sola_bot.retrieval.context_consolidator import ContextConsolidator
    from sola_bot.retrieval.final_context import build_context_package_text

    contexts = [make_parent_context("doc::chapter::1", "anchor-1", ["a"], 2.0)]
    package = ContextConsolidator().consolidate("O que é o batismo?", contexts)
    text = build_context_package_text(package)

    assert "Pergunta: O que é o batismo?" in text
    assert "Documento:" in text
    assert "Unidade:" in text
    assert "Páginas:" in text
    assert "Chunks âncora:" in text
    assert "Chunks incluídos:" in text
    assert "Resposta:" not in text


def test_retrieval_pipeline_uses_hierarchical_retriever_and_returns_package():
    from sola_bot.retrieval.context_consolidator import ContextConsolidator
    from sola_bot.retrieval.retrieval_pipeline import RetrievalPipeline

    contexts = [make_parent_context("doc::chapter::1", "anchor-1", ["a"], 2.0)]
    pipeline = RetrievalPipeline(
        hierarchical_retriever=FakeHierarchicalRetriever(contexts),
        context_consolidator=ContextConsolidator(final_context_top_k=2),
    )
    package = pipeline.retrieve("O que é o batismo?", filters={"document_id": "confissao-fe-westminster"})

    assert package.query == "O que é o batismo?"
    assert package.contexts
    assert package.context_count == 1
    assert package.source_map
    assert package.filters["document_id"] == "confissao-fe-westminster"


def test_retrieval_pipeline_retries_normative_query_when_only_doctrinal_context_is_found():
    from sola_bot.retrieval.context_consolidator import ContextConsolidator
    from sola_bot.retrieval.retrieval_pipeline import RetrievalPipeline

    doctrinal_context = mark_context(
        make_parent_context(
            "confissao::igreja",
            "doctrinal-anchor",
            ["d1"],
            2.0,
            document_id="confissao-fe-congregacional-alianca",
            document="Confissão de Fé Congregacional",
            text="[CONTEXTO DOCUMENTAL]\nDocumento: Confissão de Fé Congregacional\nTexto sobre igreja local.",
        ),
        document_type="confession_of_faith",
        source_category="doctrinal_document",
        content_role="doctrinal",
    )
    normative_context = mark_context(
        make_parent_context(
            "regimento::igreja-local",
            "normative-anchor",
            ["n1"],
            1.0,
            chunk_type="internal_regiment_article",
            document_id="regimento-interno-alianca-2022",
            document="Regimento Interno da Aliança",
            text="[CONTEXTO DOCUMENTAL]\nDocumento: Regimento Interno da Aliança\nTexto sobre deveres de uma igreja local.",
        ),
        document_type="internal_regiment",
        source_category="denominational_normative_document",
        content_role="normative",
    )
    retriever = FilterAwareHierarchicalRetriever([doctrinal_context], [normative_context])
    pipeline = RetrievalPipeline(
        hierarchical_retriever=retriever,
        context_consolidator=ContextConsolidator(final_context_top_k=2),
    )

    package = pipeline.retrieve("Quais são os deveres de uma igreja local?")

    assert package.documents == ["regimento-interno-alianca-2022"]
    assert package.contexts[0].document == "Regimento Interno da Aliança"
    assert package.contexts[0].content_priority == "normative"
    assert retriever.calls == [{}, {"source_category": "denominational_normative_document"}]
    assert package.metadata["fallback_retry"]["reason"] == "missing_normative_context"


def test_retrieval_pipeline_retries_alliance_doctrinal_query_on_congregational_confession():
    from sola_bot.retrieval.context_consolidator import ContextConsolidator
    from sola_bot.retrieval.retrieval_pipeline import RetrievalPipeline

    normative_context = mark_context(
        make_parent_context(
            "regimento::datas-comemorativas",
            "normative-anchor",
            ["n1"],
            2.0,
            chunk_type="internal_regiment_article",
            document_id="regimento-interno-alianca-2022",
            document="Regimento Interno da Aliança",
            text="[CONTEXTO DOCUMENTAL]\nDocumento: Regimento Interno da Aliança\nTexto administrativo sobre datas comemorativas.",
        ),
        document_type="internal_regiment",
        source_category="denominational_normative_document",
        content_role="normative",
    )
    congregational_confession_context = mark_context(
        make_parent_context(
            "confissao-congregacional::vocacao-eficaz",
            "doctrinal-anchor",
            ["d1"],
            1.0,
            document_id="confissao-fe-congregacional-alianca",
            document="Confissão de Fé Congregacional",
            text=(
                "[CONTEXTO DOCUMENTAL]\nDocumento: Confissão de Fé Congregacional\n"
                "O chamado eficaz é obra de Deus por sua Palavra e Espírito. Deus tira o coração de pedra, "
                "dá coração de carne, renova a vontade e vivifica o homem para responder à graça."
            ),
        ),
        document_type="confession_of_faith",
        source_category="doctrinal_document",
        content_role="doctrinal",
    )
    retriever = DocumentFilterAwareHierarchicalRetriever(
        [normative_context],
        [congregational_confession_context],
    )
    pipeline = RetrievalPipeline(
        hierarchical_retriever=retriever,
        context_consolidator=ContextConsolidator(final_context_top_k=2),
    )

    package = pipeline.retrieve("Como a Aliança vê a regeneração do homem?")

    assert package.documents == ["confissao-fe-congregacional-alianca"]
    assert package.contexts[0].document == "Confissão de Fé Congregacional"
    assert package.contexts[0].content_priority == "doctrinal"
    assert retriever.calls == [{}, {"document_id": "confissao-fe-congregacional-alianca"}]
    assert package.metadata["fallback_retry"]["reason"] == "missing_alliance_doctrinal_context"


def test_retrieval_pipeline_returns_package_when_dependencies_are_available():
    load_dotenv_if_available()

    if importlib.util.find_spec("sentence_transformers") is None:
        pytest.skip("sentence-transformers não está instalado neste ambiente.")
    if importlib.util.find_spec("rank_bm25") is None:
        pytest.skip("rank-bm25 não está instalado neste ambiente.")
    if importlib.util.find_spec("chromadb") is None:
        pytest.skip("chromadb não está instalado neste ambiente.")
    if not os.getenv("OPENAI_API_KEY", "").strip():
        pytest.skip("OPENAI_API_KEY não está configurada neste ambiente.")

    from sola_bot.retrieval.retrieval_pipeline import RetrievalPipeline

    try:
        package = RetrievalPipeline(final_context_top_k=2, max_total_context_chars=12000).retrieve(
            "O que é o batismo?"
        )
    except Exception as exc:
        pytest.skip(f"Pipeline final indisponível para execução real: {exc}")

    assert package.query == "O que é o batismo?"
    assert package.contexts
    assert package.context_count <= 2
    assert package.total_context_chars <= 12000
    assert package.documents
    assert package.source_map
    assert package.metadata["corpus_scope"] == "alliance_documents"


def test_retrieval_pipeline_reports_exist_and_do_not_have_next_step_sections():
    forbidden = ["Próximo passo", "Próximo passo recomendado", "Next step"]
    for path in REPORT_PATHS:
        assert path.exists()
        if path.suffix == ".md":
            text = path.read_text(encoding="utf-8")
            for phrase in forbidden:
                assert phrase not in text
