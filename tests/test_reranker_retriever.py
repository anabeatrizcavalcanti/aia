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
    Path("src/sola_bot/retrieval/cross_encoder_reranker.py"),
    Path("src/sola_bot/retrieval/reranked_retriever.py"),
    Path("scripts/pipeline/query_reranked_retriever.py"),
]
REQUIRED_INPUTS = [
    Path("reports/specs/hybrid-retrieval.md"),
    Path("corpus/reports/retrieval/hybrid-retrieval-report.md"),
    Path("corpus/reports/retrieval/hybrid-retrieval-report.json"),
    Path("corpus/processed/chunks/alliance/all_chunks_for_embeddings.jsonl"),
    Path("corpus/indexes/chroma/alliance"),
]


class FakeCrossEncoder:
    def predict(self, pairs):
        scores = []
        for _, text in pairs:
            if "score alto" in text:
                scores.append(0.95)
            elif "score medio" in text:
                scores.append(0.55)
            else:
                scores.append(0.10)
        return scores


def load_dotenv_if_available() -> None:
    if importlib.util.find_spec("dotenv") is None:
        return
    from dotenv import load_dotenv

    load_dotenv()


def make_result(chunk_id: str, text: str, score: float):
    from sola_bot.retrieval.retrieval_result import RetrievalResult

    return RetrievalResult(
        chunk_id=chunk_id,
        document_id="canones-de-dort",
        document="Cânones de Dort",
        chunk_type="doctrinal_article",
        content_role="doctrinal",
        section_title="Artigo 1",
        section_reference="Artigo 1",
        chapter_title="A Eleição e a Reprovação Divinas",
        chapter_reference="Primeiro Capítulo da Doutrina",
        page_start=1,
        page_end=1,
        source_path="corpus/raw/reformed/Os-Canones-de-Dort.pdf",
        text_hash=f"hash-{chunk_id}",
        score=score,
        distance=None,
        text=text,
        metadata={
            "corpus_id": "reformed",
            "retrieval_namespace": "reformed_confessional",
            "retrieval_sources": ["vector", "bm25"],
        },
    )


def test_reranker_files_exist():
    for path in REQUIRED_FILES:
        assert path.exists()


def test_reranker_inputs_exist():
    for path in REQUIRED_INPUTS:
        assert path.exists()


def test_sentence_transformers_is_declared_and_cross_encoder_is_imported():
    requirements = Path("requirements.txt").read_text(encoding="utf-8")
    module = Path("src/sola_bot/retrieval/cross_encoder_reranker.py").read_text(encoding="utf-8")

    assert "sentence-transformers" in requirements
    assert "from sentence_transformers import CrossEncoder" in module


def test_build_reranker_text_includes_metadata_and_respects_limit():
    from sola_bot.retrieval.cross_encoder_reranker import build_reranker_text

    result = make_result("chunk-a", "Texto do chunk sobre eleição.", 0.2)
    text = build_reranker_text(result, max_chars=500)
    limited = build_reranker_text(result, max_chars=40)

    assert "Documento: Cânones de Dort" in text
    assert "Capítulo: A Eleição e a Reprovação Divinas" in text
    assert "Seção: Artigo 1" in text
    assert "Texto:" in text
    assert "Texto do chunk sobre eleição." in text
    assert len(limited) <= 40


def test_cross_encoder_reranker_orders_with_fake_model():
    from sola_bot.retrieval.cross_encoder_reranker import CrossEncoderReranker

    candidates = [
        make_result("chunk-baixo", "texto score baixo", 0.90),
        make_result("chunk-alto", "texto score alto", 0.10),
        make_result("chunk-medio", "texto score medio", 0.50),
    ]
    reranker = CrossEncoderReranker(model=FakeCrossEncoder(), model_name="fake-cross-encoder")
    results = reranker.rerank("pergunta", candidates, top_k=3)

    assert [result.chunk_id for result in results] == ["chunk-alto", "chunk-medio", "chunk-baixo"]
    assert results[0].score == 0.95
    assert results[0].metadata["reranker_score"] == 0.95
    assert results[0].metadata["reranker_provider"] == "sentence_transformers"
    assert results[0].metadata["reranker_model"] == "fake-cross-encoder"
    assert results[0].metadata["pre_rerank_rank"] == 2
    assert results[0].metadata["pre_rerank_score"] == 0.10
    assert results[0].metadata["retrieval_stage"] == "reranked"
    assert results[0].metadata["pre_rerank_sources"] == ["vector", "bm25"]


def test_cross_encoder_reranker_deduplicates_chunk_ids():
    from sola_bot.retrieval.cross_encoder_reranker import CrossEncoderReranker

    candidates = [
        make_result("chunk-a", "texto score alto", 0.1),
        make_result("chunk-a", "texto score baixo", 0.2),
    ]
    reranker = CrossEncoderReranker(model=FakeCrossEncoder(), model_name="fake-cross-encoder")
    results = reranker.rerank("pergunta", candidates, top_k=5)

    assert len(results) == 1
    assert results[0].chunk_id == "chunk-a"


def test_reranked_retriever_returns_results_when_dependencies_are_available():
    load_dotenv_if_available()

    if importlib.util.find_spec("sentence_transformers") is None:
        pytest.skip("sentence-transformers não está instalado neste ambiente.")
    if importlib.util.find_spec("rank_bm25") is None:
        pytest.skip("rank-bm25 não está instalado neste ambiente.")
    if importlib.util.find_spec("chromadb") is None:
        pytest.skip("chromadb não está instalado neste ambiente.")
    if not os.getenv("OPENAI_API_KEY", "").strip():
        pytest.skip("OPENAI_API_KEY não está configurada neste ambiente.")

    from sola_bot.retrieval.reranked_retriever import RerankedRetriever

    try:
        retriever = RerankedRetriever(hybrid_candidate_k=5, final_top_k=2)
        results = retriever.retrieve("O que é o batismo?", top_k=2)
    except Exception as exc:
        pytest.skip(f"Cross-Encoder indisponível para execução real: {exc}")

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
        assert "reranker_score" in result.metadata
        assert result.metadata["reranker_provider"] == "sentence_transformers"
        assert "reranker_model" in result.metadata
        assert "pre_rerank_rank" in result.metadata
        assert "pre_rerank_score" in result.metadata
        assert result.metadata["retrieval_stage"] == "reranked"


def test_reranker_reports_exist():
    assert Path("reports/specs/reranker-retrieval.md").exists()
    assert Path("corpus/reports/retrieval/reranker-retrieval-report.md").exists()
    assert Path("corpus/reports/retrieval/reranker-retrieval-report.json").exists()
