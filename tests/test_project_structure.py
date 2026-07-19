from pathlib import Path


def test_main_project_files_exist():
    assert Path("README.md").exists()
    assert Path("requirements.txt").exists()
    assert Path(".env.example").exists()


def test_main_directories_exist():
    assert Path("src/aia").exists()
    assert Path("corpus/raw/reformed").exists()
    assert Path("corpus/raw/evaluation_sets").exists()
    assert Path("docs").exists()
    assert Path("docs/architecture.mmd").exists()


def test_theoretical_documentation_exists():
    assert Path("docs/theoretical_foundation.md").exists()
    assert Path("docs/retrieval_strategy.md").exists()
    assert Path("docs/evaluation_methodology.md").exists()


def test_advanced_retrieval_modules_exist():
    assert Path("src/aia/retrieval/bm25.py").exists()
    assert Path("src/aia/retrieval/hybrid_retriever.py").exists()
    assert Path("src/aia/retrieval/rrf.py").exists()
    assert Path("src/aia/retrieval/reranker.py").exists()
    assert Path("src/aia/retrieval/metadata_filter.py").exists()
    assert Path("src/aia/retrieval/parent_retriever.py").exists()


def test_generation_and_evaluation_modules_exist():
    assert Path("src/aia/generation/evidence_policy.py").exists()
    assert Path("src/aia/generation/source_grounded_prompt.py").exists()
    assert Path("src/aia/evaluation/ragas_metrics.py").exists()
    assert Path("src/aia/evaluation/ares_metrics.py").exists()
    assert Path("src/aia/evaluation/theological_contamination.py").exists()
    assert Path("src/aia/evaluation/citation_metrics.py").exists()
