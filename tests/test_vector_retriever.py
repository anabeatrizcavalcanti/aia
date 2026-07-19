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
    Path("src/aia/retrieval/vector_retriever.py"),
    Path("src/aia/retrieval/query_embedder.py"),
    Path("src/aia/retrieval/retrieval_result.py"),
    Path("scripts/pipeline/query_vector_retriever.py"),
]


def load_dotenv_if_available() -> None:
    if importlib.util.find_spec("dotenv") is None:
        return
    from dotenv import load_dotenv

    load_dotenv()


def test_vector_retrieval_files_exist():
    for path in REQUIRED_FILES:
        assert path.exists()


def test_vector_index_directory_exists():
    index_dir = Path("corpus/indexes/chroma/alliance")
    assert index_dir.exists()
    assert any(index_dir.iterdir())


def test_vector_retrieval_reports_exist():
    assert Path("reports/specs/vector-retrieval.md").exists()
    assert Path("corpus/reports/retrieval/vector-retrieval-report.md").exists()
    assert Path("corpus/reports/retrieval/vector-retrieval-report.json").exists()


def test_optional_filters_are_preserved():
    from aia.retrieval.vector_retriever import VectorRetriever

    where = VectorRetriever.__new__(VectorRetriever).build_where_filter(
        {"document_id": "canones-de-dort"}
    )

    assert where == {"document_id": "canones-de-dort"}


def test_vector_retriever_returns_results_when_dependencies_are_available():
    load_dotenv_if_available()

    if importlib.util.find_spec("chromadb") is None:
        pytest.skip("chromadb não está instalado neste ambiente.")
    if not os.getenv("OPENAI_API_KEY", "").strip():
        pytest.skip("OPENAI_API_KEY não está configurada neste ambiente.")

    from aia.retrieval.vector_retriever import VectorRetriever

    retriever = VectorRetriever()
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
