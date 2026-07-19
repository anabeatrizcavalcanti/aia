"""
Filtros por metadados para controle do corpus ativo.
"""


def apply_metadata_filters(
    candidates: list[dict[str, str]],
    filters: dict[str, str],
) -> list[dict[str, str]]:
    """
    Filtra candidatos por corpus, tradição, documento ou namespace.
    """
    raise NotImplementedError("Metadata filtering is not implemented yet.")
