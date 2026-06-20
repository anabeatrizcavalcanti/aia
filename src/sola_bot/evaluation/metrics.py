"""
Métricas de avaliação para o pipeline RAG.
"""


def calculate_documentary_faithfulness(answer: str, sources: list[str]) -> float:
    """
    Calcula uma métrica inicial de fidelidade documental.

    A métrica real será definida durante a etapa de avaliação.
    """
    raise NotImplementedError("Evaluation metrics are not implemented yet.")
