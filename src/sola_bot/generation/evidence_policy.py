"""Política de evidência para geração RAG."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass, field
from typing import Any

from sola_bot.retrieval.final_context import RetrievalContextPackage
from sola_bot.retrieval.context_consolidator import classify_query_intent


DEFAULT_REFUSAL_MESSAGE = (
    "Não encontrei base documental suficiente nos documentos doutrinários e normativos da Aliança para responder "
    "com segurança a essa pergunta. Posso responder apenas quando houver evidência nos "
    "documentos recuperados."
)
STOPWORDS = {
    "a",
    "as",
    "o",
    "os",
    "um",
    "uma",
    "de",
    "da",
    "do",
    "das",
    "dos",
    "em",
    "no",
    "na",
    "nos",
    "nas",
    "para",
    "por",
    "com",
    "sobre",
    "segundo",
    "documentos",
    "documento",
    "reformados",
    "reformado",
    "disponiveis",
    "disponivel",
    "doutrina",
    "esta",
    "qual",
    "quais",
    "que",
    "e",
    "é",
    "trata",
    "tratar",
    "significa",
    "significado",
    "explique",
    "explica",
    "defina",
    "definicao",
    "definição",
    "papel",
    "funcao",
    "função",
    "funciona",
    "funcionamento",
    "estabelece",
    "estabelecem",
    "ensina",
    "tradição",
    "tradicao",
    "reformada",
    "corpus",
    "ativo",
    "posicao",
}
REGENERATION_TERMS = {
    "regeneracao",
    "regenerado",
    "regenerada",
    "regenerados",
    "regeneradas",
    "regenerar",
    "regenera",
    "regenerador",
    "regeneradora",
    "vivificacao",
    "vivificar",
    "vivifica",
    "nascimento",
    "renovacao",
}
QUERY_TERM_EXPANSIONS = {
    "expiacao": {"satisfacao", "sacrificio", "sangue", "morte", "cristo", "redencao"},
    **{term: REGENERATION_TERMS - {term} for term in REGENERATION_TERMS},
}


@dataclass(slots=True)
class EvidenceDecision:
    """Decisão da política de evidência."""

    can_answer: bool
    reason: str
    context_count: int
    total_context_chars: int
    has_source_map: bool
    has_doctrinal_context: bool
    has_normative_context: bool
    has_only_introductory_context: bool
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Converte a decisão para dicionário serializável."""
        return asdict(self)


class EvidencePolicy:
    """Avalia se um pacote de retrieval sustenta uma resposta."""

    def __init__(
        self,
        min_contexts_required: int = 1,
        min_total_context_chars: int = 500,
        allow_answer_with_anchor_only: bool = False,
        require_source_map: bool = True,
        refuse_when_context_is_only_introductory: bool = True,
    ) -> None:
        self.min_contexts_required = min_contexts_required
        self.min_total_context_chars = min_total_context_chars
        self.allow_answer_with_anchor_only = allow_answer_with_anchor_only
        self.require_source_map = require_source_map
        self.refuse_when_context_is_only_introductory = refuse_when_context_is_only_introductory

    def evaluate(self, package: RetrievalContextPackage) -> EvidenceDecision:
        """Avalia suficiência documental do pacote recuperado."""
        context_count = package.context_count
        total_context_chars = package.total_context_chars
        has_source_map = bool(package.source_map)
        priorities = [context.content_priority for context in package.contexts]
        statuses = [context.context_status for context in package.contexts]
        has_doctrinal_context = "doctrinal" in priorities
        has_normative_context = "normative" in priorities
        has_only_introductory_context = bool(priorities) and all(
            priority == "introductory" for priority in priorities
        )
        has_only_anchor_only = bool(statuses) and all(status.startswith("anchor_only") for status in statuses)
        original_query_terms = _significant_terms(package.query)
        query_terms = _expand_query_terms(original_query_terms)
        context_terms = _significant_terms(" ".join(context.context_text for context in package.contexts))
        overlap = sorted(query_terms & context_terms)
        original_overlap = sorted(original_query_terms & context_terms)
        query_intent = classify_query_intent(package.query)
        metadata = {
            "min_contexts_required": self.min_contexts_required,
            "min_total_context_chars": self.min_total_context_chars,
            "allow_answer_with_anchor_only": self.allow_answer_with_anchor_only,
            "query_intent": query_intent,
            "query_terms": sorted(original_query_terms),
            "expanded_query_terms": sorted(query_terms),
            "matched_query_terms": overlap,
            "matched_original_query_terms": original_overlap,
            "context_priorities": priorities,
            "context_statuses": statuses,
        }

        if context_count < self.min_contexts_required:
            return self._decision(False, "no_context", package, has_source_map, has_doctrinal_context, has_normative_context, has_only_introductory_context, metadata)
        if _explicitly_outside_active_corpus(package.query):
            return self._decision(False, "requested_material_outside_active_corpus", package, has_source_map, has_doctrinal_context, has_normative_context, has_only_introductory_context, metadata)
        if total_context_chars < self.min_total_context_chars:
            return self._decision(False, "context_too_short", package, has_source_map, has_doctrinal_context, has_normative_context, has_only_introductory_context, metadata)
        if self.require_source_map and not has_source_map:
            return self._decision(False, "missing_source_map", package, has_source_map, has_doctrinal_context, has_normative_context, has_only_introductory_context, metadata)
        if self.refuse_when_context_is_only_introductory and has_only_introductory_context:
            return self._decision(False, "only_introductory_context", package, has_source_map, has_doctrinal_context, has_normative_context, has_only_introductory_context, metadata)
        if has_only_anchor_only and not self.allow_answer_with_anchor_only:
            if not ((has_doctrinal_context or has_normative_context) and has_source_map):
                return self._decision(False, "only_anchor_context", package, has_source_map, has_doctrinal_context, has_normative_context, has_only_introductory_context, metadata)
        if original_query_terms and not overlap:
            return self._decision(False, "insufficient_query_context_overlap", package, has_source_map, has_doctrinal_context, has_normative_context, has_only_introductory_context, metadata)
        if _has_low_query_context_overlap(original_query_terms, query_terms, context_terms):
            return self._decision(False, "insufficient_query_context_overlap", package, has_source_map, has_doctrinal_context, has_normative_context, has_only_introductory_context, metadata)
        if not original_query_terms:
            return self._decision(False, "insufficient_query_specificity", package, has_source_map, has_doctrinal_context, has_normative_context, has_only_introductory_context, metadata)
        if query_intent == "doctrinal" and not has_doctrinal_context:
            return self._decision(False, "no_doctrinal_context", package, has_source_map, has_doctrinal_context, has_normative_context, has_only_introductory_context, metadata)
        if query_intent == "normative" and not has_normative_context:
            return self._decision(False, "no_normative_context_for_normative_query", package, has_source_map, has_doctrinal_context, has_normative_context, has_only_introductory_context, metadata)
        if query_intent == "mixed" and not (has_doctrinal_context or has_normative_context):
            return self._decision(False, "no_relevant_documentary_context", package, has_source_map, has_doctrinal_context, has_normative_context, has_only_introductory_context, metadata)
        if query_intent == "general" and not (has_doctrinal_context or has_normative_context):
            return self._decision(False, "no_relevant_documentary_context", package, has_source_map, has_doctrinal_context, has_normative_context, has_only_introductory_context, metadata)

        return self._decision(True, "sufficient_documentary_evidence", package, has_source_map, has_doctrinal_context, has_normative_context, has_only_introductory_context, metadata)

    @staticmethod
    def _decision(
        can_answer: bool,
        reason: str,
        package: RetrievalContextPackage,
        has_source_map: bool,
        has_doctrinal_context: bool,
        has_normative_context: bool,
        has_only_introductory_context: bool,
        metadata: dict[str, Any],
    ) -> EvidenceDecision:
        return EvidenceDecision(
            can_answer=can_answer,
            reason=reason,
            context_count=package.context_count,
            total_context_chars=package.total_context_chars,
            has_source_map=has_source_map,
            has_doctrinal_context=has_doctrinal_context,
            has_normative_context=has_normative_context,
            has_only_introductory_context=has_only_introductory_context,
            metadata=metadata,
        )


def has_sufficient_evidence(package: RetrievalContextPackage) -> bool:
    """Compatibilidade simples para verificar evidência suficiente."""
    return EvidencePolicy().evaluate(package).can_answer


def build_evidence_refusal(corpus_id: str = "reformed") -> str:
    """Mensagem padrão de recusa por evidência insuficiente."""
    return DEFAULT_REFUSAL_MESSAGE


def _significant_terms(text: str) -> set[str]:
    normalized = _normalize(text)
    terms = set(re.findall(r"[a-z0-9]+", normalized))
    return {term for term in terms if len(term) >= 4 and term not in STOPWORDS}


def _expand_query_terms(terms: set[str]) -> set[str]:
    expanded = set(terms)
    for term in terms:
        expanded.update(QUERY_TERM_EXPANSIONS.get(term, set()))
    return expanded


def _explicitly_outside_active_corpus(query: str) -> bool:
    normalized = _normalize(query)
    outside_markers = [
        "nao esta no corpus",
        "fora do corpus",
        "documento nao disponivel",
        "documento nao esta disponivel",
        "nao incluido no corpus",
        "nao incluida no corpus",
        "nao incluidos no corpus",
        "nao incluidas no corpus",
    ]
    return any(marker in normalized for marker in outside_markers)


def _has_low_query_context_overlap(
    original_terms: set[str],
    expanded_terms: set[str],
    context_terms: set[str],
) -> bool:
    """Detecta aderência fraca sem depender de uma lista fixa de assuntos."""
    if not original_terms:
        return False

    original_overlap = original_terms & context_terms
    expanded_overlap = expanded_terms & context_terms
    expansion_only_overlap = expanded_overlap - original_overlap

    if len(original_terms) == 1:
        return not bool(original_overlap or expansion_only_overlap)

    if len(original_terms) == 2:
        return len(original_overlap) < len(original_terms)

    return False


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text.lower())
    return normalized.encode("ascii", "ignore").decode("ascii")
