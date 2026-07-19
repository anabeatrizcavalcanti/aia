"""Detecção de escopo documental explícito na pergunta."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any


@dataclass(frozen=True, slots=True)
class QueryDocumentScope:
    """Documento solicitado explicitamente pelo usuário."""

    document_id: str
    document_label: str
    matched_alias: str
    match_type: str


DOCUMENT_ALIASES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    (
        "regimento-interno-alianca-2022",
        "Regimento Interno da Aliança",
        (
            "regimento interno",
            "regimento interno da alianca",
            "regimento da alianca",
            "regimento",
        ),
    ),
    (
        "constituicao-alianca-2022",
        "Constituição da Aliança",
        (
            "constituicao da alianca",
            "constituicao",
        ),
    ),
    (
        "codigo-etica-ministro-alianca",
        "Código de Ética do Ministro Congregacional",
        (
            "codigo de etica",
            "codigo de etica do ministro",
            "codigo de etica ministerial",
        ),
    ),
    (
        "resolucao-alianca-01-2020",
        "Resolução Aliança nº 01/2020",
        (
            "resolucao alianca",
            "resolucao 01 2020",
            "resolucao",
        ),
    ),
    (
        "confissao-fe-congregacional-alianca",
        "Confissão de Fé Congregacional",
        (
            "confissao de fe congregacional",
            "confissao congregacional",
            "confissao da alianca",
        ),
    ),
    (
        "confissao-batista-londres-1689",
        "Confissão Batista de Londres de 1689",
        (
            "confissao batista de londres",
            "confissao batista",
            "londres 1689",
        ),
    ),
    (
        "confissao-fe-westminster",
        "Confissão de Fé de Westminster",
        (
            "confissao de fe de westminster",
            "confissao de westminster",
            "westminster",
        ),
    ),
    (
        "catecismo-heidelberg",
        "Catecismo de Heidelberg",
        (
            "catecismo de heidelberg",
            "heidelberg",
        ),
    ),
    (
        "canones-de-dort",
        "Cânones de Dort",
        (
            "canones de dort",
            "canones",
            "dort",
        ),
    ),
)

COMPARATIVE_SCOPE_PATTERNS = (
    r"\bcompar(?:e|ar|acao|ação|ativo|ativa)\b",
    r"\brelacion(?:e|ar|a|am|ado|ada|amento)\b",
    r"\bconect(?:e|ar|a|am|ado|ada)\b",
    r"\b(?:a|à)\s+luz\s+de\b",
    r"\bem\s+conjunto\s+com\b",
    r"\bjunto\s+com\b",
    r"\bentre\s+(?:os|as|o|a)?\b",
)


def derive_query_document_scope(query: str, filters: dict[str, Any] | None = None) -> QueryDocumentScope | None:
    """
    Detecta quando a pergunta restringe a resposta a um documento específico.

    Quando já existe `document_id` explícito nos filtros, a chamada externa é
    tratada como fonte da verdade e a pergunta não sobrescreve esse escopo.
    """
    if filters and filters.get("document_id"):
        return None

    normalized = normalize_scope_text(query)
    if not normalized or _is_comparative_query(normalized):
        return None

    matches = _document_matches(normalized)
    document_ids = {match.document_id for match in matches}
    if len(document_ids) != 1:
        return None

    return max(matches, key=_scope_match_priority)


def scoped_filters_for_query(
    query: str,
    filters: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], QueryDocumentScope | None]:
    """Combina filtros explícitos com o escopo documental detectado na pergunta."""
    merged = dict(filters or {})
    scope = derive_query_document_scope(query, merged)
    if scope is not None:
        merged["document_id"] = scope.document_id
    return merged, scope


def normalize_scope_text(value: str) -> str:
    """Normaliza texto para matching tolerante a acentos e caixa."""
    normalized = unicodedata.normalize("NFKD", str(value or "").lower())
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_text = re.sub(r"[^a-z0-9]+", " ", ascii_text)
    return re.sub(r"\s+", " ", ascii_text).strip()


def _document_matches(normalized_query: str) -> list[QueryDocumentScope]:
    matches: list[QueryDocumentScope] = []
    for document_id, label, aliases in DOCUMENT_ALIASES:
        for alias in aliases:
            normalized_alias = normalize_scope_text(alias)
            if not normalized_alias:
                continue
            if _contains_phrase(normalized_query, normalized_alias):
                matches.append(
                    QueryDocumentScope(
                        document_id=document_id,
                        document_label=label,
                        matched_alias=alias,
                        match_type="exact",
                    )
                )
                continue
            if _fuzzy_contains_phrase(normalized_query, normalized_alias):
                matches.append(
                    QueryDocumentScope(
                        document_id=document_id,
                        document_label=label,
                        matched_alias=alias,
                        match_type="fuzzy",
                    )
                )
    return matches


def _contains_phrase(normalized_query: str, normalized_alias: str) -> bool:
    return bool(re.search(rf"(?<![a-z0-9]){re.escape(normalized_alias)}(?![a-z0-9])", normalized_query))


def _fuzzy_contains_phrase(normalized_query: str, normalized_alias: str) -> bool:
    alias_tokens = normalized_alias.split()
    query_tokens = normalized_query.split()
    if not alias_tokens or len(query_tokens) < len(alias_tokens):
        return False

    if len(alias_tokens) == 1 and len(alias_tokens[0]) < 7:
        return False

    threshold = 0.88 if len(alias_tokens) == 1 else 0.84
    window_size = len(alias_tokens)
    for index in range(0, len(query_tokens) - window_size + 1):
        window = " ".join(query_tokens[index : index + window_size])
        if SequenceMatcher(None, normalized_alias, window).ratio() >= threshold:
            return True
    return False


def _is_comparative_query(normalized_query: str) -> bool:
    return any(re.search(pattern, normalized_query) for pattern in COMPARATIVE_SCOPE_PATTERNS)


def _scope_match_priority(scope: QueryDocumentScope) -> tuple[int, int]:
    match_score = 1 if scope.match_type == "exact" else 0
    return match_score, len(normalize_scope_text(scope.matched_alias))
