"""
Política de evidência para respostas e recusas do SolaBot.
"""


def has_sufficient_evidence(retrieved_chunks: list[dict[str, str]]) -> bool:
    """
    Verifica se os chunks recuperados sustentam uma resposta.
    """
    raise NotImplementedError("Evidence policy is not implemented yet.")


def build_evidence_refusal(corpus_id: str) -> str:
    """
    Cria uma mensagem de recusa quando não há evidência documental suficiente.
    """
    raise NotImplementedError("Evidence-based refusal is not implemented yet.")
