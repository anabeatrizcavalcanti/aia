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
    Path("src/sola_bot/generation/prompt_builder.py"),
    Path("src/sola_bot/generation/evidence_policy.py"),
    Path("src/sola_bot/generation/citation_formatter.py"),
    Path("src/sola_bot/generation/rag_answer.py"),
    Path("src/sola_bot/generation/rag_generator.py"),
    Path("scripts/pipeline/query_rag_generator.py"),
]
REQUIRED_INPUTS = [
    Path("reports/specs/retrieval-pipeline.md"),
    Path("corpus/reports/retrieval/retrieval-pipeline-report.md"),
    Path("corpus/reports/retrieval/retrieval-pipeline-report.json"),
    Path("corpus/processed/chunks/alliance/all_chunks_for_embeddings.jsonl"),
    Path("corpus/indexes/chroma/alliance"),
]
REPORT_PATHS = [
    Path("reports/specs/rag-answer-generation.md"),
    Path("corpus/reports/generation/rag-answer-generation-report.md"),
    Path("corpus/reports/generation/rag-answer-generation-report.json"),
]


def load_dotenv_if_available() -> None:
    if importlib.util.find_spec("dotenv") is None:
        return
    from dotenv import load_dotenv

    load_dotenv()


def make_package(
    query: str = "O que é o batismo?",
    contexts=None,
    source_map=None,
    total_chars: int | None = None,
):
    from sola_bot.retrieval.final_context import FinalContext, RetrievalContextPackage

    if contexts is None:
        context_text = "O batismo é tratado como ordenança do Novo Testamento no corpus reformado. " * 10
        contexts = [
            FinalContext(
                query=query,
                rank=1,
                parent_key="confissao-batista-londres-1689::chapter::capitulo-29",
                parent_title="CAPÍTULO 29 — BATISMO",
                document_id="confissao-batista-londres-1689",
                document="Confissão Batista de Londres de 1689",
                context_text=context_text,
                context_char_count=len(context_text),
                included_chunk_ids=["chunk-1", "chunk-2"],
                anchor_chunk_ids=["chunk-1"],
                anchor_scores=[4.5],
                page_start=74,
                page_end=75,
                source_paths=["corpus/raw/reformed/londres.pdf"],
                context_status="expanded",
                content_priority="doctrinal",
                metadata={},
            )
        ]
    if source_map is None:
        source_map = {
            "source_1": {
                "document": "Confissão Batista de Londres de 1689",
                "document_id": "confissao-batista-londres-1689",
                "parent_key": "confissao-batista-londres-1689::chapter::capitulo-29",
                "parent_title": "CAPÍTULO 29 — BATISMO",
                "pages": "74-75",
                "anchor_chunk_ids": ["chunk-1"],
                "included_chunk_ids": ["chunk-1", "chunk-2"],
                "source_paths": ["corpus/raw/reformed/londres.pdf"],
            }
        }
    total = total_chars if total_chars is not None else sum(context.context_char_count for context in contexts)
    return RetrievalContextPackage(
        query=query,
        contexts=contexts,
        context_count=len(contexts),
        total_context_chars=total,
        documents=sorted({context.document_id for context in contexts}),
        source_map=source_map,
        retrieval_stages=["retrieval_pipeline"],
        filters={},
        metadata={"corpus_scope": "alliance_documents"},
    )


class FakeRetrievalPipeline:
    def __init__(self, package):
        self.package = package
        self.called = False

    def retrieve(self, query, filters=None):
        self.called = True
        return self.package


class FakeOpenAIClient:
    def __init__(self):
        self.called = False
        self.chat = self
        self.completions = self

    def create(self, **kwargs):
        self.called = True
        self.kwargs = kwargs

        class Message:
            content = "Resposta:\nO batismo é apresentado no contexto recuperado.\n\nBase documental:\n- [1] fonte usada."

        class Choice:
            message = Message()

        class Response:
            choices = [Choice()]

        return Response()


def test_generation_files_exist():
    for path in REQUIRED_FILES:
        assert path.exists()


def test_generation_inputs_exist():
    for path in REQUIRED_INPUTS:
        assert path.exists()


def test_citation_formatter_preserves_source_data_and_missing_pages():
    from sola_bot.generation.citation_formatter import citations_from_source_map, format_citations

    package = make_package()
    package.source_map["source_2"] = {
        "document": "Documento sem página",
        "document_id": "doc-sem-pagina",
        "parent_title": "Unidade",
        "anchor_chunk_ids": ["a"],
        "included_chunk_ids": ["a"],
        "source_paths": ["corpus/raw/reformed/doc.pdf"],
    }
    citations = citations_from_source_map(package)
    lines = format_citations(citations)

    assert citations[0].document == "Confissão Batista de Londres de 1689"
    assert citations[0].parent_title == "CAPÍTULO 29 — BATISMO"
    assert citations[0].pages == "74-75"
    assert citations[0].anchor_chunk_ids == ["chunk-1"]
    assert citations[0].source_paths == ["corpus/raw/reformed/londres.pdf"]
    assert "p. 74-75" in lines[0]
    assert "página não informada" in lines[1]


def test_evidence_policy_refuses_and_allows_expected_packages():
    from sola_bot.generation.evidence_policy import EvidencePolicy
    from sola_bot.retrieval.final_context import FinalContext

    policy = EvidencePolicy()
    empty_package = make_package(contexts=[], source_map={}, total_chars=0)
    no_source = make_package(source_map={})
    allowed = make_package()
    introductory_context = FinalContext(
        query="O que é o batismo?",
        rank=1,
        parent_key="intro",
        parent_title="Introdução",
        document_id="doc",
        document="Doc",
        context_text="Texto introdutório sobre história.",
        context_char_count=800,
        included_chunk_ids=["intro"],
        anchor_chunk_ids=["intro"],
        anchor_scores=[1.0],
        page_start=1,
        page_end=1,
        source_paths=["corpus/raw/reformed/doc.pdf"],
        context_status="expanded",
        content_priority="introductory",
        metadata={},
    )
    intro_package = make_package(contexts=[introductory_context])
    unrelated_text = (
        "A justificação é apresentada como ato gratuito de Deus, com perdão dos pecados "
        "e aceitação da pessoa como justa por causa de Cristo. "
    ) * 8
    unrelated_context = FinalContext(
        query="O que é batismo?",
        rank=1,
        parent_key="confissao-batista-londres-1689::chapter::capitulo-11",
        parent_title="CAPÍTULO 11 — A JUSTIFICAÇÃO",
        document_id="confissao-batista-londres-1689",
        document="Confissão Batista de Londres de 1689",
        context_text=unrelated_text,
        context_char_count=len(unrelated_text),
        included_chunk_ids=["justificacao-1"],
        anchor_chunk_ids=["justificacao-1"],
        anchor_scores=[3.2],
        page_start=29,
        page_end=31,
        source_paths=["corpus/raw/reformed/londres.pdf"],
        context_status="expanded",
        content_priority="doctrinal",
        metadata={},
    )
    unrelated_package = make_package(
        query="O que é batismo?",
        contexts=[unrelated_context],
        source_map={
            "source_1": {
                "document": "Confissão Batista de Londres de 1689",
                "document_id": "confissao-batista-londres-1689",
                "parent_title": "CAPÍTULO 11 — A JUSTIFICAÇÃO",
                "pages": "29-31",
                "anchor_chunk_ids": ["justificacao-1"],
                "included_chunk_ids": ["justificacao-1"],
                "source_paths": ["corpus/raw/reformed/londres.pdf"],
            }
        },
    )
    generic_topic_context = FinalContext(
        query="Do que se trata a justificação?",
        rank=1,
        parent_key="confissao-fe-westminster::chapter::capitulo-xi",
        parent_title="CAPÍTULO XI — DA JUSTIFICAÇÃO",
        document_id="confissao-fe-westminster",
        document="Confissão de Fé de Westminster",
        context_text=(
            "A justificação é apresentada como ato gratuito de Deus, com perdão dos pecados "
            "e aceitação da pessoa como justa por causa de Cristo. "
        ) * 8,
        context_char_count=len(unrelated_text),
        included_chunk_ids=["westminster-justificacao-1"],
        anchor_chunk_ids=["westminster-justificacao-1"],
        anchor_scores=[3.2],
        page_start=33,
        page_end=33,
        source_paths=["corpus/raw/reformed/westminster.pdf"],
        context_status="expanded",
        content_priority="doctrinal",
        metadata={},
    )
    generic_topic_package = make_package(
        query="Do que se trata a justificação?",
        contexts=[generic_topic_context],
        source_map={
            "source_1": {
                "document": "Confissão de Fé de Westminster",
                "document_id": "confissao-fe-westminster",
                "parent_title": "CAPÍTULO XI — DA JUSTIFICAÇÃO",
                "pages": "33",
                "anchor_chunk_ids": ["westminster-justificacao-1"],
                "included_chunk_ids": ["westminster-justificacao-1"],
                "source_paths": ["corpus/raw/reformed/westminster.pdf"],
            }
        },
    )
    regeneration_context_text = (
        "A regeneração é descrita como nova criação, vivificação e renovação operada por Deus. "
        "O contexto documental apresenta essa obra como ação eficaz do Espírito, que abre o coração "
        "e produz nova vida espiritual. "
    ) * 5
    regeneration_context = FinalContext(
        query="O que é ser regenerado?",
        rank=1,
        parent_key="canones-de-dort::article::12",
        parent_title="Artigo 12",
        document_id="canones-de-dort",
        document="Cânones de Dort",
        context_text=regeneration_context_text,
        context_char_count=len(regeneration_context_text),
        included_chunk_ids=["dort-regeneracao-1"],
        anchor_chunk_ids=["dort-regeneracao-1"],
        anchor_scores=[3.2],
        page_start=4,
        page_end=27,
        source_paths=["corpus/raw/reformed/dort.pdf"],
        context_status="expanded",
        content_priority="doctrinal",
        metadata={},
    )
    regeneration_package = make_package(
        query="O que é ser regenerado?",
        contexts=[regeneration_context],
        source_map={
            "source_1": {
                "document": "Cânones de Dort",
                "document_id": "canones-de-dort",
                "parent_title": "Artigo 12",
                "pages": "4-27",
                "anchor_chunk_ids": ["dort-regeneracao-1"],
                "included_chunk_ids": ["dort-regeneracao-1"],
                "source_paths": ["corpus/raw/reformed/dort.pdf"],
            }
        },
    )
    outside_corpus_package = make_package(
        query="Qual é a posição sobre um documento não está disponível no corpus?",
    )

    assert policy.evaluate(empty_package).reason == "no_context"
    assert policy.evaluate(no_source).reason == "missing_source_map"
    assert policy.evaluate(allowed).can_answer is True
    assert policy.evaluate(generic_topic_package).can_answer is True
    regeneration_decision = policy.evaluate(regeneration_package)
    assert regeneration_decision.can_answer is True
    assert regeneration_decision.metadata["query_intent"] == "doctrinal"
    assert "regeneracao" in regeneration_decision.metadata["matched_query_terms"]
    assert policy.evaluate(intro_package).reason == "only_introductory_context"
    assert policy.evaluate(unrelated_package).reason == "insufficient_query_context_overlap"
    assert policy.evaluate(outside_corpus_package).reason == "requested_material_outside_active_corpus"


def test_prompt_builder_includes_query_context_sources_and_rules():
    from sola_bot.generation.citation_formatter import citations_from_source_map
    from sola_bot.generation.prompt_builder import build_rag_prompt

    package = make_package()
    prompt = build_rag_prompt(package.query, package, citations_from_source_map(package))

    assert "Pergunta:" in prompt
    assert "O que é o batismo?" in prompt
    assert "Contextos:" in prompt
    assert "Fontes disponíveis:" in prompt
    assert "Use apenas os contextos documentais fornecidos." in prompt
    assert "Não invente fontes" in prompt
    assert "Se a evidência for insuficiente" in prompt
    assert "Separe mudanças de tópico" in prompt
    assert "Não coloque a resposta principal inteira em um único parágrafo" in prompt


def test_rag_generator_answers_with_fake_openai_client():
    from sola_bot.generation.rag_generator import RagGenerator

    package = make_package()
    fake_pipeline = FakeRetrievalPipeline(package)
    fake_client = FakeOpenAIClient()
    generator = RagGenerator(
        model="fake-model",
        retrieval_pipeline=fake_pipeline,
        client=fake_client,
    )

    answer = generator.answer("O que é o batismo?")

    assert fake_pipeline.called is True
    assert fake_client.called is True
    assert answer.status == "answered"
    assert answer.used_context_count == 1
    assert answer.citations
    assert answer.used_documents == ["confissao-batista-londres-1689"]


def test_polish_generated_answer_capitalizes_sentence_starts():
    from sola_bot.generation.rag_generator import polish_generated_answer

    polished = polish_generated_answer(
        "resposta principal.\n\nObservação:\nos contextos recuperados são limitados. ainda assim, há base [1].",
        [],
    )

    assert "Resposta principal." in polished
    assert "Observação:\nOs contextos recuperados são limitados." in polished
    assert "Ainda assim, há base [1]." in polished


def test_polish_generated_answer_spaces_discussed_topics():
    from sola_bot.generation.rag_generator import polish_generated_answer

    raw = (
        "A regeneração é apresentada pelos Cânones de Dort como nova criação e vivificação que Deus opera em nós [1]. "
        "Os Cânones de Dort também explicam que Deus penetra o homem interior, abre corações fechados e abranda os endurecidos [1]. "
        "Por isso, a regeneração não é descrita como algo plenamente compreensível nesta vida, mas como obra conhecida por seus efeitos [1]. "
        "A Confissão de Fé de Westminster e a Confissão Batista de Londres de 1689 usam linguagem muito próxima sobre novo coração e novo espírito [2] [3]. "
        "Isso mostra os efeitos da regeneração na vida do crente, embora os textos estejam tratando diretamente da santificação [2] [3]."
    )

    polished = polish_generated_answer(raw, [])

    assert "[1].\n\nOs Cânones de Dort" in polished
    assert "[1].\n\nPor isso" in polished
    assert "[1].\n\nA Confissão de Fé de Westminster" in polished
    assert "[3].\n\nIsso mostra" in polished


def test_polish_generated_answer_preserves_markdown_lists():
    from sola_bot.generation.rag_generator import polish_generated_answer

    raw = (
        "O Regimento Interno lista deveres da igreja local [1]. "
        "- **Doutrinar**: deve doutrinar cuidadosamente os membros [1]. "
        "- **Cooperar**: deve cooperar espiritualmente com a Aliança [1]."
    )

    polished = polish_generated_answer(raw, [])

    assert "local [1].\n\n- **Doutrinar**" in polished
    assert "[1].\n- **Cooperar**" in polished


def test_polish_generated_answer_removes_trailing_followup_offer():
    from sola_bot.generation.rag_generator import polish_generated_answer

    polished = polish_generated_answer(
        "A justificação é ato gratuito de Deus [1].\n\nSe você quiser, posso comparar as confissões.",
        [],
    )

    assert polished == "A justificação é ato gratuito de Deus [1]."


def test_compact_cited_sources_renumbers_used_references():
    from sola_bot.generation.rag_answer import Citation
    from sola_bot.generation.rag_generator import compact_cited_sources

    citations = [
        Citation(
            source_id=f"source_{index}",
            document=f"Documento {index}",
            document_id=f"documento-{index}",
            parent_title="Unidade",
            pages=None,
            anchor_chunk_ids=[],
            included_chunk_ids=[],
            source_paths=[],
        )
        for index in range(1, 5)
    ]

    text, compacted = compact_cited_sources("A fonte um sustenta isto [1]. A quarta complementa [4]. Repetindo [1].", citations)

    assert text == "A fonte um sustenta isto [1]. A quarta complementa [2]. Repetindo [1]."
    assert [citation.source_id for citation in compacted] == ["source_1", "source_4"]


def test_rag_generator_does_not_call_openai_when_evidence_is_refused():
    from sola_bot.generation.rag_generator import RagGenerator

    package = make_package(contexts=[], source_map={}, total_chars=0)
    fake_pipeline = FakeRetrievalPipeline(package)
    fake_client = FakeOpenAIClient()
    generator = RagGenerator(
        model="fake-model",
        retrieval_pipeline=fake_pipeline,
        client=fake_client,
    )

    answer = generator.answer("Pergunta sem base documental")

    assert answer.status == "refused"
    assert answer.refusal_reason == "no_context"
    assert fake_client.called is False


def test_rag_generator_real_execution_when_dependencies_are_available():
    load_dotenv_if_available()

    if importlib.util.find_spec("openai") is None:
        pytest.skip("openai não está instalado neste ambiente.")
    if importlib.util.find_spec("sentence_transformers") is None:
        pytest.skip("sentence-transformers não está instalado neste ambiente.")
    if importlib.util.find_spec("rank_bm25") is None:
        pytest.skip("rank-bm25 não está instalado neste ambiente.")
    if importlib.util.find_spec("chromadb") is None:
        pytest.skip("chromadb não está instalado neste ambiente.")
    if not os.getenv("OPENAI_API_KEY", "").strip():
        pytest.skip("OPENAI_API_KEY não está configurada neste ambiente.")

    from sola_bot.generation.rag_generator import RagGenerator

    answer = RagGenerator(max_output_tokens=400).answer("O que é justificação?")

    if answer.status == "error":
        pytest.skip(f"Geração real indisponível: {answer.metadata}")
    assert answer.status == "answered"
    assert answer.answer
    assert answer.citations
    assert answer.used_context_count >= 1


def test_rag_generation_reports_exist_and_do_not_have_next_step_sections():
    forbidden = ["Próximo passo", "Próximo passo recomendado", "Next step"]
    for path in REPORT_PATHS:
        assert path.exists()
        if path.suffix == ".md":
            text = path.read_text(encoding="utf-8")
            for phrase in forbidden:
                assert phrase not in text
