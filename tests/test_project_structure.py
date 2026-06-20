from pathlib import Path


def test_main_project_files_exist():
    assert Path("README.md").exists()
    assert Path("requirements.txt").exists()
    assert Path(".env.example").exists()


def test_main_directories_exist():
    assert Path("src/sola_bot").exists()
    assert Path("corpus/raw/reformed").exists()
    assert Path("corpus/raw/evaluation_sets").exists()
    assert Path("docs").exists()
    assert Path("docs/architecture.mmd").exists()


def test_theoretical_documentation_exists():
    assert Path("docs/theoretical_foundation.md").exists()
    assert Path("docs/retrieval_strategy.md").exists()
    assert Path("docs/evaluation_methodology.md").exists()


def test_advanced_retrieval_modules_exist():
    assert Path("src/sola_bot/retrieval/bm25.py").exists()
    assert Path("src/sola_bot/retrieval/hybrid_retriever.py").exists()
    assert Path("src/sola_bot/retrieval/rrf.py").exists()
    assert Path("src/sola_bot/retrieval/reranker.py").exists()
    assert Path("src/sola_bot/retrieval/metadata_filter.py").exists()
    assert Path("src/sola_bot/retrieval/parent_retriever.py").exists()


def test_generation_and_evaluation_modules_exist():
    assert Path("src/sola_bot/generation/evidence_policy.py").exists()
    assert Path("src/sola_bot/generation/source_grounded_prompt.py").exists()
    assert Path("src/sola_bot/evaluation/ragas_metrics.py").exists()
    assert Path("src/sola_bot/evaluation/ares_metrics.py").exists()
    assert Path("src/sola_bot/evaluation/theological_contamination.py").exists()
    assert Path("src/sola_bot/evaluation/citation_metrics.py").exists()
