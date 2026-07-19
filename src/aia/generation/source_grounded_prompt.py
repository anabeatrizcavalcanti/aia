"""Compatibilidade para montagem simples de prompt com fontes.

O caminho oficial de geração usa ``RagGenerator`` com
``prompt_builder.build_rag_prompt``. Este módulo fica disponível apenas para
integrações antigas que já chamavam ``build_source_grounded_prompt``.
"""

from __future__ import annotations


def build_source_grounded_prompt(question: str, context: list[dict[str, str]]) -> str:
    """Monta prompt legado a partir de blocos de contexto já preparados."""
    context_lines = []
    for index, item in enumerate(context, start=1):
        source = item.get("source") or item.get("document") or f"Fonte {index}"
        text = item.get("text") or item.get("context") or ""
        context_lines.append(f"[{index}] {source}\n{text}")

    return "\n".join(
        [
            "Responda usando apenas os contextos documentais abaixo.",
            "Não invente fontes, páginas ou referências.",
            "",
            f"Pergunta: {question}",
            "",
            "Contextos:",
            "\n\n".join(context_lines),
        ]
    ).strip()
