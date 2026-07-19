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
    Path("src/aia/retrieval/bm25_retriever.py"),
    Path("src/aia/retrieval/rrf.py"),
    Path("src/aia/retrieval/hybrid_retriever.py"),
    Path("scripts/pipeline/query_hybrid_retriever.py"),
]


def load_dotenv_if_available() -> None:
    if importlib.util.find_spec("dotenv") is None:
        return
    from dotenv import load_dotenv

    load_dotenv()


def make_result(chunk_id: str, source: str, score: float):
    from aia.retrieval.retrieval_result import RetrievalResult

    return RetrievalResult(
        chunk_id=chunk_id,
        document_id="canones-de-dort",
        document="Cânones de Dort",
        chunk_type="doctrinal_article",
        content_role="doctrinal",
        section_title="Artigo",
        section_reference="Artigo 1",
        chapter_title="A Eleição e a Reprovação Divinas",
        chapter_reference="Primeiro Capítulo da Doutrina",
        page_start=1,
        page_end=1,
        source_path="corpus/raw/reformed/Os-Canones-de-Dort.pdf",
        text_hash=f"hash-{chunk_id}",
        score=score,
        distance=score if source == "vector" else None,
        text=f"Texto do chunk {chunk_id}",
        metadata={
            "corpus_id": "reformed",
            "retrieval_namespace": "reformed_confessional",
            "retrieval_source": source,
        },
    )


def test_hybrid_retrieval_files_exist():
    for path in REQUIRED_FILES:
        assert path.exists()


def test_hybrid_retrieval_inputs_exist():
    assert Path("corpus/processed/chunks/alliance/all_chunks_for_embeddings.jsonl").exists()
    index_dir = Path("corpus/indexes/chroma/alliance")
    assert index_dir.exists()
    assert any(index_dir.iterdir())


def test_rank_bm25_is_declared_and_imported():
    requirements = Path("requirements.txt").read_text(encoding="utf-8")
    bm25_module = Path("src/aia/retrieval/bm25_retriever.py").read_text(encoding="utf-8")

    assert "rank-bm25" in requirements
    assert "from rank_bm25 import BM25Okapi" in bm25_module


def test_bm25_tokenizer_preserves_doctrinal_terms():
    from aia.retrieval.bm25_retriever import tokenize_for_bm25

    tokens = tokenize_for_bm25("Eleição, justificação, regeneração, expiação e batismo.")

    assert "eleição" in tokens
    assert "justificação" in tokens
    assert "regeneração" in tokens
    assert "expiação" in tokens
    assert "batismo" in tokens


def test_bm25_retriever_returns_results_when_dependency_is_available():
    if importlib.util.find_spec("rank_bm25") is None:
        pytest.skip("rank-bm25 não está instalado neste ambiente.")

    from aia.retrieval.bm25_retriever import BM25Retriever

    retriever = BM25Retriever()
    results = retriever.retrieve("batismo", top_k=5)

    assert retriever.chunks
    assert results
    for result in results:
        assert result.chunk_id
        assert result.source_path.startswith(("corpus/raw/reformed/", "corpus/raw/normative/"))
        assert result.metadata["retrieval_source"] == "bm25"
        assert "bm25_score" in result.metadata


def test_rrf_combines_rankings_without_duplicate_chunks():
    from aia.retrieval.rrf import reciprocal_rank_fusion

    vector_results = [
        make_result("chunk-a", "vector", 0.2),
        make_result("chunk-b", "vector", 0.4),
    ]
    bm25_results = [
        make_result("chunk-b", "bm25", 8.0),
        make_result("chunk-c", "bm25", 3.0),
    ]

    fused = reciprocal_rank_fusion([vector_results, bm25_results], k=60, top_k=3)

    assert len(fused) == 3
    assert len({result.chunk_id for result in fused}) == 3
    assert fused[0].chunk_id == "chunk-b"
    assert fused[0].score >= fused[1].score
    assert "rrf_score" in fused[0].metadata
    assert set(fused[0].metadata["retrieval_sources"]) == {"bm25", "vector"}


def test_hybrid_retriever_returns_results_when_dependencies_are_available():
    load_dotenv_if_available()

    if importlib.util.find_spec("rank_bm25") is None:
        pytest.skip("rank-bm25 não está instalado neste ambiente.")
    if importlib.util.find_spec("chromadb") is None:
        pytest.skip("chromadb não está instalado neste ambiente.")
    if not os.getenv("OPENAI_API_KEY", "").strip():
        pytest.skip("OPENAI_API_KEY não está configurada neste ambiente.")

    from aia.retrieval.hybrid_retriever import HybridRetriever

    retriever = HybridRetriever(vector_candidate_k=5, bm25_candidate_k=5, final_top_k=3)
    results = retriever.retrieve("O que é o batismo?", top_k=3)

    assert results
    for result in results:
        assert result.chunk_id
        assert result.document_id
        assert result.document
        assert result.chunk_type
        assert result.source_path.startswith(("corpus/raw/reformed/", "corpus/raw/normative/"))
        assert result.text_hash
        assert result.text
        assert result.score is not None
        assert result.metadata["corpus_id"] in {"reformed", "congregational_normative"}
        assert result.metadata["retrieval_namespace"] in {"reformed_confessional", "congregational_normative"}


def test_hybrid_retrieval_reports_exist():
    assert Path("reports/specs/hybrid-retrieval.md").exists()
    assert Path("corpus/reports/retrieval/hybrid-retrieval-report.md").exists()
    assert Path("corpus/reports/retrieval/hybrid-retrieval-report.json").exists()
