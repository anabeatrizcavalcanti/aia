"""Compatibilidade para integrações antigas de geração.

O caminho oficial de geração do projeto é:
RagGenerator -> RetrievalPipeline -> EvidencePolicy -> PromptBuilder ->
CitationFormatter -> OpenAI -> RagAnswer.

Este módulo existe apenas para chamadas legadas que esperam uma função simples
retornando texto. Novas integrações devem usar ``RagGenerator`` diretamente.
"""

from __future__ import annotations

from sola_bot.generation.rag_generator import RagGenerator


def generate_answer(question: str, corpus_id: str | None = None) -> str:
    """Gera texto por compatibilidade, delegando ao ``RagGenerator`` oficial."""
    filters = {"corpus_id": corpus_id} if corpus_id else None
    return RagGenerator().answer(question, filters=filters).answer
