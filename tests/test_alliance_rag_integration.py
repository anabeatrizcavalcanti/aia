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

ALLIANCE_CHUNKS = Path("corpus/processed/chunks/alliance/all_chunks_for_embeddings.jsonl")
ALLIANCE_EMBEDDINGS = Path("corpus/processed/embeddings/alliance/openai_embeddings.jsonl")
ALLIANCE_CHROMA_DIR = Path("corpus/indexes/chroma/alliance")
ALLIANCE_COLLECTION = "aia_alliance_v1"
EXPECTED_NORMATIVE_DOCS = {
    "confissao-fe-congregacional-alianca",
    "constituicao-alianca-2022",
    "regimento-interno-alianca-2022",
    "codigo-etica-ministro-alianca",
    "resolucao-alianca-01-2020",
}


def read_jsonl(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def load_dotenv_if_available() -> None:
    if importlib.util.find_spec("dotenv") is None:
        return
    from dotenv import load_dotenv

    load_dotenv()


def test_alliance_chunks_preserve_required_normative_metadata():
    rows = read_jsonl(ALLIANCE_CHUNKS)
    by_doc = {row["document_id"] for row in rows}
    chunk_ids = [row["chunk_id"] for row in rows]

    assert EXPECTED_NORMATIVE_DOCS.issubset(by_doc)
    assert len(chunk_ids) == len(set(chunk_ids))
    for row in rows:
        assert row.get("doc_id")
        assert row.get("document_title")
        assert "document_type" in row
        assert "source_category" in row
        assert "full_reference" in row
        assert "document_structure_type" in row
        assert "biblical_references" in row


def test_alliance_embeddings_do_not_duplicate_chunks():
    rows = read_jsonl(ALLIANCE_EMBEDDINGS)
    chunk_ids = [row["chunk_id"] for row in rows]

    assert len(chunk_ids) == len(set(chunk_ids))
    assert EXPECTED_NORMATIVE_DOCS.issubset({row["document_id"] for row in rows})


def test_chroma_collection_contains_new_document_ids_when_available():
    if importlib.util.find_spec("chromadb") is None:
        pytest.skip("chromadb não está instalado neste ambiente.")

    import chromadb

    client = chromadb.PersistentClient(path=str(ALLIANCE_CHROMA_DIR))
    collection = client.get_collection(ALLIANCE_COLLECTION)

    for document_id in EXPECTED_NORMATIVE_DOCS:
        result = collection.get(where={"document_id": document_id}, limit=1)
        assert result["ids"], f"{document_id} não apareceu no ChromaDB"


def test_citation_formatter_prefers_full_reference():
    from aia.generation.citation_formatter import citations_from_source_map, format_citations
    from aia.retrieval.final_context import RetrievalContextPackage

    package = RetrievalContextPackage(
        query="Quais critérios existem para emancipação de campos missionários?",
        contexts=[],
        context_count=0,
        total_context_chars=0,
        documents=["resolucao-alianca-01-2020"],
        source_map={
            "source_1": {
                "document": "Resolução Aliança nº 01/2020",
                "document_id": "resolucao-alianca-01-2020",
                "document_type": "administrative_resolution",
                "source_category": "denominational_normative_document",
                "parent_title": "Capítulo II",
                "full_reference": "Resolução Aliança nº 01/2020, Capítulo II, Art. 2º",
                "pages": "3",
                "anchor_chunk_ids": ["resolucao-alianca-01-2020_artigo-002"],
                "included_chunk_ids": ["resolucao-alianca-01-2020_artigo-002"],
                "source_paths": ["corpus/raw/normative/Resolução_aliança.pdf"],
                "content_priority": "normative",
            }
        },
        retrieval_stages=[],
        filters={},
    )

    citations = citations_from_source_map(package)
    formatted = format_citations(citations)[0]

    assert citations[0].full_reference == "Resolução Aliança nº 01/2020, Capítulo II, Art. 2º"
    assert "Resolução Aliança nº 01/2020, Capítulo II, Art. 2º" in formatted
    assert "fonte normativa" in formatted


def test_evidence_policy_distinguishes_normative_and_doctrinal_questions():
    from aia.generation.evidence_policy import EvidencePolicy
    from aia.retrieval.final_context import FinalContext, RetrievalContextPackage

    doctrinal_context = FinalContext(
        query="Como uma igreja se filia à Aliança?",
        rank=1,
        parent_key="confissao::capitulo",
        parent_title="Confissão",
        document_id="confissao-fe-congregacional-alianca",
        document="Confissão de Fé Congregacional",
        context_text=("A igreja e a Aliança aparecem aqui, mas este trecho trata de ensino doutrinário, não de filiação institucional. " * 12),
        context_char_count=980,
        included_chunk_ids=["a"],
        anchor_chunk_ids=["a"],
        anchor_scores=[1.0],
        page_start=1,
        page_end=1,
        source_paths=[],
        context_status="expanded",
        content_priority="doctrinal",
        metadata={},
    )
    normative_context = FinalContext(
        query="Como uma igreja se filia à Aliança?",
        rank=1,
        parent_key="constituicao::artigo::5",
        parent_title="Constituição da Aliança, Art. 5º",
        document_id="constituicao-alianca-2022",
        document="Constituição da Aliança",
        context_text=("A igreja local deve apresentar documentos para filiação à Aliança. " * 20),
        context_char_count=1320,
        included_chunk_ids=["b"],
        anchor_chunk_ids=["b"],
        anchor_scores=[1.0],
        page_start=1,
        page_end=1,
        source_paths=[],
        context_status="expanded",
        content_priority="normative",
        metadata={},
    )

    def package(context):
        return RetrievalContextPackage(
            query="Como uma igreja se filia à Aliança?",
            contexts=[context],
            context_count=1,
            total_context_chars=context.context_char_count,
            documents=[context.document_id],
            source_map={"source_1": {"document": context.document, "document_id": context.document_id}},
            retrieval_stages=[],
            filters={},
        )

    policy = EvidencePolicy()

    assert policy.evaluate(package(doctrinal_context)).reason == "no_normative_context_for_normative_query"
    assert policy.evaluate(package(normative_context)).can_answer is True


def test_minimum_questions_retrieve_expected_documents_when_openai_available():
    load_dotenv_if_available()

    if importlib.util.find_spec("chromadb") is None:
        pytest.skip("chromadb não está instalado neste ambiente.")
    if not os.getenv("OPENAI_API_KEY", "").strip():
        pytest.skip("OPENAI_API_KEY não está configurada neste ambiente.")

    from aia.retrieval.vector_retriever import VectorRetriever

    expectations = [
        ("O que a Confissão de Fé Congregacional ensina sobre justificação?", {"confissao-fe-congregacional-alianca"}),
        ("Quais documentos uma igreja precisa apresentar para se filiar à Aliança?", {"constituicao-alianca-2022", "regimento-interno-alianca-2022"}),
        ("Quais são os deveres de uma igreja local?", {"constituicao-alianca-2022", "regimento-interno-alianca-2022"}),
        ("Como funciona o processo de ordenação de ministros?", {"regimento-interno-alianca-2022", "resolucao-alianca-01-2020"}),
        ("Quais são os deveres éticos do pastor em relação à Aliança?", {"codigo-etica-ministro-alianca"}),
        ("Quais os critérios para emancipação de campos missionários?", {"resolucao-alianca-01-2020"}),
    ]
    retriever = VectorRetriever()

    for question, expected_documents in expectations:
        results = retriever.retrieve(question, top_k=10)
        retrieved_documents = {result.document_id for result in results}
        assert retrieved_documents & expected_documents, question
