"""Consolidação do contexto hierárquico para a saída final de retrieval."""

from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from dataclasses import replace
from typing import Any

from aia.retrieval.final_context import FinalContext, RetrievalContextPackage
from aia.retrieval.parent_context import ParentContext


DEFAULT_FILTERS = {
}
DOCTRINAL_CHUNK_TYPES = {
    "doctrinal_article",
    "confessional_paragraph",
    "confession_paragraph",
    "confessional_section",
    "catechism_question_answer",
    "error_refutation",
    "conclusion_paragraph",
    "numbered_doctrinal_point",
}
DOCTRINAL_DOCUMENT_TYPES = {
    "confession_of_faith",
    "catechism",
    "doctrinal_canons",
}
NORMATIVE_DOCUMENT_TYPES = {
    "constitution",
    "internal_regiment",
    "normative_ethics",
    "administrative_resolution",
}
INTRODUCTORY_CHUNK_TYPES = {
    "introductory_context",
    "preface",
    "summary",
    "index",
    "bibliographic_note",
    "special_layout",
}
DOCTRINAL_TERMS = {
    "doutrina",
    "ensina",
    "ensino",
    "salvação",
    "salvacao",
    "batismo",
    "eleição",
    "eleicao",
    "justificação",
    "justificacao",
    "pecado",
    "pecados",
    "queda",
    "humano",
    "humana",
    "humanos",
    "humanas",
    "regeneração",
    "regeneracao",
    "regenerado",
    "regenerada",
    "regenerados",
    "regeneradas",
    "regenerar",
    "chamado",
    "vocação",
    "vocacao",
    "eficaz",
    "expiação",
    "expiacao",
    "escrituras",
    "sacramentos",
    "perseverança",
    "perseveranca",
    "fé",
    "fe",
    "graça",
    "graca",
    "doutrinário",
    "doutrinario",
    "doutrinários",
    "doutrinarios",
}
NORMATIVE_TERMS = {
    "alianca",
    "aliança",
    "constituicao",
    "constituição",
    "regimento",
    "codigo",
    "código",
    "etica",
    "ética",
    "resolucao",
    "resolução",
    "filiacao",
    "filiação",
    "filiada",
    "filiado",
    "igreja",
    "local",
    "deveres",
    "ordenacao",
    "ordenação",
    "ministro",
    "ministerio",
    "ministério",
    "pastor",
    "disciplina",
    "emancipacao",
    "emancipação",
    "congregacao",
    "congregação",
    "campo",
    "missao",
    "missão",
    "missoes",
    "missões",
    "missionario",
    "missionário",
    "missionarios",
    "missionários",
    "contribuicao",
    "contribuição",
    "candidato",
    "requisito",
    "requisitos",
    "processo",
    "artigo",
    "inciso",
    "paragrafo",
    "parágrafo",
    "diretoria",
    "conselho",
}
DENOMINATIONAL_SCOPE_TERMS = {
    "alianca",
    "aliança",
}
INSTITUTIONAL_TERMS = {
    "governo",
    "norma",
    "normas",
    "normativo",
    "normativa",
    "normativos",
    "normativas",
    "institucional",
    "institucionais",
    "constituicao",
    "constituição",
    "regimento",
    "codigo",
    "código",
    "etica",
    "ética",
    "decisoes",
    "decisões",
    "conciliares",
    "resolucoes",
    "resoluções",
    "resolucao",
    "resolução",
    "igreja",
    "igrejas",
    "filiada",
    "filiadas",
    "ministro",
    "ministros",
    "pastor",
    "pastores",
}
DOCTRINAL_BRIDGE_TERMS = {
    "doutrina",
    "doutrinaria",
    "doutrinária",
    "doutrinario",
    "doutrinário",
    "professada",
    "professado",
    "confissao",
    "confissão",
    "escrituras",
    "escritura",
    "fe",
    "fé",
}
CONGREGATIONAL_SCOPE_TERMS = {
    "alianca",
    "aliança",
    "congregacional",
    "congregacionais",
}
NORMATIVE_SUBJECT_SCOPE_RULES: tuple[dict[str, Any], ...] = (
    {
        "id": "ecclesiastical_discipline_rules",
        "subject": "church_discipline",
        "intent": "disciplinary_rules",
        "subject_aliases": (
            "disciplina",
            "disciplinar",
            "disciplina eclesiastica",
            "disciplina eclesiástica",
            "processo disciplinar",
            "pena disciplinar",
            "penas disciplinares",
        ),
        "intent_aliases": (
            "regra",
            "regras",
            "geral",
            "gerais",
            "norma",
            "normas",
            "procedimento",
            "procedimentos",
            "processo",
            "apuração",
            "apuracao",
            "defesa",
            "acusado",
            "sanção",
            "sancao",
            "sanções",
            "sancoes",
            "pena",
            "penas",
        ),
        "allowed_units": {
            "regimento-interno-alianca-2022": (
                {"article": "16", "priority": 90},
                {"article": "17", "priority": 85},
                {"article": "50", "priority": 80},
                {"article": "55", "priority": 76},
                {"article": "56", "priority": 74},
                {"article": "58", "priority": 72},
                {"article": "62", "priority": 70},
                {"article": "54", "priority": 65},
                {"article": "51", "priority": 60},
                {"article": "57", "priority": 58},
                {"article": "59", "priority": 56},
                {"article": "60", "priority": 54},
                {"article": "61", "priority": 52},
                {"article": "29", "priority": 30},
            ),
            "constituicao-alianca-2022": (
                {"article": "7", "priority": 35},
                {"article": "29", "priority": 32},
                {"article": "31", "priority": 30},
            ),
            "codigo-etica-ministro-alianca": (
                {"article": "1", "priority": 25},
                {"article": "2", "priority": 24},
            ),
        },
        "framing_chunk_ids": {
            "regimento-interno-alianca-2022": (
                "regimento-interno-alianca-2022_artigo-016",
                "regimento-interno-alianca-2022_artigo-017",
                "regimento-interno-alianca-2022_artigo-050",
                "regimento-interno-alianca-2022_artigo-051",
                "regimento-interno-alianca-2022_artigo-054",
                "regimento-interno-alianca-2022_artigo-055",
                "regimento-interno-alianca-2022_artigo-056",
                "regimento-interno-alianca-2022_artigo-057",
                "regimento-interno-alianca-2022_artigo-058",
                "regimento-interno-alianca-2022_artigo-059",
                "regimento-interno-alianca-2022_artigo-060",
                "regimento-interno-alianca-2022_artigo-061",
                "regimento-interno-alianca-2022_artigo-062",
            ),
            "constituicao-alianca-2022": (
                "constituicao-alianca-2022_artigo-007",
                "constituicao-alianca-2022_artigo-029",
                "constituicao-alianca-2022_artigo-031",
            ),
            "codigo-etica-ministro-alianca": (
                "codigo-etica-ministro-alianca_artigo-001",
                "codigo-etica-ministro-alianca_artigo-002",
            ),
        },
        "coverage_query_terms": (
            "disciplina eclesiástica regras processo disciplinar pena disciplinar "
            "apuração da verdade amplo direito de defesa acusado penalidades faltas "
            "denúncia oitiva parecer Regimento Interno art. 16 art. 17 art. 50 a 62"
        ),
        "min_final_contexts": 5,
        "positive_context_patterns": (
            r"\bdisciplina\s+eclesiastica\b",
            r"\bpena\s+disciplinar\b",
            r"\bpenas\s+disciplinares\b",
            r"\bprocesso\s+disciplinar\b",
            r"\bapuracao\s+da\s+verdade\b",
            r"\bamplo\s+direito\s+de\s+defesa\b",
            r"\bacao\s+disciplinar\b",
            r"\bfaltas?\s+sao\b",
            r"\bacusado\b",
            r"\bdenuncia\b",
            r"\boitiva\b",
            r"\bparecer\b",
            r"\bpenalidades\b",
        ),
        "negative_context_patterns": (
            r"\bingresso\b",
            r"\bfiliacao\b",
            r"\brequerimento\b",
            r"\bcandidatos?\b",
            r"\bcomprovatorio\b",
            r"\bultimos\s+dois\s+anos\b",
            r"\bsituacao\s+regular\b",
            r"\bquadro\s+de\s+ministros\b",
            r"\bconselho\s+de\s+pastores\s+devera\s+orientar\s+assistir\s+coordenar\b",
        ),
    },
    {
        "id": "ministerial_ordination_requirements",
        "subject": "ministers",
        "intent": "ordination_requirements",
        "subject_aliases": (
            "ordenacao",
            "ordenação",
            "ordenacao ministerial",
            "ordenação ministerial",
            "ordenacao pastoral",
            "ordenação pastoral",
            "sagrado ministerio",
            "sagrado ministério",
            "processo de ordenacao",
            "processo de ordenação",
        ),
        "intent_aliases": (
            "documento",
            "documentos",
            "tratam",
            "trata",
            "requisito",
            "requisitos",
            "criterio",
            "critério",
            "criterios",
            "critérios",
            "processo",
            "fase",
            "fases",
            "avaliacao",
            "avaliação",
            "prova",
            "monografia",
            "formacao",
            "formação",
            "certidoes",
            "certidões",
            "homologacao",
            "homologação",
        ),
        "allowed_units": {
            "constituicao-alianca-2022": (
                {"article": "5", "paragraph": "2º", "priority": 95},
                {"article": "5", "paragraph": "3º", "priority": 90},
                {"article": "60", "priority": 45},
                {"article": "61", "priority": 45},
            ),
            "regimento-interno-alianca-2022": (
                {"article": "36", "priority": 92},
                {"article": "37", "priority": 90},
                {"article": "34", "priority": 82},
                {"article": "35", "priority": 80},
                {"article": "40", "priority": 72},
                {"article": "120", "priority": 60},
                {"article": "41", "priority": 45},
            ),
            "resolucao-alianca-01-2020": (
                {"article": "3", "priority": 88},
                {"article": "1", "priority": 70},
                {"article": "2", "priority": 65},
            ),
        },
        "framing_chunk_ids": {
            "constituicao-alianca-2022": (
                "constituicao-alianca-2022_artigo-005_paragrafo-2o",
                "constituicao-alianca-2022_artigo-005_paragrafo-3o",
            ),
            "regimento-interno-alianca-2022": (
                "regimento-interno-alianca-2022_artigo-034",
                "regimento-interno-alianca-2022_artigo-035",
                "regimento-interno-alianca-2022_artigo-036",
                "regimento-interno-alianca-2022_artigo-037",
                "regimento-interno-alianca-2022_artigo-040",
                "regimento-interno-alianca-2022_artigo-120",
            ),
            "resolucao-alianca-01-2020": (
                "resolucao-alianca-01-2020_artigo-001",
                "resolucao-alianca-01-2020_artigo-003",
            ),
        },
        "coverage_query_terms": (
            "ordenação ministerial processo de ordenação candidatos a pastores "
            "Constituição art. 5 § 2 § 3 Regimento Interno art. 34 art. 35 art. 36 art. 37 "
            "avaliação psicológica avaliação oral prova escrita defesa de monografia "
            "Resolução 01/2020 art. 3 obreiros pontos de pregação congregações campos missionários"
        ),
        "min_final_contexts": 6,
        "positive_context_patterns": (
            r"\bprocesso\s+de\s+ordenacao\b",
            r"\bordenacao\s+ao\s+sagrado\s+ministerio\b",
            r"\bcandidatos?\s+a\s+pastores?\b",
            r"\bavaliacao\s+psicologica\b",
            r"\bavaliacao\s+oral\b",
            r"\bprova\s+escrita\b",
            r"\bmonografia\b",
            r"\bcertidoes?\s+negativas?\b",
            r"\bformacao\s+teologica\b",
            r"\bobreiros?\s+vinculados?\b",
            r"\bpontos?\s+de\s+pregacao\b",
            r"\bcampos?\s+missionarios?\b",
        ),
        "negative_context_patterns": (
            r"\bconfissao\s+de\s+fe\b",
            r"\bcodigo\s+de\s+etica\b",
            r"\bdenuncia\b",
            r"\breclamacao\b",
            r"\bquestoes?\s+relacionadas?\s+a\s+transgressao\b",
            r"\brespeito\s+especial\s+pelos\s+ministros\b",
            r"\bministro\s+procedente\s+de\s+outra\s+comunidade\b",
        ),
    },
    {
        "id": "church_admission_requirements",
        "subject": "churches",
        "intent": "admission_requirements",
        "subject_aliases": (
            "igreja",
            "igrejas",
            "igreja candidata",
            "igrejas candidatas",
        ),
        "intent_aliases": (
            "ingresso",
            "filiacao",
            "filiação",
            "filiar",
            "filiem",
            "requisito",
            "requisitos",
            "documentacao",
            "documentação",
        ),
        "allowed_units": {
            "constituicao-alianca-2022": (
                {"article": "5", "paragraph": "1º", "priority": 30},
                {"article": "3", "priority": 20},
                {"article": "1", "priority": 10},
            ),
            "regimento-interno-alianca-2022": (
                {"article": "7", "priority": 25},
                {"article": "6", "priority": 15},
            ),
        },
        "framing_chunk_ids": {
            "constituicao-alianca-2022": (
                "constituicao-alianca-2022_artigo-003",
                "constituicao-alianca-2022_artigo-001",
            ),
            "regimento-interno-alianca-2022": (
                "regimento-interno-alianca-2022_artigo-007",
                "regimento-interno-alianca-2022_artigo-006",
            ),
        },
        "coverage_query_terms": (
            "processo filiação igreja requerimento documentação Região Administrativa "
            "Diretoria Nacional parecer Regimento Interno art. 6 art. 7 Constituição art. 5"
        ),
        "min_final_contexts": 5,
        "positive_context_patterns": (
            r"\bigrejas?\s+candidatas\b",
            r"\bingresso\s+de\s+igrejas?\b",
            r"\bpoderao\s+filiar\s*se\s+a\s+alianca\s+igrejas?\b",
            r"\bigrejas?\s+evangelicas?\s+de\s+governo\s+congregacional\b",
            r"\bpedido\s+de\s+filiacao\b",
            r"\bregiao\s+administrativa\b",
            r"\bdiretoria\s+nacional\b",
        ),
        "negative_context_patterns": (
            r"\bcandidatos?\s+a\s+pastores?\b",
            r"\bpastores?\b",
            r"\bpresbiteros?\b",
            r"\bdiaconos?\b",
            r"\bmissionarios?\b",
            r"\bmissionarias?\b",
            r"\bpostulante\b",
        ),
    },
    {
        "id": "pastor_admission_requirements",
        "subject": "pastors",
        "intent": "admission_requirements",
        "subject_aliases": (
            "pastor",
            "pastores",
            "candidato a pastor",
            "candidatos a pastores",
        ),
        "intent_aliases": (
            "ingresso",
            "filiacao",
            "filiação",
            "filiar",
            "requisito",
            "requisitos",
            "documentacao",
            "documentação",
        ),
        "allowed_units": {
            "constituicao-alianca-2022": (
                {"article": "5", "paragraph": "2º", "priority": 30},
                {"article": "5", "paragraph": "3º", "priority": 20},
                {"article": "4", "priority": 10},
            ),
        },
        "positive_context_patterns": (
            r"\bcandidatos?\s+a\s+pastores?\b",
            r"\bpastores?\b",
            r"\bformacao\s+teologica\b",
        ),
        "negative_context_patterns": (
            r"\bigrejas?\s+candidatas\b",
            r"\bpresbiteros?\b",
            r"\bdiaconos?\b",
            r"\bmissionarios?\b",
            r"\bmissionarias?\b",
        ),
    },
    {
        "id": "officer_missionary_admission_requirements",
        "subject": "officers_and_missionaries",
        "intent": "admission_requirements",
        "subject_aliases": (
            "presbitero",
            "presbítero",
            "presbiteros",
            "presbíteros",
            "diacono",
            "diácono",
            "diaconos",
            "diáconos",
            "missionario",
            "missionário",
            "missionarios",
            "missionários",
            "missionaria",
            "missionária",
            "missionarias",
            "missionárias",
            "oficiais",
        ),
        "intent_aliases": (
            "ingresso",
            "filiacao",
            "filiação",
            "filiar",
            "requisito",
            "requisitos",
            "documentacao",
            "documentação",
        ),
        "allowed_units": {
            "constituicao-alianca-2022": (
                {"article": "5", "paragraph": "4º", "priority": 30},
                {"article": "4", "priority": 10},
            ),
        },
        "positive_context_patterns": (
            r"\bpresbiteros?\b",
            r"\bdiaconos?\b",
            r"\bmissionarios?\b",
            r"\bmissionarias?\b",
            r"\boficiais\b",
        ),
        "negative_context_patterns": (
            r"\bigrejas?\s+candidatas\b",
            r"\bcandidatos?\s+a\s+pastores?\b",
        ),
    },
    {
        "id": "congregation_emancipation_affiliation",
        "subject": "congregations",
        "intent": "emancipation_affiliation",
        "subject_aliases": (
            "congregacao",
            "congregação",
            "congregacoes",
            "congregações",
            "ponto de pregacao",
            "ponto de pregação",
            "pontos de pregacao",
            "pontos de pregação",
            "campo missionario",
            "campo missionário",
            "campos missionarios",
            "campos missionários",
        ),
        "intent_aliases": (
            "emancipacao",
            "emancipação",
            "emancipada",
            "emancipado",
            "emancipar",
            "filiação",
            "filiacao",
            "filiada",
            "filiado",
            "filiar",
            "igreja filiada",
            "tornar igreja",
            "tornar uma igreja",
        ),
        "allowed_units": {
            "regimento-interno-alianca-2022": (
                {"article": "6", "priority": 50},
                {"article": "7", "priority": 45},
            ),
            "resolucao-alianca-01-2020": (
                {"article": "2", "priority": 40},
                {"article": "1", "priority": 30},
            ),
            "constituicao-alianca-2022": (
                {"article": "5", "paragraph": "1º", "priority": 20},
            ),
        },
        "framing_chunk_ids": {
            "regimento-interno-alianca-2022": (
                "regimento-interno-alianca-2022_artigo-006",
                "regimento-interno-alianca-2022_artigo-007",
            ),
            "resolucao-alianca-01-2020": (
                "resolucao-alianca-01-2020_artigo-002",
                "resolucao-alianca-01-2020_artigo-001",
            ),
            "constituicao-alianca-2022": (
                "constituicao-alianca-2022_artigo-005_paragrafo-1o_inciso-i",
            ),
        },
        "coverage_query_terms": (
            "requisitos documentação filiação emancipação congregação igreja filiada "
            "Regimento Interno art. 6 art. 7 Resolução 01/2020 Constituição art. 5 § 1º"
        ),
        "min_final_contexts": 5,
        "positive_context_patterns": (
            r"\bcongregacoes?\b",
            r"\bpontos?\s+de\s+pregacao\b",
            r"\bcampos?\s+missionarios?\b",
            r"\bemancipacao\b",
            r"\bformalmente\s+organizada\s+como\s+igreja\b",
            r"\bpedido\s+de\s+filiacao\b",
            r"\bregiao\s+administrativa\b",
        ),
        "negative_context_patterns": (
            r"\bcandidatos?\s+a\s+pastores?\b",
            r"\bpresbiteros?\s*,?\s+diaconos?\s*,?\s+missionarios?\b",
        ),
    },
)
SPECIFIC_DOCUMENT_TERMS = {
    "westminster",
    "londres",
    "batista",
    "dort",
    "heidelberg",
    "catecismo",
    "canones",
    "cânones",
    "constituicao",
    "constituição",
    "regimento",
    "codigo",
    "código",
    "etica",
    "ética",
    "resolucao",
    "resolução",
}


class ContextConsolidator:
    """Agrupa, prioriza e limita contextos hierárquicos."""

    def __init__(
        self,
        final_context_top_k: int = 4,
        max_total_context_chars: int = 18000,
        max_context_chars_per_parent: int = 9000,
        consolidate_by_parent_key: bool = True,
        deduplicate_included_chunks: bool = True,
        prefer_expanded_contexts: bool = True,
        reduce_introductory_context_for_doctrinal_queries: bool = True,
        keep_anchor_only_when_no_expanded_alternative: bool = True,
        preserve_document_diversity: bool = True,
        max_contexts_per_parent_key: int = 1,
    ) -> None:
        self.final_context_top_k = final_context_top_k
        self.max_total_context_chars = max_total_context_chars
        self.max_context_chars_per_parent = max_context_chars_per_parent
        self.consolidate_by_parent_key = consolidate_by_parent_key
        self.deduplicate_included_chunks = deduplicate_included_chunks
        self.prefer_expanded_contexts = prefer_expanded_contexts
        self.reduce_introductory_context_for_doctrinal_queries = reduce_introductory_context_for_doctrinal_queries
        self.keep_anchor_only_when_no_expanded_alternative = keep_anchor_only_when_no_expanded_alternative
        self.preserve_document_diversity = preserve_document_diversity
        self.max_contexts_per_parent_key = max_contexts_per_parent_key

    def consolidate(
        self,
        query: str,
        parent_contexts: list[ParentContext],
        filters: dict[str, Any] | None = None,
    ) -> RetrievalContextPackage:
        """Consolida contextos hierárquicos em um pacote final."""
        merged_filters = self._merge_filters(filters)
        query_intent = classify_query_intent(query)
        query_is_doctrinal = query_intent in {"doctrinal", "mixed"}
        query_is_normative = query_intent in {"normative", "mixed"}
        grouped_contexts = self._group_contexts(parent_contexts)
        candidates = [
            self._build_final_context(query, group, parent_key, query_is_doctrinal, query_is_normative)
            for parent_key, group in grouped_contexts.items()
        ]
        candidates, removal_metadata = self._remove_introductory_anchor_only(candidates, query_is_doctrinal)
        candidates = self._apply_anchor_only_handling(candidates)
        candidates = sorted(candidates, key=lambda context: context.metadata["ranking_score"], reverse=True)
        candidates, dedupe_metadata = self._deduplicate_chunks_across_contexts(candidates)
        candidates, diversity_metadata = self._promote_document_diversity(
            candidates=candidates,
            query=query,
            filters=merged_filters,
        )
        candidates_before_final_selection = list(candidates)
        effective_final_context_top_k = max(
            self.final_context_top_k,
            normative_subject_scope_context_limit(query) or self.final_context_top_k,
        )
        selected, limit_metadata = self._apply_limits(
            candidates,
            final_context_top_k=effective_final_context_top_k,
        )

        ranked_contexts = [
            replace(context, rank=rank)
            for rank, context in enumerate(selected, start=1)
        ]
        retrieval_candidates = build_retrieval_candidates(
            parent_contexts=parent_contexts,
            final_candidates=candidates_before_final_selection,
            selected_contexts=ranked_contexts,
        )
        source_map = build_source_map(ranked_contexts)
        documents = sorted({context.document_id for context in ranked_contexts})
        metadata = {
            "corpus_scope": "alliance_documents",
            "parent_contexts_received": len(parent_contexts),
            "candidate_parent_contexts": len(candidates),
            "final_context_top_k": self.final_context_top_k,
            "effective_final_context_top_k": effective_final_context_top_k,
            "query_intent": query_intent,
            "query_is_doctrinal": query_is_doctrinal,
            "query_is_normative": query_is_normative,
            "contexts_fused_by_parent_key": sum(max(0, len(group) - 1) for group in grouped_contexts.values()),
            "removed_contexts": removal_metadata,
            "deduplication": dedupe_metadata,
            "document_diversity": diversity_metadata,
            "char_limits": limit_metadata,
            "retrieval_candidates": retrieval_candidates,
            "ordering_heuristic": (
                "ranking_score = best_anchor_score + content_priority_bonus + expanded_bonus "
                "- introductory_penalty - anchor_only_penalty"
            ),
        }
        return RetrievalContextPackage(
            query=query,
            contexts=ranked_contexts,
            context_count=len(ranked_contexts),
            total_context_chars=sum(context.context_char_count for context in ranked_contexts),
            documents=documents,
            source_map=source_map,
            retrieval_stages=[
                "vector_retrieval",
                "bm25_retrieval",
                "reciprocal_rank_fusion",
                "hybrid_retrieval",
                "cross_encoder_reranking",
                "hierarchical_retrieval",
                "context_consolidation",
                "final_context_package",
            ],
            filters=merged_filters,
            metadata=metadata,
        )

    def _group_contexts(self, contexts: list[ParentContext]) -> dict[str, list[ParentContext]]:
        grouped: dict[str, list[ParentContext]] = defaultdict(list)
        for index, context in enumerate(contexts):
            key = context.parent_key if self.consolidate_by_parent_key else f"{context.parent_key}::{index}"
            grouped[key].append(context)
        return dict(grouped)

    def _build_final_context(
        self,
        query: str,
        contexts: list[ParentContext],
        parent_key: str,
        query_is_doctrinal: bool,
        query_is_normative: bool,
    ) -> FinalContext:
        ordered_contexts = sorted(contexts, key=_parent_context_sort_key, reverse=True)
        base = ordered_contexts[0]
        anchor_chunk_ids = _unique([context.anchor_chunk_id for context in ordered_contexts])
        anchor_scores = [context.anchor_score for context in ordered_contexts]
        included_chunk_ids = _unique(
            chunk_id for context in ordered_contexts for chunk_id in context.included_chunk_ids
        )
        source_paths = _unique(
            value
            for context in ordered_contexts
            for value in [
                str(context.metadata.get("source_path") or ""),
                str(context.anchor_result.source_path if context.anchor_result else ""),
            ]
            if value
        )
        page_start = _min_nullable(context.page_start for context in ordered_contexts)
        page_end = _max_nullable(context.page_end for context in ordered_contexts)
        content_priority = _content_priority(ordered_contexts)
        best_score = _best_score(ordered_contexts)
        statuses = [context.parent_expansion_status for context in ordered_contexts]
        context_status = "expanded" if any("expanded" in status for status in statuses) else "anchor_only"
        if len(ordered_contexts) > 1:
            context_status = f"{context_status}_consolidated"

        context_char_limit = self._context_char_limit(ordered_contexts)
        context_text, truncated = _truncate_context(
            base.context_text,
            context_char_limit,
        )
        ranking_score = _ranking_score(
            best_score=best_score,
            content_priority=content_priority,
            context_status=context_status,
            query_is_doctrinal=query_is_doctrinal,
            query_is_normative=query_is_normative,
        )
        metadata = {
            "corpus_id": base.metadata.get("corpus_id"),
            "retrieval_namespace": base.metadata.get("retrieval_namespace"),
            "document_title": base.metadata.get("document_title") or base.anchor_document,
            "document_type": base.metadata.get("document_type"),
            "source_category": base.metadata.get("source_category"),
            "denomination": base.metadata.get("denomination"),
            "tradition": base.metadata.get("tradition"),
            "full_reference": base.metadata.get("full_reference"),
            "document_structure_type": base.metadata.get("document_structure_type"),
            "parent_context_count": len(ordered_contexts),
            "source_parent_keys": [context.parent_key for context in ordered_contexts],
            "source_parent_strategies": [context.parent_strategy for context in ordered_contexts],
            "original_expansion_statuses": statuses,
            "anchor_chunk_types": [
                context.anchor_result.chunk_type
                for context in ordered_contexts
                if context.anchor_result is not None
            ],
            "included_chunks": _included_chunk_metadata(ordered_contexts),
            "best_anchor_score": best_score,
            "ranking_score": ranking_score,
            "context_truncated": truncated,
            "context_char_limit": context_char_limit,
            "consolidation_decision": (
                "merged_by_parent_key" if len(ordered_contexts) > 1 else "single_parent_context"
            ),
            "anchor_only_handling": None,
            "introductory_handling": None,
        }
        return FinalContext(
            query=query,
            rank=0,
            parent_key=parent_key,
            parent_title=base.parent_title,
            document_id=base.anchor_document_id,
            document=base.anchor_document,
            context_text=context_text,
            context_char_count=len(context_text),
            included_chunk_ids=included_chunk_ids,
            anchor_chunk_ids=anchor_chunk_ids,
            anchor_scores=anchor_scores,
            page_start=page_start,
            page_end=page_end,
            source_paths=source_paths,
            context_status=context_status,
            content_priority=content_priority,
            metadata=metadata,
        )

    def _remove_introductory_anchor_only(
        self,
        contexts: list[FinalContext],
        query_is_doctrinal: bool,
    ) -> tuple[list[FinalContext], dict[str, Any]]:
        if not self.reduce_introductory_context_for_doctrinal_queries or not query_is_doctrinal:
            return contexts, {"removed_introductory_anchor_only": []}

        has_expanded_doctrinal = any(
            context.content_priority == "doctrinal" and "expanded" in context.context_status
            for context in contexts
        )
        removed: list[str] = []
        kept: list[FinalContext] = []
        for context in contexts:
            if (
                has_expanded_doctrinal
                and context.content_priority == "introductory"
                and context.context_status.startswith("anchor_only")
            ):
                removed.append(context.parent_key)
                continue
            kept.append(context)
        return kept, {"removed_introductory_anchor_only": removed}

    def _apply_anchor_only_handling(self, contexts: list[FinalContext]) -> list[FinalContext]:
        has_expanded = any("expanded" in context.context_status for context in contexts)
        updated: list[FinalContext] = []
        for context in contexts:
            metadata = dict(context.metadata)
            if context.context_status.startswith("anchor_only"):
                if has_expanded and self.prefer_expanded_contexts:
                    metadata["anchor_only_handling"] = "deprioritized_due_to_expanded_alternatives"
                    metadata["ranking_score"] -= 1.0
                elif self.keep_anchor_only_when_no_expanded_alternative:
                    metadata["anchor_only_handling"] = "kept_because_no_expanded_alternative"
                else:
                    metadata["anchor_only_handling"] = "kept"
            else:
                metadata["anchor_only_handling"] = "not_anchor_only"
            updated.append(replace(context, metadata=metadata))
        return updated

    def _deduplicate_chunks_across_contexts(
        self,
        contexts: list[FinalContext],
    ) -> tuple[list[FinalContext], dict[str, Any]]:
        if not self.deduplicate_included_chunks:
            return contexts, {"deduplicated_chunk_ids": []}

        seen: set[str] = set()
        deduplicated: list[str] = []
        updated: list[FinalContext] = []
        for context in contexts:
            retained = []
            removed = []
            for chunk_id in context.included_chunk_ids:
                if chunk_id in seen:
                    removed.append(chunk_id)
                    deduplicated.append(chunk_id)
                    continue
                seen.add(chunk_id)
                retained.append(chunk_id)
            metadata = dict(context.metadata)
            metadata["deduplicated_included_chunk_ids"] = removed
            updated.append(replace(context, included_chunk_ids=retained or context.included_chunk_ids, metadata=metadata))
        return updated, {"deduplicated_chunk_ids": deduplicated, "deduplicated_chunk_count": len(deduplicated)}

    def _promote_document_diversity(
        self,
        candidates: list[FinalContext],
        query: str,
        filters: dict[str, Any],
    ) -> tuple[list[FinalContext], dict[str, Any]]:
        """Intercala documentos relevantes quando a consulta não restringe uma fonte."""
        if not self.preserve_document_diversity or len(candidates) <= 1:
            return candidates, {"applied": False, "reason": "disabled_or_single_candidate"}
        if normative_subject_scope_for_query(query) is not None:
            promoted, intradocument_metadata = _promote_intradocument_topic_contexts(
                candidates,
                query,
                max(
                    self.final_context_top_k,
                    normative_subject_scope_context_limit(query) or self.final_context_top_k,
                ),
            )
            if intradocument_metadata["applied"]:
                return promoted, intradocument_metadata
        if filters.get("document_id"):
            promoted, intradocument_metadata = _promote_intradocument_topic_contexts(
                candidates,
                query,
                self.final_context_top_k,
            )
            if intradocument_metadata["applied"]:
                return promoted, intradocument_metadata
            return candidates, {"applied": False, "reason": "document_filter_present"}
        if _query_mentions_specific_document(query):
            return candidates, {"applied": False, "reason": "specific_document_mentioned"}
        if query_requests_institutional_doctrinal_bridge(query):
            scoped_candidates, scope_metadata = _prefer_congregational_institutional_scope(candidates)
            promoted, bridge_metadata = _promote_institutional_doctrinal_bridge(
                scoped_candidates,
                self.final_context_top_k,
                query,
            )
            if bridge_metadata["applied"]:
                bridge_metadata["scope_filter"] = scope_metadata
                return promoted, bridge_metadata
            candidates = scoped_candidates
        if query_requests_document_inventory(query):
            promoted, inventory_metadata = _promote_document_inventory_contexts(
                candidates,
                self.final_context_top_k,
            )
            if inventory_metadata["applied"]:
                return promoted, inventory_metadata
        if _is_overview_query(query) and not _query_requests_document_list(query):
            dominant_overview = next(
                (context for context in candidates if _is_overview_context(context)),
                None,
            )
            if dominant_overview is not None:
                same_document_contexts = [
                    context
                    for context in candidates
                    if context.document_id == dominant_overview.document_id
                ]
                if len(same_document_contexts) > 1:
                    promoted_keys = {context.parent_key for context in same_document_contexts}
                    remainder = [
                        context
                        for context in candidates
                        if context.parent_key not in promoted_keys
                    ]
                    return same_document_contexts + remainder, {
                        "applied": True,
                        "reason": "overview_same_document_contexts_promoted",
                        "promoted_document": dominant_overview.document_id,
                        "promoted_parent_keys": [
                            context.parent_key for context in same_document_contexts
                        ],
                    }

        available_document_ids = _unique(context.document_id for context in candidates)
        topic_matched = [context for context in candidates if _parent_unit_matches_query(context, query)]
        topic_matched_document_ids = _unique(context.document_id for context in topic_matched)
        if len(topic_matched_document_ids) >= 2:
            top_topic_by_document: dict[str, FinalContext] = {}
            for context in topic_matched:
                top_topic_by_document.setdefault(context.document_id, context)

            promoted = sorted(
                top_topic_by_document.values(),
                key=lambda context: _metadata_score(context),
                reverse=True,
            )[: self.final_context_top_k]
            promoted_keys = {context.parent_key for context in promoted}
            remainder = [context for context in candidates if context.parent_key not in promoted_keys]
            return promoted + remainder, {
                "applied": True,
                "reason": "topic_matched_one_context_per_document_promoted",
                "promoted_documents": [context.document_id for context in promoted],
                "available_documents": available_document_ids,
                "topic_matched_documents": topic_matched_document_ids,
                "topic_matched_parent_keys": [context.parent_key for context in topic_matched],
            }

        if topic_matched:
            matched_keys = {context.parent_key for context in topic_matched}
            ordered_topic_matched = sorted(
                topic_matched,
                key=lambda context: (
                    _parent_unit_match_score(context, query),
                    _metadata_score(context),
                ),
                reverse=True,
            )
            candidates = ordered_topic_matched + [
                context for context in candidates if context.parent_key not in matched_keys
            ]

        document_ids = _unique(context.document_id for context in candidates)
        if len(document_ids) <= 1:
            return candidates, {"applied": False, "reason": "single_document_available"}

        best_score = _metadata_score(candidates[0])
        relevance_floor = _diversity_relevance_floor(best_score)
        top_by_document: dict[str, FinalContext] = {}
        for context in candidates:
            if _metadata_score(context) < relevance_floor:
                continue
            if not _parent_unit_matches_query(context, query):
                continue
            top_by_document.setdefault(context.document_id, context)

        if len(top_by_document) <= 1:
            return candidates, {
                "applied": False,
                "reason": "no_relevant_alternative_document",
                "available_documents": document_ids,
                "topic_matched_documents": topic_matched_document_ids,
                "topic_matched_parent_keys": [context.parent_key for context in topic_matched],
            }

        promoted = sorted(
            top_by_document.values(),
            key=lambda context: _metadata_score(context),
            reverse=True,
        )
        max_promoted = min(len(promoted), self.final_context_top_k)
        promoted = promoted[:max_promoted]
        promoted_keys = {context.parent_key for context in promoted}
        remainder = [context for context in candidates if context.parent_key not in promoted_keys]
        reordered = promoted + remainder

        return reordered, {
            "applied": True,
            "reason": "topic_matched_multi_document_context_promoted",
            "promoted_documents": [context.document_id for context in promoted],
            "available_documents": document_ids,
            "topic_matched_documents": topic_matched_document_ids,
            "topic_matched_parent_keys": [context.parent_key for context in topic_matched],
            "relevance_floor": relevance_floor,
        }

    def _apply_limits(
        self,
        contexts: list[FinalContext],
        final_context_top_k: int | None = None,
    ) -> tuple[list[FinalContext], dict[str, Any]]:
        effective_top_k = final_context_top_k or self.final_context_top_k
        selected: list[FinalContext] = []
        total_chars = 0
        dropped_by_limit: list[str] = []
        truncated_by_global_limit: list[str] = []
        for context in contexts:
            if len(selected) >= effective_top_k:
                dropped_by_limit.append(context.parent_key)
                continue
            remaining = self.max_total_context_chars - total_chars
            if remaining <= 0:
                dropped_by_limit.append(context.parent_key)
                continue
            if context.context_char_count > remaining:
                if not selected and remaining > 0:
                    context_text, _ = _truncate_context(context.context_text, remaining)
                    metadata = dict(context.metadata)
                    metadata["global_context_truncated"] = True
                    selected.append(
                        replace(
                            context,
                            context_text=context_text,
                            context_char_count=len(context_text),
                            metadata=metadata,
                        )
                    )
                    total_chars += len(context_text)
                    truncated_by_global_limit.append(context.parent_key)
                else:
                    dropped_by_limit.append(context.parent_key)
                continue
            selected.append(context)
            total_chars += context.context_char_count

        return selected, {
            "final_context_top_k": self.final_context_top_k,
            "effective_final_context_top_k": effective_top_k,
            "max_total_context_chars": self.max_total_context_chars,
            "max_context_chars_per_parent": self.max_context_chars_per_parent,
            "dropped_by_limit": dropped_by_limit,
            "truncated_by_global_limit": truncated_by_global_limit,
        }

    @staticmethod
    def _merge_filters(filters: dict[str, Any] | None) -> dict[str, Any]:
        merged = dict(DEFAULT_FILTERS)
        for key, value in (filters or {}).items():
            if value is None:
                continue
            if key in DEFAULT_FILTERS and value != DEFAULT_FILTERS[key]:
                continue
            merged[key] = value
        return merged

    def _context_char_limit(self, contexts: list[ParentContext]) -> int:
        has_expanded_long_context = any(
            context.parent_strategy in {"overview_structural_group", "normative_unit_list"}
            for context in contexts
        )
        if not has_expanded_long_context:
            return self.max_context_chars_per_parent
        return max(
            self.max_context_chars_per_parent,
            min(self.max_total_context_chars, int(self.max_context_chars_per_parent * 1.5)),
        )


def classify_query_intent(query: str) -> str:
    """Classifica pergunta em escopo doutrinário, normativo, misto ou geral."""
    terms = _query_terms(query)
    doctrinal_terms = terms & DOCTRINAL_TERMS
    normative_terms = terms & NORMATIVE_TERMS
    normative_terms_without_scope = normative_terms - DENOMINATIONAL_SCOPE_TERMS
    has_doctrinal = bool(doctrinal_terms)
    has_normative = bool(normative_terms_without_scope)
    if has_doctrinal and has_normative:
        return "mixed"
    if has_normative:
        return "normative"
    if has_doctrinal:
        return "doctrinal"
    if normative_terms:
        return "normative"
    return "general"


def query_mentions_doctrinal_terms(query: str) -> bool:
    """Identifica presença explícita de vocabulário doutrinário na consulta."""
    return bool(_query_terms(query) & DOCTRINAL_TERMS)


def is_doctrinal_query(query: str) -> bool:
    """Compatibilidade para chamadas antigas que esperam booleano."""
    return classify_query_intent(query) in {"doctrinal", "mixed"}


def query_mentions_denominational_scope(query: str) -> bool:
    """Identifica quando a pergunta restringe o escopo à Aliança como denominação."""
    return bool(_query_terms(query) & DENOMINATIONAL_SCOPE_TERMS)


def query_requests_document_inventory(query: str) -> bool:
    """Detecta perguntas que pedem lista de documentos/fontes/normas orientadoras."""
    normalized = _normalize_ascii(query)
    return bool(
        re.search(r"\bquais\s+(?:sao\s+)?(?:documentos|fontes|normas)\b", normalized)
        or re.search(r"\b(?:documentos|fontes|normas)\s+.+\b(?:orientam|regem|disciplinam|tratam)\b", normalized)
    )


def query_requests_institutional_doctrinal_bridge(query: str) -> bool:
    """Detecta perguntas que pedem relação entre doutrina congregacional e normas institucionais."""
    terms = _query_terms(query)
    has_scope = bool(terms & CONGREGATIONAL_SCOPE_TERMS)
    has_doctrinal_layer = bool(terms & DOCTRINAL_BRIDGE_TERMS)
    has_institutional_layer = bool(terms & INSTITUTIONAL_TERMS)
    return has_scope and has_doctrinal_layer and has_institutional_layer


def _query_terms(query: str) -> set[str]:
    normalized = _normalize_ascii(query)
    return set(re.findall(r"[\wÀ-ÿ]+", normalized))


def build_source_map(contexts: list[FinalContext]) -> dict[str, dict[str, Any]]:
    """Monta mapa de fontes rastreáveis para o pacote final."""
    source_map: dict[str, dict[str, Any]] = {}
    for index, context in enumerate(contexts, start=1):
        source_map[f"source_{index}"] = {
            "context_index": index,
            "final_rank": context.rank or index,
            "document": context.document,
            "document_id": context.document_id,
            "document_title": context.metadata.get("document_title") or context.document,
            "document_type": context.metadata.get("document_type"),
            "source_category": context.metadata.get("source_category"),
            "denomination": context.metadata.get("denomination"),
            "tradition": context.metadata.get("tradition"),
            "parent_key": context.parent_key,
            "parent_title": context.parent_title,
            "full_reference": context.metadata.get("full_reference") or _first_included_value(context, "full_reference"),
            "document_structure_type": context.metadata.get("document_structure_type"),
            "content_priority": context.content_priority,
            "pages": _format_pages(context.page_start, context.page_end),
            "anchor_chunk_id": _first_value(context.anchor_chunk_ids),
            "anchor_chunk_ids": context.anchor_chunk_ids,
            "included_chunk_ids": context.included_chunk_ids,
            "score": context.metadata.get("best_anchor_score"),
            "ranking_score": context.metadata.get("ranking_score"),
            "selected_for_prompt": True,
            "source_paths": context.source_paths,
        }
    return source_map


def build_retrieval_candidates(
    parent_contexts: list[ParentContext],
    final_candidates: list[FinalContext],
    selected_contexts: list[FinalContext],
) -> list[dict[str, Any]]:
    """Serializa candidatos âncora disponíveis antes da seleção final do prompt."""
    final_by_parent_key = {context.parent_key: context for context in final_candidates}
    selected_by_parent_key = {context.parent_key: context for context in selected_contexts}
    candidates: list[dict[str, Any]] = []
    for candidate_rank, context in enumerate(parent_contexts, start=1):
        result = context.anchor_result
        metadata = dict(result.metadata) if result is not None else {}
        final_context = final_by_parent_key.get(context.parent_key)
        selected_context = selected_by_parent_key.get(context.parent_key)
        score_details = _candidate_score_details(metadata)
        candidates.append(
            {
                "candidate_rank": candidate_rank,
                "final_rank": selected_context.rank if selected_context is not None else None,
                "chunk_id": context.anchor_chunk_id,
                "document_id": context.anchor_document_id,
                "document_title": (
                    metadata.get("document_title")
                    or metadata.get("document")
                    or context.anchor_document
                ),
                "parent_key": context.parent_key,
                "parent_title": context.parent_title,
                "page": _format_pages(context.page_start, context.page_end),
                "dense_score": score_details.get("dense_score"),
                "bm25_score": score_details.get("bm25_score"),
                "rrf_score": score_details.get("rrf_score"),
                "rerank_score": score_details.get("rerank_score"),
                "ranking_score": (
                    final_context.metadata.get("ranking_score")
                    if final_context is not None
                    else None
                ),
                "selected_for_prompt": selected_context is not None,
                "context_status": context.parent_expansion_status,
                "included_chunk_ids": context.included_chunk_ids,
                "retrieval_sources": metadata.get("retrieval_sources")
                or metadata.get("pre_rerank_sources")
                or [],
            }
        )
    return candidates


def _candidate_score_details(metadata: dict[str, Any]) -> dict[str, Any]:
    details = {
        "dense_score": metadata.get("vector_score"),
        "bm25_score": metadata.get("bm25_score"),
        "rrf_score": metadata.get("rrf_score") or metadata.get("pre_rerank_score"),
        "rerank_score": metadata.get("reranker_score"),
    }
    rankings = metadata.get("source_rankings")
    if isinstance(rankings, list):
        for ranking in rankings:
            if not isinstance(ranking, dict):
                continue
            source = str(ranking.get("source") or "")
            original_score = ranking.get("original_score")
            if source in {"vector", "dense"} and details["dense_score"] is None:
                details["dense_score"] = original_score
            if source == "bm25" and details["bm25_score"] is None:
                details["bm25_score"] = original_score
    return details


def _parent_context_sort_key(context: ParentContext) -> tuple[float, int, int]:
    score = context.anchor_score if context.anchor_score is not None else float("-inf")
    expanded = 1 if context.parent_expansion_status == "expanded" else 0
    doctrinal = 1 if _anchor_chunk_type(context) in DOCTRINAL_CHUNK_TYPES else 0
    return score, expanded, doctrinal


def _content_priority(contexts: list[ParentContext]) -> str:
    chunk_types = {_anchor_chunk_type(context) for context in contexts}
    metadatas = [
        context.anchor_result.metadata
        for context in contexts
        if context.anchor_result is not None
    ]
    document_types = {str(metadata.get("document_type") or "") for metadata in metadatas}
    source_categories = {str(metadata.get("source_category") or "") for metadata in metadatas}
    content_roles = {str(metadata.get("content_role") or "") for metadata in metadatas}
    if (
        chunk_types & DOCTRINAL_CHUNK_TYPES
        or document_types & DOCTRINAL_DOCUMENT_TYPES
        or "doctrinal_document" in source_categories
        or "doctrinal" in content_roles
    ):
        return "doctrinal"
    if (
        document_types & NORMATIVE_DOCUMENT_TYPES
        or "denominational_normative_document" in source_categories
        or "normative" in content_roles
    ):
        return "normative"
    if chunk_types & INTRODUCTORY_CHUNK_TYPES:
        return "introductory"
    return "contextual"


def _included_chunk_metadata(contexts: list[ParentContext]) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    seen: set[str] = set()
    for context in contexts:
        raw_chunks = context.metadata.get("included_chunks")
        if not isinstance(raw_chunks, list):
            continue
        for chunk in raw_chunks:
            if not isinstance(chunk, dict):
                continue
            chunk_id = str(chunk.get("chunk_id") or "")
            if not chunk_id or chunk_id in seen:
                continue
            seen.add(chunk_id)
            chunks.append(dict(chunk))
    return chunks


def _first_included_value(context: FinalContext, key: str) -> Any | None:
    chunks = context.metadata.get("included_chunks")
    if not isinstance(chunks, list):
        return None
    for chunk in chunks:
        if not isinstance(chunk, dict):
            continue
        value = chunk.get(key)
        if value not in (None, ""):
            return value
    return None


def _anchor_chunk_type(context: ParentContext) -> str | None:
    if context.anchor_result is None:
        return None
    return context.anchor_result.chunk_type


def _best_score(contexts: list[ParentContext]) -> float | None:
    scores = [context.anchor_score for context in contexts if context.anchor_score is not None]
    return max(scores) if scores else None


def _ranking_score(
    best_score: float | None,
    content_priority: str,
    context_status: str,
    query_is_doctrinal: bool,
    query_is_normative: bool,
) -> float:
    score = best_score if best_score is not None else 0.0
    if "expanded" in context_status:
        score += 0.75
    if content_priority == "doctrinal":
        score += 0.5
    if content_priority == "normative":
        score += 0.45
    if query_is_normative and content_priority == "normative":
        score += 0.7
    if query_is_doctrinal and content_priority == "doctrinal":
        score += 0.7
    if query_is_doctrinal and content_priority == "introductory":
        score -= 2.0
    if context_status.startswith("anchor_only"):
        score -= 0.5
    return score


def _metadata_score(context: FinalContext) -> float:
    value = context.metadata.get("ranking_score", 0.0)
    return float(value if value is not None else 0.0)


def _promote_intradocument_topic_contexts(
    candidates: list[FinalContext],
    query: str,
    final_context_top_k: int,
) -> tuple[list[FinalContext], dict[str, Any]]:
    """Reordena unidades do mesmo documento quando a pergunta mira uma subunidade específica."""
    normative_scope = _normative_subject_scope_for_query(query)
    if normative_scope:
        scoped = [
            context
            for context in candidates
            if _context_matches_normative_subject_scope(context, normative_scope)
        ]
        if scoped:
            ordered_scoped = sorted(
                scoped,
                key=lambda context: (
                    _normative_subject_scope_context_priority(context, normative_scope),
                    _parent_unit_match_score(context, query),
                    _metadata_score(context),
                ),
                reverse=True,
            )
            removed = [
                context
                for context in candidates
                if context.parent_key not in {item.parent_key for item in ordered_scoped}
            ]
            return ordered_scoped, {
                "applied": True,
                "reason": "normative_subject_scope_filtered",
                "scope_id": normative_scope["id"],
                "subject": normative_scope["subject"],
                "intent": normative_scope["intent"],
                "promoted_parent_keys": [context.parent_key for context in ordered_scoped],
                "removed_parent_keys": [context.parent_key for context in removed],
                "removed_references": [
                    context.metadata.get("full_reference") or context.parent_title or context.parent_key
                    for context in removed
                ],
            }

    topic_matched = [context for context in candidates if _parent_unit_matches_query(context, query)]
    if not topic_matched:
        return candidates, {"applied": False, "reason": "no_intradocument_topic_match"}

    ordered_topic_matched = sorted(
        topic_matched,
        key=lambda context: (
            _parent_unit_match_score(context, query),
            _metadata_score(context),
        ),
        reverse=True,
    )[:final_context_top_k]
    promoted_keys = {context.parent_key for context in ordered_topic_matched}
    remainder = [context for context in candidates if context.parent_key not in promoted_keys]
    return ordered_topic_matched + remainder, {
        "applied": True,
        "reason": "intradocument_topic_contexts_promoted",
        "promoted_parent_keys": [context.parent_key for context in ordered_topic_matched],
        "topic_match_scores": {
            context.parent_key: _parent_unit_match_score(context, query)
            for context in ordered_topic_matched
        },
    }


def _prefer_congregational_institutional_scope(
    candidates: list[FinalContext],
) -> tuple[list[FinalContext], dict[str, Any]]:
    scoped = [context for context in candidates if _is_congregational_institutional_context(context)]
    suppressed = [
        context
        for context in candidates
        if context.content_priority == "doctrinal" and context not in scoped
    ]
    if not scoped or not suppressed:
        return candidates, {"applied": False, "suppressed_documents": []}

    suppressed_keys = {context.parent_key for context in suppressed}
    retained = [context for context in candidates if context.parent_key not in suppressed_keys]
    return retained, {
        "applied": True,
        "suppressed_documents": _unique(context.document_id for context in suppressed),
        "suppressed_parent_keys": [context.parent_key for context in suppressed],
    }


def _promote_institutional_doctrinal_bridge(
    candidates: list[FinalContext],
    final_context_top_k: int,
    query: str,
) -> tuple[list[FinalContext], dict[str, Any]]:
    role_order = (
        "alliance_confession",
        "constitution",
        "internal_regiment",
        "normative_ethics",
        "administrative_resolution",
    )
    promoted = _top_context_by_role(candidates, role_order, final_context_top_k, query=query)
    promoted_roles = [_document_coverage_role(context) for context in promoted]
    has_doctrinal = "alliance_confession" in promoted_roles
    has_normative = any(role in promoted_roles for role in role_order[1:])
    if len(promoted) < 2 or not (has_doctrinal and has_normative):
        return candidates, {
            "applied": False,
            "reason": "insufficient_doctrinal_normative_coverage",
            "available_roles": _unique(_document_coverage_role(context) for context in candidates),
        }

    promoted = _mark_coverage_promoted_contexts(
        promoted,
        reason="institutional_doctrinal_bridge_coverage_promoted",
    )
    promoted_keys = {context.parent_key for context in promoted}
    remainder = [context for context in candidates if context.parent_key not in promoted_keys]
    return promoted + remainder, {
        "applied": True,
        "reason": "institutional_doctrinal_bridge_coverage_promoted",
        "promoted_documents": [context.document_id for context in promoted],
        "promoted_roles": promoted_roles,
        "available_roles": _unique(_document_coverage_role(context) for context in candidates),
    }


def _promote_document_inventory_contexts(
    candidates: list[FinalContext],
    final_context_top_k: int,
) -> tuple[list[FinalContext], dict[str, Any]]:
    role_order = (
        "document_inventory",
        "alliance_confession",
        "normative_ethics",
        "constitution",
        "internal_regiment",
        "administrative_resolution",
    )
    promoted = _top_context_by_role(candidates, role_order, final_context_top_k)
    promoted_roles = [_document_coverage_role(context) for context in promoted]
    if len(promoted) < 2:
        return candidates, {
            "applied": False,
            "reason": "insufficient_document_inventory_coverage",
            "available_roles": _unique(_document_coverage_role(context) for context in candidates),
        }

    promoted = _mark_coverage_promoted_contexts(
        promoted,
        reason="document_inventory_coverage_promoted",
    )
    promoted_keys = {context.parent_key for context in promoted}
    remainder = [context for context in candidates if context.parent_key not in promoted_keys]
    return promoted + remainder, {
        "applied": True,
        "reason": "document_inventory_coverage_promoted",
        "promoted_documents": [context.document_id for context in promoted],
        "promoted_roles": promoted_roles,
        "available_roles": _unique(_document_coverage_role(context) for context in candidates),
    }


def _top_context_by_role(
    candidates: list[FinalContext],
    role_order: tuple[str, ...],
    final_context_top_k: int,
    query: str | None = None,
) -> list[FinalContext]:
    promoted: list[FinalContext] = []
    used_parent_keys: set[str] = set()
    used_document_ids: set[str] = set()
    for role in role_order:
        role_candidates = [
            context
            for context in candidates
            if context.parent_key not in used_parent_keys
            and context.document_id not in used_document_ids
            and _context_matches_coverage_role(context, role)
        ]
        if not role_candidates:
            continue
        best = max(
            role_candidates,
            key=lambda context: (
                _institutional_bridge_match_score(context) if query else 0,
                1 if query and _parent_unit_matches_query(context, query) else 0,
                _document_inventory_term_count(context),
                _metadata_score(context),
            ),
        )
        promoted.append(best)
        used_parent_keys.add(best.parent_key)
        used_document_ids.add(best.document_id)
        if len(promoted) >= final_context_top_k:
            break
    return promoted


def _context_matches_coverage_role(context: FinalContext, role: str) -> bool:
    if _document_coverage_role(context) == role:
        return True
    document_type = str(context.metadata.get("document_type") or "")
    if role == "constitution":
        return document_type == "constitution"
    if role == "internal_regiment":
        return document_type == "internal_regiment"
    if role == "normative_ethics":
        return document_type == "normative_ethics"
    if role == "administrative_resolution":
        return document_type == "administrative_resolution"
    return False


def _mark_coverage_promoted_contexts(
    contexts: list[FinalContext],
    reason: str,
    max_chars: int = 4200,
) -> list[FinalContext]:
    promoted: list[FinalContext] = []
    for context in contexts:
        role = _document_coverage_role(context)
        context_text = context.context_text
        truncated = False
        if context.context_char_count > max_chars:
            context_text, truncated = _truncate_context(context.context_text, max_chars)
        metadata = dict(context.metadata)
        metadata["coverage_promoted"] = reason
        metadata["coverage_role"] = role
        metadata["coverage_context_truncated"] = truncated
        promoted.append(
            replace(
                context,
                context_text=context_text,
                context_char_count=len(context_text),
                metadata=metadata,
            )
        )
    return promoted


def _document_coverage_role(context: FinalContext) -> str:
    if _document_inventory_term_count(context) >= 3:
        return "document_inventory"

    document_id = str(context.document_id or "")
    document_type = str(context.metadata.get("document_type") or "")
    source_category = str(context.metadata.get("source_category") or "")

    if document_id == "confissao-fe-congregacional-alianca":
        return "alliance_confession"
    if document_type == "constitution":
        return "constitution"
    if document_type == "internal_regiment":
        return "internal_regiment"
    if document_type == "normative_ethics":
        return "normative_ethics"
    if document_type == "administrative_resolution":
        return "administrative_resolution"
    if source_category == "denominational_normative_document":
        return "other_normative"
    if context.content_priority == "doctrinal":
        return "other_doctrinal"
    return "other"


def _institutional_bridge_match_score(context: FinalContext) -> int:
    text = _normalize_ascii(
        " ".join(
            [
                context.parent_title,
                context.document,
                str(context.metadata.get("document_title") or ""),
                context.context_text[:3000],
            ]
        )
    )
    weighted_patterns = (
        (r"\bigrejas?\b", 3),
        (r"\bgoverno\b", 3),
        (r"\bordem\b", 3),
        (r"\binstituicao\b", 3),
        (r"\binstitucional\b", 2),
        (r"\binstitucionais\b", 2),
        (r"\bnormas?\b", 2),
        (r"\bpalavra\b", 1),
        (r"\bescrituras?\b", 1),
        (r"\bdoutrina\b", 1),
    )
    return sum(weight for pattern, weight in weighted_patterns if re.search(pattern, text))


def _is_congregational_institutional_context(context: FinalContext) -> bool:
    document_id = str(context.document_id or "")
    if document_id == "confissao-fe-congregacional-alianca":
        return True
    metadata_text = _normalize_ascii(
        " ".join(
            str(value or "")
            for value in (
                context.document,
                context.metadata.get("document_title"),
                context.metadata.get("source_category"),
                context.metadata.get("denomination"),
                context.metadata.get("tradition"),
            )
        )
    )
    return (
        "alianca" in metadata_text
        or "congregacional" in metadata_text
        or context.metadata.get("source_category") == "denominational_normative_document"
    )


def _document_inventory_term_count(context: FinalContext) -> int:
    text = _normalize_ascii(
        " ".join(
            [
                context.document,
                str(context.metadata.get("document_title") or ""),
                context.parent_title,
                context.context_text[:4000],
            ]
        )
    )
    patterns = (
        r"\bconstituicao\b",
        r"\bregimento\b",
        r"\bconfissao\b",
        r"\bcodigo\b",
        r"\betica\b",
        r"\bdecisoes?\b",
        r"\bconciliares?\b",
        r"\bresolucoes?\b",
        r"\bdiretoria\s+nacional\b",
    )
    return sum(1 for pattern in patterns if re.search(pattern, text))


def _diversity_relevance_floor(best_score: float) -> float:
    if best_score <= 0:
        return best_score - 1.0
    return best_score - max(1.5, abs(best_score) * 0.35)


def _query_mentions_specific_document(query: str) -> bool:
    normalized = _normalize_ascii(query)
    terms = set(re.findall(r"[\wÀ-ÿ]+", normalized))
    if "congregacional" in terms and {"confissao", "fe"} & terms:
        return True
    return bool(terms & SPECIFIC_DOCUMENT_TERMS)


def _is_overview_query(query: str) -> bool:
    normalized = _normalize_ascii(query)
    patterns = (
        r"\bquais\s+(?:sao\s+)?(?:responsabilidades|deveres|regras|orientacoes|requisitos)\b",
        r"\bo\s+que\s+.+\b(?:diz|ensina|trata|orienta|estabelece)\b",
        r"\bcomo\s+.+\b(?:trata|orienta|explica|regula|estabelece)\b",
        r"\b(?:resuma|liste|sintetize|explique)\b",
    )
    return any(re.search(pattern, normalized) for pattern in patterns)


def _query_requests_document_list(query: str) -> bool:
    normalized = _normalize_ascii(query)
    return bool(
        re.search(r"\bquais\s+(?:sao\s+)?(?:documentos|fontes)\b", normalized)
        or re.search(r"\b(?:compare|comparar|comparacao|relacionam)\b", normalized)
    )


def _is_overview_context(context: FinalContext) -> bool:
    strategies = context.metadata.get("source_parent_strategies")
    if not isinstance(strategies, list):
        return False
    return "overview_structural_group" in {str(strategy) for strategy in strategies}


def _parent_unit_matches_query(context: FinalContext, query: str) -> bool:
    return _parent_unit_match_score(context, query) > 0


def _parent_unit_match_score(context: FinalContext, query: str) -> int:
    query_terms = _topic_terms(query)
    if not query_terms:
        return 1
    parent_text = _parent_unit_search_text(context)
    parent_terms = _topic_terms(parent_text)
    lexical_score = len(query_terms & parent_terms)
    subject_score = _normative_subject_match_score(query, parent_text)
    return lexical_score + subject_score


def _parent_unit_search_text(context: FinalContext) -> str:
    included_chunks = context.metadata.get("included_chunks")
    included_text = ""
    if isinstance(included_chunks, list):
        included_text = " ".join(
            " ".join(
                str(chunk.get(key) or "")
                for key in (
                    "document_title",
                    "chapter_title",
                    "section_title",
                    "subsection_title",
                    "full_reference",
                    "chunk_type",
                    "text",
                )
            )
            for chunk in included_chunks
            if isinstance(chunk, dict)
        )

    return " ".join(
        [
            str(context.parent_title or ""),
            str(context.parent_key or ""),
            str(context.document or ""),
            str(context.metadata.get("document_title") or ""),
            str(context.metadata.get("full_reference") or ""),
            str(context.metadata.get("document_type") or ""),
            str(context.metadata.get("source_category") or ""),
            str(context.context_text[:2000] or ""),
            included_text[:4000],
        ]
    )


def _normative_subject_match_score(query: str, parent_text: str) -> int:
    scope = _normative_subject_scope_for_query(query)
    if scope is None:
        return 0
    normalized_text = _normalize_ascii(parent_text)
    score = 0

    for pattern in scope.get("positive_context_patterns", ()):
        if re.search(pattern, normalized_text):
            score += 4
    for pattern in scope.get("negative_context_patterns", ()):
        if re.search(pattern, normalized_text):
            score -= 3

    return score


def _normative_subject_scope_for_query(query: str) -> dict[str, Any] | None:
    normalized_query = _normalize_ascii(query)
    if not normalized_query:
        return None

    matching_rules: list[dict[str, Any]] = []
    for rule in NORMATIVE_SUBJECT_SCOPE_RULES:
        subject_aliases = tuple(_normalize_ascii(alias) for alias in rule.get("subject_aliases", ()))
        intent_aliases = tuple(_normalize_ascii(alias) for alias in rule.get("intent_aliases", ()))
        if not _contains_any_scope_alias(normalized_query, subject_aliases):
            continue
        if not _contains_any_scope_alias(normalized_query, intent_aliases):
            continue
        matching_rules.append(rule)

    if len(matching_rules) != 1:
        return None
    return matching_rules[0]


def normative_subject_scope_for_query(query: str) -> dict[str, Any] | None:
    """Retorna a regra de escopo normativo aplicável à pergunta, se houver."""
    return _normative_subject_scope_for_query(query)


def normative_subject_scope_context_limit(query: str) -> int | None:
    """Retorna o mínimo de contextos finais necessário para cobrir o escopo."""
    scope = _normative_subject_scope_for_query(query)
    if scope is None:
        return None
    value = scope.get("min_final_contexts")
    if value is None:
        return None
    try:
        return max(1, int(value))
    except (TypeError, ValueError):
        return None


def normative_subject_scope_coverage_query(query: str) -> str:
    """Expande a consulta com termos de cobertura normativa do escopo detectado."""
    scope = _normative_subject_scope_for_query(query)
    if scope is None:
        return query
    terms = str(scope.get("coverage_query_terms") or "").strip()
    return f"{query} {terms}".strip() if terms else query


def normative_subject_scope_framing_chunk_ids(
    query: str,
    document_id: str | None = None,
) -> tuple[str, ...]:
    """Lista chunks de enquadramento que complementam a unidade normativa central."""
    scope = _normative_subject_scope_for_query(query)
    if scope is None:
        return ()

    framing_by_document = scope.get("framing_chunk_ids")
    if not isinstance(framing_by_document, dict):
        return ()

    if document_id:
        chunk_ids = framing_by_document.get(document_id, ())
        return tuple(str(chunk_id) for chunk_id in chunk_ids if chunk_id)

    result: list[str] = []
    for chunk_ids in framing_by_document.values():
        result.extend(str(chunk_id) for chunk_id in chunk_ids if chunk_id)
    return tuple(result)


def _context_matches_normative_subject_scope(
    context: FinalContext,
    scope: dict[str, Any],
) -> bool:
    document_id = str(context.document_id or "")
    allowed_units_by_document = scope.get("allowed_units")
    if not isinstance(allowed_units_by_document, dict):
        return False
    allowed_units = allowed_units_by_document.get(document_id)
    if not allowed_units:
        return False
    return any(_context_matches_normative_unit(context, unit) for unit in allowed_units)


def _normative_subject_scope_context_priority(
    context: FinalContext,
    scope: dict[str, Any],
) -> int:
    allowed_units_by_document = scope.get("allowed_units")
    if not isinstance(allowed_units_by_document, dict):
        return 0
    allowed_units = allowed_units_by_document.get(str(context.document_id or ""), ())
    priorities = [
        int(unit.get("priority") or 0)
        for unit in allowed_units
        if _context_matches_normative_unit(context, unit)
    ]
    return max(priorities) if priorities else 0


def _context_matches_normative_unit(context: FinalContext, unit: dict[str, Any]) -> bool:
    article = _normalize_ascii(str(unit.get("article") or ""))
    paragraph = _normalize_ascii(str(unit.get("paragraph") or ""))
    parent_key = _normalize_ascii(context.parent_key)
    reference = _normalize_ascii(
        " ".join(
            str(value or "")
            for value in (
                context.parent_title,
                context.metadata.get("full_reference"),
            )
        )
    )

    included_chunks = context.metadata.get("included_chunks")
    if isinstance(included_chunks, list):
        for chunk in included_chunks:
            if not isinstance(chunk, dict):
                continue
            article_number = _normalize_ascii(str(chunk.get("article_number") or ""))
            paragraph_number = _normalize_ascii(str(chunk.get("paragraph_number") or ""))
            if article_number != article:
                continue
            if paragraph and paragraph_number != paragraph:
                continue
            if not paragraph and paragraph_number:
                continue
            return True

    if not article:
        return False
    article_pattern = rf"(?:::article::{re.escape(article)}\b|\bart\.?\s*{re.escape(article)}\b)"
    if not (re.search(article_pattern, parent_key) or re.search(article_pattern, reference)):
        return False
    if paragraph:
        paragraph_pattern = rf"(?:::paragraph::{re.escape(paragraph)}\b|\b{re.escape(paragraph)}\b)"
        return bool(re.search(paragraph_pattern, parent_key) or re.search(paragraph_pattern, reference))
    return "::paragraph::" not in parent_key and not re.search(r"\b\d+o\b", reference)


def _contains_any_scope_alias(normalized_text: str, aliases: tuple[str, ...]) -> bool:
    for alias in aliases:
        if not alias:
            continue
        if " " in alias:
            if alias in normalized_text:
                return True
            continue
        if re.search(rf"\b{re.escape(alias)}\b", normalized_text):
            return True
    return False


def _topic_terms(text: str) -> set[str]:
    normalized = _normalize_ascii(text)
    terms = set(re.findall(r"[\wÀ-ÿ]+", normalized))
    stopwords = {
        "para",
        "pela",
        "pelo",
        "como",
        "qual",
        "quais",
        "trata",
        "tratar",
        "significa",
        "significado",
        "responda",
        "explique",
        "sobre",
        "tradicao",
        "reformada",
        "reformado",
        "ensina",
        "ensino",
        "alianca",
        "evangelicas",
        "evangelica",
        "brasil",
        "constituicao",
        "regimento",
        "codigo",
        "acordo",
        "conforme",
        "segundo",
        "documentos",
        "documento",
        "corpus",
        "pergunta",
        "capitulo",
        "chapter",
        "section",
        "secao",
        "confissao",
        "catecismo",
        "canones",
    }
    return {_simple_stem(term) for term in terms if len(term) >= 4 and term not in stopwords}


def _normalize_ascii(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(text or "").lower())
    return normalized.encode("ascii", "ignore").decode("ascii")


def _simple_stem(term: str) -> str:
    if term.endswith("ões"):
        return term[:-3] + "ao"
    if term.endswith("s") and len(term) > 5:
        return term[:-1]
    return term


def _truncate_context(text: str, max_chars: int) -> tuple[str, bool]:
    if max_chars <= 0 or len(text) <= max_chars:
        return text, False
    marker = "\n\n[TRUNCADO POR LIMITE DE CONTEXTO]"
    usable = max(0, max_chars - len(marker))
    return text[:usable].rstrip() + marker, True


def _unique(values) -> list[Any]:
    seen: set[Any] = set()
    result: list[Any] = []
    for value in values:
        if value is None or value == "":
            continue
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _first_value(values) -> Any | None:
    for value in values or []:
        if value not in (None, ""):
            return value
    return None


def _min_nullable(values) -> int | None:
    concrete = [value for value in values if value is not None]
    return min(concrete) if concrete else None


def _max_nullable(values) -> int | None:
    concrete = [value for value in values if value is not None]
    return max(concrete) if concrete else None


def _format_pages(page_start: int | None, page_end: int | None) -> str:
    if page_start is None and page_end is None:
        return "não informado"
    if page_end is None or page_start == page_end:
        return str(page_start)
    return f"{page_start}-{page_end}"
