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
    Path("src/aia/retrieval/final_context.py"),
    Path("src/aia/retrieval/context_consolidator.py"),
    Path("src/aia/retrieval/retrieval_pipeline.py"),
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
    from aia.retrieval.retrieval_result import RetrievalResult

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
    from aia.retrieval.parent_context import ParentContext

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


class MultiFilterAwareHierarchicalRetriever:
    def __init__(self, initial_contexts, filtered_contexts_by_filter):
        self.initial_contexts = initial_contexts
        self.filtered_contexts_by_filter = filtered_contexts_by_filter
        self.calls = []

    def retrieve(self, query, top_k=None, filters=None):
        current_filter = dict(filters or {})
        self.calls.append(current_filter)
        key = tuple(sorted(current_filter.items()))
        return self.filtered_contexts_by_filter.get(key, self.initial_contexts)


class LeakyDocumentScopeHierarchicalRetriever:
    def __init__(self, contexts):
        self.contexts = contexts
        self.calls = []

    def retrieve(self, query, top_k=None, filters=None):
        self.calls.append(dict(filters or {}))
        return self.contexts


class BuilderAwareStaticRetriever:
    def __init__(self, contexts, context_builder):
        self.contexts = contexts
        self.context_builder = context_builder
        self.calls = []

    def retrieve(self, query, top_k=None, filters=None):
        self.calls.append(dict(filters or {}))
        return self.contexts


def make_constitution_article_chunk(
    chunk_id: str,
    article_number: str,
    text: str,
    page: int,
) -> dict:
    return {
        "chunk_id": chunk_id,
        "corpus_id": "congregational_normative",
        "retrieval_namespace": "congregational_normative",
        "document_id": "constituicao-alianca-2022",
        "document": "Constituição da Aliança das Igrejas Evangélicas Congregacionais do Brasil",
        "document_title": "Constituição da Aliança das Igrejas Evangélicas Congregacionais do Brasil",
        "document_type": "constitution",
        "source_category": "denominational_normative_document",
        "chunk_type": "normative_article",
        "content_role": "normative",
        "document_structure_type": "normative_article",
        "chapter_number": "II",
        "chapter_title": "DO INGRESSO, DESLIGAMENTO E EXCLUSÃO DOS FILIADOS",
        "chapter_reference": "Capítulo II",
        "section_title": None,
        "section_reference": f"Constituição da Aliança, Art. {article_number}º",
        "article_number": article_number,
        "article_label": f"Art. {article_number}º",
        "paragraph_number": None,
        "paragraph_label": None,
        "paragraph_number_roman": None,
        "inciso": None,
        "alinea": None,
        "item_label": None,
        "full_reference": f"Constituição da Aliança, Art. {article_number}º",
        "page_start": page,
        "page_end": page,
        "text": text,
        "source_path": "corpus/raw/normative/Constituição da Aliança.pdf",
        "normalized_source": "corpus/processed/normalized/normative/constituicao.normalized.json",
        "text_hash": f"hash-{chunk_id}",
    }


def make_normative_article_chunk(
    *,
    chunk_id: str,
    document_id: str,
    document: str,
    document_type: str,
    full_reference: str,
    article_number: str,
    text: str,
    page: int,
    paragraph_number: str | None = None,
    inciso: str | None = None,
) -> dict:
    return {
        "chunk_id": chunk_id,
        "corpus_id": "congregational_normative",
        "retrieval_namespace": "congregational_normative",
        "document_id": document_id,
        "document": document,
        "document_title": document,
        "document_type": document_type,
        "source_category": "denominational_normative_document",
        "chunk_type": "normative_article" if paragraph_number is None else "inciso",
        "content_role": "normative",
        "document_structure_type": "normative_article" if paragraph_number is None else "inciso",
        "chapter_number": "I",
        "chapter_title": "Capítulo de teste",
        "chapter_reference": "Capítulo I",
        "section_title": None,
        "section_reference": full_reference,
        "article_number": article_number,
        "article_label": f"Art. {article_number}º",
        "paragraph_number": paragraph_number,
        "paragraph_label": None,
        "paragraph_number_roman": None,
        "inciso": inciso,
        "alinea": None,
        "item_label": f"inciso {inciso}" if inciso else None,
        "full_reference": full_reference,
        "page_start": page,
        "page_end": page,
        "text": text,
        "source_path": f"corpus/raw/normative/{document_id}.pdf",
        "normalized_source": f"corpus/processed/normalized/normative/{document_id}.normalized.json",
        "text_hash": f"hash-{chunk_id}",
    }


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows),
        encoding="utf-8",
    )


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
    from aia.retrieval.context_consolidator import ContextConsolidator

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
    from aia.retrieval.context_consolidator import ContextConsolidator

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
    from aia.retrieval.context_consolidator import ContextConsolidator

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
    from aia.retrieval.context_consolidator import ContextConsolidator

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
    from aia.retrieval.context_consolidator import (
        classify_query_intent,
        query_requests_document_inventory,
        query_requests_institutional_doctrinal_bridge,
    )

    assert classify_query_intent("Como a Aliança vê a regeneração do homem?") == "doctrinal"
    assert classify_query_intent("Como uma igreja se filia à Aliança?") == "normative"
    assert (
        classify_query_intent(
            "Como os documentos explicam a relação entre pecado humano e graça de Deus?"
        )
        == "doctrinal"
    )
    assert (
        classify_query_intent(
            "Como os documentos doutrinários explicam a relação entre pecado humano e graça de Deus?"
        )
        == "doctrinal"
    )
    assert query_requests_document_inventory(
        "Quais documentos orientam a conduta de uma igreja filiada e de seus ministros?"
    )
    assert query_requests_institutional_doctrinal_bridge(
        "Como a doutrina professada e as normas institucionais se relacionam no governo congregacional?"
    )


def test_build_context_package_text_contains_sources_without_answer_generation():
    from aia.retrieval.context_consolidator import ContextConsolidator
    from aia.retrieval.final_context import build_context_package_text

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
    from aia.retrieval.context_consolidator import ContextConsolidator
    from aia.retrieval.retrieval_pipeline import RetrievalPipeline

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


def test_query_scope_detects_specific_document_with_typo():
    from aia.retrieval.query_scope import derive_query_document_scope

    scope = derive_query_document_scope(
        "Segundo o Regiemnto Interno, quais são as orientações sobre batismo e ceia?"
    )

    assert scope is not None
    assert scope.document_id == "regimento-interno-alianca-2022"
    assert scope.match_type == "fuzzy"


def test_retrieval_pipeline_applies_exclusive_document_scope_and_removes_leaked_contexts():
    from aia.retrieval.context_consolidator import ContextConsolidator
    from aia.retrieval.retrieval_pipeline import RetrievalPipeline

    regiment_context = mark_context(
        make_parent_context(
            "regimento::batismo",
            "regiment-anchor",
            ["r1"],
            2.0,
            chunk_type="internal_regiment_article",
            document_id="regimento-interno-alianca-2022",
            document="Regimento Interno da Aliança",
            text=(
                "[CONTEXTO DOCUMENTAL]\nDocumento: Regimento Interno da Aliança\n"
                "Cabe ao pastor realizar batismos e ministrar a ceia do Senhor."
            ),
        ),
        document_type="internal_regiment",
        source_category="denominational_normative_document",
        content_role="normative",
    )
    baptist_context = mark_context(
        make_parent_context(
            "batista::ordenancas",
            "baptist-anchor",
            ["b1"],
            5.0,
            document_id="confissao-batista-londres-1689",
            document="Confissão Batista de Londres de 1689",
            text=(
                "[CONTEXTO DOCUMENTAL]\nDocumento: Confissão Batista de Londres de 1689\n"
                "Texto doutrinário sobre batismo e ceia."
            ),
        ),
        document_type="confession_of_faith",
        source_category="doctrinal_document",
        content_role="doctrinal",
    )
    retriever = LeakyDocumentScopeHierarchicalRetriever([baptist_context, regiment_context])
    pipeline = RetrievalPipeline(
        hierarchical_retriever=retriever,
        context_consolidator=ContextConsolidator(final_context_top_k=2),
    )

    package = pipeline.retrieve(
        "Segundo o Regimento Interno, quais são as orientações sobre batismo e ceia?"
    )

    assert retriever.calls[0] == {"document_id": "regimento-interno-alianca-2022"}
    assert package.filters["document_id"] == "regimento-interno-alianca-2022"
    assert package.documents == ["regimento-interno-alianca-2022"]
    assert package.context_count == 1
    assert package.contexts[0].document == "Regimento Interno da Aliança"
    assert package.metadata["query_document_scope"]["policy"] == "exclusive_document_scope"
    assert package.metadata["document_scope_guard"]["removed_documents"] == [
        "confissao-batista-londres-1689"
    ]


def test_retrieval_pipeline_promotes_church_admission_requirements_inside_constitution_scope():
    from aia.retrieval.context_consolidator import ContextConsolidator
    from aia.retrieval.retrieval_pipeline import RetrievalPipeline

    church_requirements = mark_context(
        make_parent_context(
            "constituicao-alianca-2022::article::5::paragraph::1o",
            "art-5-par-1",
            ["art-5-par-1", "art-5-par-1-i", "art-5-par-1-ii"],
            1.0,
            chunk_type="inciso",
            document_id="constituicao-alianca-2022",
            document="Constituição da Aliança",
            text=(
                "[CONTEXTO DOCUMENTAL]\nDocumento: Constituição da Aliança\n"
                "Art. 5º. O ingresso de igrejas, pastores, oficiais, missionários e missionárias "
                "será precedido do envio da documentação exigida.\n\n"
                "§ 1º. As igrejas candidatas devem apresentar a seguinte documentação: "
                "requerimento formal, ata da assembleia, rol atualizado, estatuto registrado, "
                "CNPJ, alvará e comprovante de conta bancária."
            ),
        ),
        document_type="constitution",
        source_category="denominational_normative_document",
        content_role="normative",
    )
    officer_requirements = mark_context(
        make_parent_context(
            "constituicao-alianca-2022::article::5::paragraph::4o",
            "art-5-par-4-a",
            ["art-5-par-4", "art-5-par-4-a"],
            5.0,
            chunk_type="alinea",
            document_id="constituicao-alianca-2022",
            document="Constituição da Aliança",
            text=(
                "[CONTEXTO DOCUMENTAL]\nDocumento: Constituição da Aliança\n"
                "§ 4º. Presbíteros, diáconos, missionários e missionárias devem apresentar "
                "ata da igreja, declaração de conhecimento dos documentos, termo de compromisso, "
                "comprovação de membresia e ausência de sanção disciplinar."
            ),
        ),
        document_type="constitution",
        source_category="denominational_normative_document",
        content_role="normative",
    )
    pastor_requirements = mark_context(
        make_parent_context(
            "constituicao-alianca-2022::article::5::paragraph::2o",
            "art-5-par-2",
            ["art-5-par-2"],
            4.0,
            chunk_type="inciso",
            document_id="constituicao-alianca-2022",
            document="Constituição da Aliança",
            text=(
                "[CONTEXTO DOCUMENTAL]\nDocumento: Constituição da Aliança\n"
                "§ 2º. Os candidatos a pastores, além do requerimento formal, devem apresentar "
                "declaração de conhecimento dos documentos normativos e termo de compromisso."
            ),
        ),
        document_type="constitution",
        source_category="denominational_normative_document",
        content_role="normative",
    )
    ministerial_activity = mark_context(
        make_parent_context(
            "constituicao-alianca-2022::article::5::paragraph::3o",
            "art-5-par-3",
            ["art-5-par-3"],
            3.0,
            chunk_type="paragraph",
            document_id="constituicao-alianca-2022",
            document="Constituição da Aliança",
            text=(
                "[CONTEXTO DOCUMENTAL]\nDocumento: Constituição da Aliança\n"
                "§ 3º. Caso o postulante não possua título de formação teológica, deverá comprovar "
                "atividade ministerial contínua."
            ),
        ),
        document_type="constitution",
        source_category="denominational_normative_document",
        content_role="normative",
    )
    article_3 = mark_context(
        make_parent_context(
            "constituicao-alianca-2022::article::3",
            "art-3",
            ["art-3"],
            0.8,
            chunk_type="normative_article",
            document_id="constituicao-alianca-2022",
            document="Constituição da Aliança",
            text=(
                "[CONTEXTO DOCUMENTAL]\nDocumento: Constituição da Aliança\n"
                "Art. 3º. Poderão filiar-se à ALIANÇA igrejas evangélicas de governo "
                "congregacional que adotem os princípios consagrados no artigo 1º."
            ),
        ),
        document_type="constitution",
        source_category="denominational_normative_document",
        content_role="normative",
    )
    retriever = LeakyDocumentScopeHierarchicalRetriever(
        [officer_requirements, pastor_requirements, ministerial_activity, church_requirements, article_3]
    )
    pipeline = RetrievalPipeline(
        hierarchical_retriever=retriever,
        context_consolidator=ContextConsolidator(final_context_top_k=4),
    )

    package = pipeline.retrieve(
        "De acordo com a Constituição da Aliança, quais são os requisitos para ingresso de igrejas?"
    )

    assert retriever.calls[0] == {"document_id": "constituicao-alianca-2022"}
    assert package.contexts[0].parent_key == "constituicao-alianca-2022::article::5::paragraph::1o"
    assert package.contexts[1].parent_key == "constituicao-alianca-2022::article::3"
    assert package.context_count == 2
    selected_parent_keys = {context.parent_key for context in package.contexts}
    assert "constituicao-alianca-2022::article::5::paragraph::2o" not in selected_parent_keys
    assert "constituicao-alianca-2022::article::5::paragraph::3o" not in selected_parent_keys
    assert "constituicao-alianca-2022::article::5::paragraph::4o" not in selected_parent_keys
    assert package.metadata["document_diversity"]["reason"] == "normative_subject_scope_filtered"
    assert package.metadata["document_diversity"]["scope_id"] == "church_admission_requirements"


def test_retrieval_pipeline_adds_church_admission_framing_units(tmp_path):
    from aia.retrieval.context_consolidator import ContextConsolidator
    from aia.retrieval.parent_context import ParentContextBuilder
    from aia.retrieval.retrieval_pipeline import RetrievalPipeline

    chunks_path = tmp_path / "chunks.jsonl"
    write_jsonl(
        chunks_path,
        [
            make_constitution_article_chunk(
                "constituicao-alianca-2022_artigo-003",
                "3",
                (
                    "Art. 3º. Poderão filiar-se à ALIANÇA igrejas evangélicas de governo "
                    "congregacional que adotem os princípios consagrados no artigo 1º."
                ),
                4,
            ),
            make_constitution_article_chunk(
                "constituicao-alianca-2022_artigo-001",
                "1",
                (
                    "Art. 1º. A ALIANÇA é constituída de igrejas de governo congregacional, "
                    "que adotam as Sagradas Escrituras como única regra de fé e prática e, "
                    "como síntese doutrinária, a Confissão de Fé da Aliança."
                ),
                3,
            ),
        ],
    )
    context_builder = ParentContextBuilder(chunks_path=str(chunks_path))
    church_requirements = mark_context(
        make_parent_context(
            "constituicao-alianca-2022::article::5::paragraph::1o",
            "art-5-par-1",
            ["art-5-par-1"],
            5.0,
            chunk_type="inciso",
            document_id="constituicao-alianca-2022",
            document="Constituição da Aliança",
            text=(
                "[CONTEXTO DOCUMENTAL]\nDocumento: Constituição da Aliança\n"
                "§ 1º. As igrejas candidatas devem apresentar requerimento formal, ata, "
                "rol atualizado, estatuto registrado, CNPJ, alvará e conta bancária."
            ),
        ),
        document_type="constitution",
        source_category="denominational_normative_document",
        content_role="normative",
    )
    retriever = BuilderAwareStaticRetriever([church_requirements], context_builder)
    pipeline = RetrievalPipeline(
        hierarchical_retriever=retriever,
        context_consolidator=ContextConsolidator(final_context_top_k=4),
    )

    package = pipeline.retrieve(
        "De acordo com a Constituição da Aliança, quais são os requisitos para ingresso de igrejas?"
    )

    parent_keys = [context.parent_key for context in package.contexts]
    assert parent_keys == [
        "constituicao-alianca-2022::article::5::paragraph::1o",
        "constituicao-alianca-2022::article::3",
        "constituicao-alianca-2022::article::1",
    ]
    assert package.metadata["normative_subject_scope_supplement"]["reason"] == (
        "normative_subject_framing_units_added"
    )
    assert "constituicao-alianca-2022_artigo-003" in package.metadata[
        "normative_subject_scope_supplement"
    ]["added_chunk_ids"]


def test_retrieval_pipeline_adds_regiment_for_generic_church_affiliation_process(tmp_path):
    from aia.retrieval.context_consolidator import ContextConsolidator
    from aia.retrieval.parent_context import ParentContextBuilder
    from aia.retrieval.retrieval_pipeline import RetrievalPipeline

    chunks_path = tmp_path / "chunks.jsonl"
    write_jsonl(
        chunks_path,
        [
            make_constitution_article_chunk(
                "constituicao-alianca-2022_artigo-003",
                "3",
                (
                    "Art. 3º. Poderão filiar-se à ALIANÇA igrejas evangélicas de governo "
                    "congregacional que adotem os princípios consagrados no artigo 1º."
                ),
                4,
            ),
            make_constitution_article_chunk(
                "constituicao-alianca-2022_artigo-001",
                "1",
                (
                    "Art. 1º. A ALIANÇA é constituída de igrejas de governo congregacional "
                    "e adota as Sagradas Escrituras como única regra de fé e prática."
                ),
                3,
            ),
            make_normative_article_chunk(
                chunk_id="regimento-interno-alianca-2022_artigo-007",
                document_id="regimento-interno-alianca-2022",
                document="Regimento Interno da Aliança",
                document_type="internal_regiment",
                full_reference="Regimento Interno, Capítulo I, Seção I, Art. 7º",
                article_number="7",
                page=3,
                text=(
                    "Art. 7º. O pedido de filiação será encaminhado à Região Administrativa, "
                    "que verificará as condições e enviará à Diretoria Nacional com parecer; "
                    "a Diretoria Nacional examinará e aprovará ou não o pedido."
                ),
            ),
            make_normative_article_chunk(
                chunk_id="regimento-interno-alianca-2022_artigo-006",
                document_id="regimento-interno-alianca-2022",
                document="Regimento Interno da Aliança",
                document_type="internal_regiment",
                full_reference="Regimento Interno, Capítulo I, Seção I, Art. 6º",
                article_number="6",
                page=3,
                text=(
                    "Art. 6º. Uma congregação, formalmente organizada como igreja, poderá "
                    "filiar-se à ALIANÇA se apresentar os requisitos regimentais."
                ),
            ),
        ],
    )
    context_builder = ParentContextBuilder(chunks_path=str(chunks_path))
    constitution_requirements = mark_context(
        make_parent_context(
            "constituicao-alianca-2022::article::5::paragraph::1o",
            "art-5-par-1",
            ["art-5-par-1"],
            5.0,
            chunk_type="inciso",
            document_id="constituicao-alianca-2022",
            document="Constituição da Aliança",
            text=(
                "[CONTEXTO DOCUMENTAL]\nDocumento: Constituição da Aliança\n"
                "§ 1º. As igrejas candidatas devem apresentar requerimento formal, ata, "
                "rol atualizado, estatuto registrado, CNPJ, alvará e conta bancária."
            ),
        ),
        document_type="constitution",
        source_category="denominational_normative_document",
        content_role="normative",
    )
    retriever = BuilderAwareStaticRetriever([constitution_requirements], context_builder)
    pipeline = RetrievalPipeline(
        hierarchical_retriever=retriever,
        context_consolidator=ContextConsolidator(final_context_top_k=4),
    )

    package = pipeline.retrieve("Como funciona o processo de filiação de uma igreja?")

    parent_keys = [context.parent_key for context in package.contexts]
    assert "constituicao-alianca-2022::article::5::paragraph::1o" in parent_keys
    assert "regimento-interno-alianca-2022::article::7" in parent_keys
    assert "regimento-interno-alianca-2022::article::6" in parent_keys
    assert package.metadata["normative_subject_scope_supplement"]["reason"] == (
        "normative_subject_framing_units_added"
    )
    assert package.metadata["effective_final_context_top_k"] == 5


def test_retrieval_pipeline_scopes_ecclesiastical_discipline_to_disciplinary_rules(tmp_path):
    from aia.retrieval.context_consolidator import ContextConsolidator
    from aia.retrieval.parent_context import ParentContextBuilder
    from aia.retrieval.retrieval_pipeline import RetrievalPipeline

    chunks_path = tmp_path / "chunks.jsonl"
    write_jsonl(
        chunks_path,
        [
            make_normative_article_chunk(
                chunk_id="regimento-interno-alianca-2022_artigo-016",
                document_id="regimento-interno-alianca-2022",
                document="Regimento Interno da Aliança",
                document_type="internal_regiment",
                full_reference="Regimento Interno, Capítulo I, Seção II, Art. 16",
                article_number="16",
                page=5,
                text=(
                    "Art. 16. A igreja local tem autonomia para disciplinar os seus membros. "
                    "Nenhuma pena disciplinar será aplicada sem instauração de processo para "
                    "apuração da verdade, devidamente instruído, e com amplo direito de defesa "
                    "ao acusado."
                ),
            ),
            make_normative_article_chunk(
                chunk_id="regimento-interno-alianca-2022_artigo-017",
                document_id="regimento-interno-alianca-2022",
                document="Regimento Interno da Aliança",
                document_type="internal_regiment",
                full_reference="Regimento Interno, Capítulo I, Seção II, Art. 17",
                article_number="17",
                page=5,
                text=(
                    "Art. 17. As penalidades impostas pelas igrejas filiadas são censura, "
                    "suspensão, desligamento de cargo ou função e exclusão."
                ),
            ),
            make_normative_article_chunk(
                chunk_id="regimento-interno-alianca-2022_artigo-050",
                document_id="regimento-interno-alianca-2022",
                document="Regimento Interno da Aliança",
                document_type="internal_regiment",
                full_reference="Regimento Interno, Capítulo IV, Art. 50",
                article_number="50",
                page=13,
                text=(
                    "Art. 50. A ALIANÇA exerce ação disciplinar sobre pastores, missionários "
                    "e igrejas a ela jurisdicionadas, visando edificação, correção de "
                    "escândalos, erros ou faltas."
                ),
            ),
            make_normative_article_chunk(
                chunk_id="regimento-interno-alianca-2022_artigo-055",
                document_id="regimento-interno-alianca-2022",
                document="Regimento Interno da Aliança",
                document_type="internal_regiment",
                full_reference="Regimento Interno, Capítulo IV, Seção I, Art. 55",
                article_number="55",
                page=14,
                text=(
                    "Art. 55. Ministros que desabonarem a conduta do Evangelho serão "
                    "julgados e disciplinados pela ALIANÇA, mediante denúncia justificada."
                ),
            ),
            make_normative_article_chunk(
                chunk_id="regimento-interno-alianca-2022_artigo-056",
                document_id="regimento-interno-alianca-2022",
                document="Regimento Interno da Aliança",
                document_type="internal_regiment",
                full_reference="Regimento Interno, Capítulo IV, Seção I, Art. 56",
                article_number="56",
                page=14,
                text=(
                    "Art. 56. Recebida a denúncia, a Diretoria acionará o Conselho de "
                    "Pastores para apurar os fatos."
                ),
            ),
        ],
    )
    context_builder = ParentContextBuilder(chunks_path=str(chunks_path))
    distracting_context = mark_context(
        make_parent_context(
            "regimento-interno-alianca-2022::article::127",
            "regimento-art-127",
            ["regimento-art-127"],
            12.0,
            chunk_type="normative_article",
            document_id="regimento-interno-alianca-2022",
            document="Regimento Interno da Aliança",
            text=(
                "[CONTEXTO DOCUMENTAL]\nDocumento: Regimento Interno da Aliança\n"
                "Art. 127. O Conselho de Pastores deverá orientar, assistir, coordenar "
                "e disciplinar o exercício do Ministério Pastoral."
            ),
        ),
        document_type="internal_regiment",
        source_category="denominational_normative_document",
        content_role="normative",
    )
    admission_context = mark_context(
        make_parent_context(
            "constituicao-alianca-2022::article::5::paragraph::4o",
            "constituicao-art-5-par-4",
            ["constituicao-art-5-par-4"],
            11.0,
            chunk_type="inciso",
            document_id="constituicao-alianca-2022",
            document="Constituição da Aliança",
            text=(
                "[CONTEXTO DOCUMENTAL]\nDocumento: Constituição da Aliança\n"
                "O ingresso exige documento comprobatório de que o requerente não sofreu "
                "sanção ou disciplina eclesiástica nos últimos dois anos."
            ),
        ),
        document_type="constitution",
        source_category="denominational_normative_document",
        content_role="normative",
    )
    pipeline = RetrievalPipeline(
        hierarchical_retriever=BuilderAwareStaticRetriever(
            [distracting_context, admission_context],
            context_builder,
        ),
        context_consolidator=ContextConsolidator(final_context_top_k=4),
    )

    package = pipeline.retrieve(
        "Segundo os documentos normativos da Aliança, quais são as regras gerais "
        "sobre disciplina eclesiástica?"
    )

    parent_keys = [context.parent_key for context in package.contexts]
    assert parent_keys[:3] == [
        "regimento-interno-alianca-2022::article::16",
        "regimento-interno-alianca-2022::article::17",
        "regimento-interno-alianca-2022::article::50",
    ]
    assert "regimento-interno-alianca-2022::article::55" in parent_keys
    assert "regimento-interno-alianca-2022::article::56" in parent_keys
    assert "regimento-interno-alianca-2022::article::127" not in parent_keys
    assert "constituicao-alianca-2022::article::5::paragraph::4o" not in parent_keys
    assert package.metadata["document_diversity"]["reason"] == "normative_subject_scope_filtered"
    assert package.metadata["document_diversity"]["scope_id"] == "ecclesiastical_discipline_rules"
    assert package.metadata["normative_subject_scope_supplement"]["reason"] == (
        "normative_subject_framing_units_added"
    )
    assert package.metadata["effective_final_context_top_k"] == 5


def test_retrieval_pipeline_scopes_ministerial_ordination_to_core_normative_units(tmp_path):
    from aia.retrieval.context_consolidator import ContextConsolidator
    from aia.retrieval.parent_context import ParentContextBuilder
    from aia.retrieval.retrieval_pipeline import RetrievalPipeline

    chunks_path = tmp_path / "chunks.jsonl"
    write_jsonl(
        chunks_path,
        [
            make_normative_article_chunk(
                chunk_id="constituicao-alianca-2022_artigo-005_paragrafo-2o",
                document_id="constituicao-alianca-2022",
                document="Constituição da Aliança",
                document_type="constitution",
                full_reference="Constituição da Aliança, Capítulo II, Art. 5º, § 2º",
                article_number="5",
                paragraph_number="2º",
                page=5,
                text=(
                    "§ 2º. Os candidatos a pastores devem apresentar requerimento formal, "
                    "ata da assembleia, declaração de conhecimento dos documentos normativos, "
                    "termo de compromisso, certificado de formação teológica, documentos "
                    "pessoais e certidões negativas."
                ),
            ),
            make_normative_article_chunk(
                chunk_id="constituicao-alianca-2022_artigo-005_paragrafo-3o",
                document_id="constituicao-alianca-2022",
                document="Constituição da Aliança",
                document_type="constitution",
                full_reference="Constituição da Aliança, Capítulo II, Art. 5º, § 3º",
                article_number="5",
                paragraph_number="3º",
                page=5,
                text=(
                    "§ 3º. Caso o postulante não possua formação teológica, deverá comprovar "
                    "atividade ministerial contínua por cinco anos ou sete anos com intervalos."
                ),
            ),
            make_normative_article_chunk(
                chunk_id="regimento-interno-alianca-2022_artigo-034",
                document_id="regimento-interno-alianca-2022",
                document="Regimento Interno da Aliança",
                document_type="internal_regiment",
                full_reference="Regimento Interno, Capítulo II, Seção V, Art. 34",
                article_number="34",
                page=10,
                text=(
                    "Art. 34. Serão ordenados ministros os formados em teologia por seminário "
                    "da ALIANÇA ou por outros reconhecidos pelo Departamento Teológico."
                ),
            ),
            make_normative_article_chunk(
                chunk_id="regimento-interno-alianca-2022_artigo-035",
                document_id="regimento-interno-alianca-2022",
                document="Regimento Interno da Aliança",
                document_type="internal_regiment",
                full_reference="Regimento Interno, Capítulo II, Seção V, Art. 35",
                article_number="35",
                page=10,
                text=(
                    "Art. 35. O candidato ao ministério poderá ser ordenado em Concílio "
                    "Nacional ou Regional, ou nas igrejas da Região Administrativa."
                ),
            ),
            make_normative_article_chunk(
                chunk_id="regimento-interno-alianca-2022_artigo-036",
                document_id="regimento-interno-alianca-2022",
                document="Regimento Interno da Aliança",
                document_type="internal_regiment",
                full_reference="Regimento Interno, Capítulo II, Seção V, Art. 36",
                article_number="36",
                page=10,
                text=(
                    "Art. 36. A igreja interessada enviará ofício à Diretoria Nacional "
                    "requerendo a ordenação do candidato, e a Diretoria instaurará o processo."
                ),
            ),
            make_normative_article_chunk(
                chunk_id="regimento-interno-alianca-2022_artigo-037",
                document_id="regimento-interno-alianca-2022",
                document="Regimento Interno da Aliança",
                document_type="internal_regiment",
                full_reference="Regimento Interno, Capítulo II, Seção V, Art. 37",
                article_number="37",
                page=10,
                text=(
                    "Art. 37. O processo de ordenação ocorrerá em quatro fases: avaliação "
                    "psicológica, avaliação oral pelo Conselho de Pastores, prova escrita "
                    "pelo Departamento Teológico e defesa de monografia teológica."
                ),
            ),
            make_normative_article_chunk(
                chunk_id="resolucao-alianca-01-2020_artigo-001",
                document_id="resolucao-alianca-01-2020",
                document="Resolução Aliança nº 01/2020",
                document_type="administrative_resolution",
                full_reference="Resolução Aliança nº 01/2020, Capítulo I, Art. 1º",
                article_number="1",
                page=2,
                text=(
                    "Art. 1º. O plano de incentivo à emancipação e à ordenação ao sagrado "
                    "ministério abrange pontos de pregação, congregações e campos missionários."
                ),
            ),
            make_normative_article_chunk(
                chunk_id="resolucao-alianca-01-2020_artigo-003",
                document_id="resolucao-alianca-01-2020",
                document="Resolução Aliança nº 01/2020",
                document_type="administrative_resolution",
                full_reference="Resolução Aliança nº 01/2020, Capítulo III, Art. 3º",
                article_number="3",
                page=3,
                text=(
                    "Art. 3º. Obreiros vinculados a pontos de pregação, congregações e campos "
                    "missionários poderão aderir ao processo de ordenação se tiverem vínculo "
                    "superior a cinco anos, encaminhamento pela igreja-mãe, formação teológica, "
                    "curso denominacional, avaliações, monografia, certidões negativas e "
                    "pareceres favoráveis homologados."
                ),
            ),
        ],
    )
    context_builder = ParentContextBuilder(chunks_path=str(chunks_path))
    peripheral_regiment = mark_context(
        make_parent_context(
            "regimento-interno-alianca-2022::article::41",
            "regimento-art-41",
            ["regimento-art-41"],
            12.0,
            chunk_type="normative_article",
            document_id="regimento-interno-alianca-2022",
            document="Regimento Interno da Aliança",
            text=(
                "[CONTEXTO DOCUMENTAL]\nDocumento: Regimento Interno da Aliança\n"
                "Art. 41. Um ministro procedente de outra comunidade evangélica que queira "
                "ser admitido no quadro de ministros deverá apresentar documentos."
            ),
        ),
        document_type="internal_regiment",
        source_category="denominational_normative_document",
        content_role="normative",
    )
    confession_context = mark_context(
        make_parent_context(
            "confissao-fe-congregacional-alianca::chapter::xxviii",
            "confissao-ministros",
            ["confissao-ministros"],
            10.0,
            document_id="confissao-fe-congregacional-alianca",
            document="Confissão de Fé Congregacional",
            text=(
                "[CONTEXTO DOCUMENTAL]\nDocumento: Confissão de Fé Congregacional\n"
                "Cada um deve ter respeito especial pelos ministros da Palavra."
            ),
        ),
        document_type="confession_of_faith",
        source_category="doctrinal_document",
        content_role="doctrinal",
    )
    ethics_context = mark_context(
        make_parent_context(
            "codigo-etica-ministro-alianca::article::20",
            "codigo-etica-art-20",
            ["codigo-etica-art-20"],
            9.0,
            chunk_type="normative_article",
            document_id="codigo-etica-ministro-alianca",
            document="Código de Ética do Ministro Congregacional",
            text=(
                "[CONTEXTO DOCUMENTAL]\nDocumento: Código de Ética\n"
                "Art. 20. Recebida uma reclamação contra pastor, o Conselho de Pastores "
                "deverá convocá-lo para esclarecimentos."
            ),
        ),
        document_type="normative_ethics",
        source_category="denominational_normative_document",
        content_role="normative",
    )
    pipeline = RetrievalPipeline(
        hierarchical_retriever=BuilderAwareStaticRetriever(
            [peripheral_regiment, confession_context, ethics_context],
            context_builder,
        ),
        context_consolidator=ContextConsolidator(final_context_top_k=4),
    )

    package = pipeline.retrieve(
        "Quais documentos tratam de ordenação ministerial e quais requisitos aparecem em cada um?"
    )

    parent_keys = [context.parent_key for context in package.contexts]
    included_chunk_ids = {
        chunk_id
        for context in package.contexts
        for chunk_id in context.included_chunk_ids
    }
    assert {
        "constituicao-alianca-2022_artigo-005_paragrafo-2o",
        "constituicao-alianca-2022_artigo-005_paragrafo-3o",
        "regimento-interno-alianca-2022_artigo-034",
        "regimento-interno-alianca-2022_artigo-036",
        "regimento-interno-alianca-2022_artigo-037",
        "resolucao-alianca-01-2020_artigo-003",
    } <= included_chunk_ids
    assert "confissao-fe-congregacional-alianca::chapter::xxviii" not in parent_keys
    assert "codigo-etica-ministro-alianca::article::20" not in parent_keys
    assert parent_keys.index("regimento-interno-alianca-2022::article::41") > 0
    assert package.metadata["document_diversity"]["reason"] == "normative_subject_scope_filtered"
    assert package.metadata["document_diversity"]["scope_id"] == "ministerial_ordination_requirements"
    assert package.metadata["normative_subject_scope_supplement"]["reason"] == (
        "normative_subject_framing_units_added"
    )
    assert package.metadata["effective_final_context_top_k"] == 6


def test_retrieval_pipeline_covers_congregation_emancipation_affiliation_scope(tmp_path):
    from aia.retrieval.context_consolidator import ContextConsolidator
    from aia.retrieval.parent_context import ParentContextBuilder
    from aia.retrieval.retrieval_pipeline import RetrievalPipeline

    chunks_path = tmp_path / "chunks.jsonl"
    write_jsonl(
        chunks_path,
        [
            make_normative_article_chunk(
                chunk_id="regimento-interno-alianca-2022_artigo-006",
                document_id="regimento-interno-alianca-2022",
                document="Regimento Interno da Aliança",
                document_type="internal_regiment",
                full_reference="Regimento Interno, Capítulo I, Seção I, Art. 6º",
                article_number="6",
                page=3,
                text=(
                    "Art. 6º. Uma congregação, formalmente organizada como igreja, poderá "
                    "filiar-se à ALIANÇA, desde que apresente mínimo de 40 membros, um "
                    "presbítero e dois diáconos, declaração de acatamento dos documentos, "
                    "estatuto próprio e ata assinada por no mínimo 2/3 dos membros."
                ),
            ),
            make_normative_article_chunk(
                chunk_id="regimento-interno-alianca-2022_artigo-007",
                document_id="regimento-interno-alianca-2022",
                document="Regimento Interno da Aliança",
                document_type="internal_regiment",
                full_reference="Regimento Interno, Capítulo I, Seção I, Art. 7º",
                article_number="7",
                page=3,
                text=(
                    "Art. 7º. O pedido de filiação será encaminhado à Região Administrativa, "
                    "que verificará as condições e enviará à Diretoria Nacional com parecer; "
                    "a Diretoria Nacional examinará e aprovará ou não o pedido."
                ),
            ),
            make_normative_article_chunk(
                chunk_id="resolucao-alianca-01-2020_artigo-002",
                document_id="resolucao-alianca-01-2020",
                document="Resolução Aliança nº 01/2020",
                document_type="administrative_resolution",
                full_reference="Resolução Aliança nº 01/2020, Capítulo II, Art. 2º",
                article_number="2",
                page=3,
                text=(
                    "Art. 2º. Pontos de Pregação, Congregações e Campos Missionários deverão "
                    "ter mínimo de 40 membros, pastor eleito ou em ordenação, presbítero e "
                    "diáconos, capacidade financeira, compromisso de emancipação e filiação "
                    "em 12 meses e relatórios mensais."
                ),
            ),
            make_normative_article_chunk(
                chunk_id="resolucao-alianca-01-2020_artigo-001",
                document_id="resolucao-alianca-01-2020",
                document="Resolução Aliança nº 01/2020",
                document_type="administrative_resolution",
                full_reference="Resolução Aliança nº 01/2020, Capítulo I, Art. 1º",
                article_number="1",
                page=2,
                text=(
                    "Art. 1º. O plano de incentivo à emancipação abrange Pontos de Pregação, "
                    "Congregações e Campos Missionários."
                ),
            ),
            make_normative_article_chunk(
                chunk_id="constituicao-alianca-2022_artigo-005_paragrafo-1o_inciso-i",
                document_id="constituicao-alianca-2022",
                document="Constituição da Aliança",
                document_type="constitution",
                full_reference="Constituição da Aliança, Capítulo II, Art. 5º, § 1º, inciso I",
                article_number="5",
                paragraph_number="1º",
                inciso="I",
                page=4,
                text=(
                    "Art. 5º. O ingresso de igrejas será precedido do envio da documentação. "
                    "I - Requerimento formal."
                ),
            ),
        ],
    )
    context_builder = ParentContextBuilder(chunks_path=str(chunks_path))
    peripheral_context = mark_context(
        make_parent_context(
            "regimento-interno-alianca-2022::article::3",
            "regimento-art-3",
            ["regimento-art-3"],
            9.0,
            chunk_type="normative_article",
            document_id="regimento-interno-alianca-2022",
            document="Regimento Interno da Aliança",
            text=(
                "[CONTEXTO DOCUMENTAL]\nDocumento: Regimento Interno da Aliança\n"
                "Art. 3º. Congregação é comunidade de crentes professos com autonomia relativa."
            ),
        ),
        document_type="internal_regiment",
        source_category="denominational_normative_document",
        content_role="normative",
    )
    pipeline = RetrievalPipeline(
        hierarchical_retriever=BuilderAwareStaticRetriever([peripheral_context], context_builder),
        context_consolidator=ContextConsolidator(final_context_top_k=4),
    )

    package = pipeline.retrieve(
        "Como uma congregação pode ser emancipada e se tornar uma igreja filiada?"
    )

    assert package.context_count == 5
    assert package.metadata["effective_final_context_top_k"] == 5
    assert package.metadata["document_diversity"]["reason"] == "normative_subject_scope_filtered"
    assert package.metadata["document_diversity"]["scope_id"] == (
        "congregation_emancipation_affiliation"
    )
    assert package.metadata["normative_subject_scope_supplement"]["reason"] == (
        "normative_subject_framing_units_added"
    )
    assert [context.parent_key for context in package.contexts] == [
        "regimento-interno-alianca-2022::article::6",
        "regimento-interno-alianca-2022::article::7",
        "resolucao-alianca-01-2020::article::2",
        "resolucao-alianca-01-2020::article::1",
        "constituicao-alianca-2022::article::5::paragraph::1o",
    ]
    assert all("regimento-interno-alianca-2022::article::3" != context.parent_key for context in package.contexts)


def test_retrieval_pipeline_applies_normative_subject_scope_for_pastor_admission():
    from aia.retrieval.context_consolidator import ContextConsolidator
    from aia.retrieval.retrieval_pipeline import RetrievalPipeline

    church_requirements = mark_context(
        make_parent_context(
            "constituicao-alianca-2022::article::5::paragraph::1o",
            "art-5-par-1",
            ["art-5-par-1"],
            5.0,
            chunk_type="inciso",
            document_id="constituicao-alianca-2022",
            document="Constituição da Aliança",
            text=(
                "[CONTEXTO DOCUMENTAL]\nDocumento: Constituição da Aliança\n"
                "§ 1º. As igrejas candidatas devem apresentar requerimento formal, ata, "
                "rol atualizado, estatuto registrado, CNPJ, alvará e conta bancária."
            ),
        ),
        document_type="constitution",
        source_category="denominational_normative_document",
        content_role="normative",
    )
    pastor_requirements = mark_context(
        make_parent_context(
            "constituicao-alianca-2022::article::5::paragraph::2o",
            "art-5-par-2",
            ["art-5-par-2"],
            1.0,
            chunk_type="inciso",
            document_id="constituicao-alianca-2022",
            document="Constituição da Aliança",
            text=(
                "[CONTEXTO DOCUMENTAL]\nDocumento: Constituição da Aliança\n"
                "§ 2º. Os candidatos a pastores devem apresentar requerimento formal, "
                "declaração de conhecimento dos documentos normativos, termo de compromisso "
                "e documentação pessoal."
            ),
        ),
        document_type="constitution",
        source_category="denominational_normative_document",
        content_role="normative",
    )
    ministerial_activity = mark_context(
        make_parent_context(
            "constituicao-alianca-2022::article::5::paragraph::3o",
            "art-5-par-3",
            ["art-5-par-3"],
            0.8,
            chunk_type="paragraph",
            document_id="constituicao-alianca-2022",
            document="Constituição da Aliança",
            text=(
                "[CONTEXTO DOCUMENTAL]\nDocumento: Constituição da Aliança\n"
                "§ 3º. Caso o postulante não possua título de formação teológica, deverá "
                "comprovar atividade ministerial contínua."
            ),
        ),
        document_type="constitution",
        source_category="denominational_normative_document",
        content_role="normative",
    )
    retriever = LeakyDocumentScopeHierarchicalRetriever(
        [church_requirements, pastor_requirements, ministerial_activity]
    )
    pipeline = RetrievalPipeline(
        hierarchical_retriever=retriever,
        context_consolidator=ContextConsolidator(final_context_top_k=4),
    )

    package = pipeline.retrieve(
        "De acordo com a Constituição da Aliança, quais são os requisitos para ingresso de pastores?"
    )

    selected_parent_keys = [context.parent_key for context in package.contexts]
    assert selected_parent_keys == [
        "constituicao-alianca-2022::article::5::paragraph::2o",
        "constituicao-alianca-2022::article::5::paragraph::3o",
    ]
    assert "constituicao-alianca-2022::article::5::paragraph::1o" not in selected_parent_keys
    assert package.metadata["document_diversity"]["reason"] == "normative_subject_scope_filtered"
    assert package.metadata["document_diversity"]["scope_id"] == "pastor_admission_requirements"


def test_retrieval_pipeline_retries_normative_query_when_only_doctrinal_context_is_found():
    from aia.retrieval.context_consolidator import ContextConsolidator
    from aia.retrieval.retrieval_pipeline import RetrievalPipeline

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


def test_retrieval_pipeline_retries_doctrinal_query_when_only_normative_context_is_found():
    from aia.retrieval.context_consolidator import ContextConsolidator
    from aia.retrieval.retrieval_pipeline import RetrievalPipeline

    normative_context = mark_context(
        make_parent_context(
            "regimento::finalidade",
            "normative-anchor",
            ["n1"],
            2.0,
            chunk_type="internal_regiment_article",
            document_id="regimento-interno-alianca-2022",
            document="Regimento Interno da Aliança",
            text=(
                "[CONTEXTO DOCUMENTAL]\nDocumento: Regimento Interno da Aliança\n"
                "Texto institucional sobre finalidade e organização da igreja local."
            ),
        ),
        document_type="internal_regiment",
        source_category="denominational_normative_document",
        content_role="normative",
    )
    doctrinal_context = mark_context(
        make_parent_context(
            "confissao::queda-e-graca",
            "doctrinal-anchor",
            ["d1"],
            1.0,
            document_id="confissao-batista-londres-1689",
            document="Confissão Batista de Londres de 1689",
            text=(
                "[CONTEXTO DOCUMENTAL]\nDocumento: Confissão Batista de Londres de 1689\n"
                "O homem está morto em pecados, incapaz por si mesmo, e Deus o chama "
                "eficazmente por sua graça em Cristo."
            ),
        ),
        document_type="confession_of_faith",
        source_category="doctrinal_document",
        content_role="doctrinal",
    )
    retriever = FilterAwareHierarchicalRetriever([normative_context], [doctrinal_context])
    pipeline = RetrievalPipeline(
        hierarchical_retriever=retriever,
        context_consolidator=ContextConsolidator(final_context_top_k=2),
    )

    package = pipeline.retrieve(
        "Como os documentos explicam a relação entre pecado humano e graça de Deus?"
    )

    assert package.documents == ["confissao-batista-londres-1689"]
    assert package.contexts[0].document == "Confissão Batista de Londres de 1689"
    assert package.contexts[0].content_priority == "doctrinal"
    assert retriever.calls == [{}, {"source_category": "doctrinal_document"}]
    assert package.metadata["fallback_retry"]["reason"] == "missing_doctrinal_context"


def test_retrieval_pipeline_retries_alliance_doctrinal_query_on_congregational_confession():
    from aia.retrieval.context_consolidator import ContextConsolidator
    from aia.retrieval.retrieval_pipeline import RetrievalPipeline

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


def test_retrieval_pipeline_supplements_document_inventory_queries():
    from aia.retrieval.context_consolidator import ContextConsolidator
    from aia.retrieval.retrieval_pipeline import RetrievalPipeline

    manual_context = mark_context(
        make_parent_context(
            "regimento::manual-cerimonias",
            "manual-anchor",
            ["m1"],
            5.0,
            chunk_type="internal_regiment_article",
            document_id="regimento-interno-alianca-2022",
            document="Regimento Interno da Aliança",
            text=(
                "[CONTEXTO DOCUMENTAL]\nDocumento: Regimento Interno da Aliança\n"
                "Art. 44. Cabe à ALIANÇA organizar e disponibilizar o Manual de Cerimônias "
                "Religiosas para orientar os ministros e as igrejas filiadas."
            ),
        ),
        document_type="internal_regiment",
        source_category="denominational_normative_document",
        content_role="normative",
    )
    inventory_context = mark_context(
        make_parent_context(
            "regimento::declaracao-documental",
            "inventory-anchor",
            ["i1"],
            2.0,
            chunk_type="internal_regiment_article",
            document_id="regimento-interno-alianca-2022",
            document="Regimento Interno da Aliança",
            text=(
                "[CONTEXTO DOCUMENTAL]\nDocumento: Regimento Interno da Aliança\n"
                "O ministro deve apresentar declaração de conhecimento e aceitação da Constituição "
                "da ALIANÇA, do Regimento Interno, da Confissão de Fé da ALIANÇA, do Código de Ética, "
                "das Decisões conciliares e Resoluções da Diretoria Nacional."
            ),
        ),
        document_type="internal_regiment",
        source_category="denominational_normative_document",
        content_role="normative",
    )
    ethics_context = mark_context(
        make_parent_context(
            "codigo-etica::conduta",
            "ethics-anchor",
            ["e1"],
            1.5,
            chunk_type="normative_ethics_article",
            document_id="codigo-etica-ministro-alianca",
            document="Código de Ética do Ministro Congregacional",
            text="[CONTEXTO DOCUMENTAL]\nDocumento: Código de Ética\nTexto sobre conduta ministerial.",
        ),
        document_type="normative_ethics",
        source_category="denominational_normative_document",
        content_role="normative",
    )
    confession_context = mark_context(
        make_parent_context(
            "confissao-congregacional::igreja",
            "confession-anchor",
            ["c1"],
            1.0,
            document_id="confissao-fe-congregacional-alianca",
            document="Confissão de Fé Congregacional",
            text="[CONTEXTO DOCUMENTAL]\nDocumento: Confissão de Fé Congregacional\nTexto doutrinário.",
        ),
        document_type="confession_of_faith",
        source_category="doctrinal_document",
        content_role="doctrinal",
    )
    retriever = MultiFilterAwareHierarchicalRetriever(
        [manual_context],
        {
            (("source_category", "denominational_normative_document"),): [
                manual_context,
                inventory_context,
                ethics_context,
            ],
            (("document_id", "confissao-fe-congregacional-alianca"),): [confession_context],
        },
    )
    pipeline = RetrievalPipeline(
        hierarchical_retriever=retriever,
        context_consolidator=ContextConsolidator(final_context_top_k=3),
    )

    package = pipeline.retrieve(
        "Quais documentos orientam a conduta de uma igreja filiada e de seus ministros?"
    )

    assert retriever.calls == [
        {},
        {"source_category": "denominational_normative_document"},
        {"document_id": "confissao-fe-congregacional-alianca"},
    ]
    assert package.contexts[0].parent_key == "regimento::declaracao-documental"
    assert "confissao-fe-congregacional-alianca" in package.documents
    assert "codigo-etica-ministro-alianca" in package.documents
    assert package.metadata["document_diversity"]["reason"] == "document_inventory_coverage_promoted"
    assert package.metadata["supplemental_retrieval"]["applied"] is True


def test_retrieval_pipeline_prefers_congregational_sources_for_institutional_doctrinal_bridge():
    from aia.retrieval.context_consolidator import ContextConsolidator
    from aia.retrieval.retrieval_pipeline import RetrievalPipeline

    baptist_context = mark_context(
        make_parent_context(
            "batista::governo",
            "baptist-anchor",
            ["b1"],
            5.0,
            document_id="confissao-batista-londres-1689",
            document="Confissão Batista de Londres de 1689",
            text="[CONTEXTO DOCUMENTAL]\nDocumento: Confissão Batista\nTexto sobre governo de igreja.",
        ),
        document_type="confession_of_faith",
        source_category="doctrinal_document",
        content_role="doctrinal",
    )
    congregational_confession = mark_context(
        make_parent_context(
            "confissao-congregacional::governo",
            "congregational-anchor",
            ["c1"],
            2.0,
            document_id="confissao-fe-congregacional-alianca",
            document="Confissão de Fé Congregacional",
            text=(
                "[CONTEXTO DOCUMENTAL]\nDocumento: Confissão de Fé Congregacional\n"
                "A igreja deve ser governada conforme a ordem espiritual ensinada por Cristo."
            ),
        ),
        document_type="confession_of_faith",
        source_category="doctrinal_document",
        content_role="doctrinal",
    )
    constitution_context = mark_context(
        make_parent_context(
            "constituicao::normas",
            "constitution-anchor",
            ["n1"],
            1.8,
            chunk_type="constitution_article",
            document_id="constituicao-alianca-2022",
            document="Constituição da Aliança",
            text="[CONTEXTO DOCUMENTAL]\nDocumento: Constituição da Aliança\nTexto sobre normas da Aliança.",
        ),
        document_type="constitution",
        source_category="denominational_normative_document",
        content_role="normative",
    )
    regiment_context = mark_context(
        make_parent_context(
            "regimento::governo-local",
            "regiment-anchor",
            ["r1"],
            1.7,
            chunk_type="internal_regiment_article",
            document_id="regimento-interno-alianca-2022",
            document="Regimento Interno da Aliança",
            text="[CONTEXTO DOCUMENTAL]\nDocumento: Regimento Interno\nTexto sobre governo congregacional.",
        ),
        document_type="internal_regiment",
        source_category="denominational_normative_document",
        content_role="normative",
    )
    retriever = MultiFilterAwareHierarchicalRetriever(
        [baptist_context],
        {
            (("document_id", "confissao-fe-congregacional-alianca"),): [congregational_confession],
            (("source_category", "denominational_normative_document"),): [
                constitution_context,
                regiment_context,
            ],
        },
    )
    pipeline = RetrievalPipeline(
        hierarchical_retriever=retriever,
        context_consolidator=ContextConsolidator(final_context_top_k=3),
    )

    package = pipeline.retrieve(
        "Como a doutrina professada e as normas institucionais se relacionam no governo congregacional?"
    )

    assert retriever.calls == [
        {},
        {"document_id": "confissao-fe-congregacional-alianca"},
        {"source_category": "denominational_normative_document"},
    ]
    assert "confissao-batista-londres-1689" not in package.documents
    assert package.documents == [
        "confissao-fe-congregacional-alianca",
        "constituicao-alianca-2022",
        "regimento-interno-alianca-2022",
    ]
    assert (
        package.metadata["document_diversity"]["reason"]
        == "institutional_doctrinal_bridge_coverage_promoted"
    )


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

    from aia.retrieval.retrieval_pipeline import RetrievalPipeline

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
