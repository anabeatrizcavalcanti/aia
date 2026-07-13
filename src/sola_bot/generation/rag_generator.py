"""Gerador RAG com fontes dos documentos da Aliança."""

from __future__ import annotations

import os
import re
import unicodedata
from typing import Any

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None

from sola_bot.generation.citation_formatter import (
    citation_metadata,
    citations_from_source_map,
    format_citations,
)
from sola_bot.generation.evidence_policy import (
    DEFAULT_REFUSAL_MESSAGE,
    EvidenceDecision,
    EvidencePolicy,
    build_evidence_refusal,
)
from sola_bot.generation.prompt_builder import build_rag_prompt
from sola_bot.generation.rag_answer import Citation, RagAnswer
from sola_bot.retrieval.retrieval_pipeline import RetrievalPipeline


DEFAULT_CHAT_MODEL = "gpt-5.4-mini"


class RagGenerator:
    """Orquestra retrieval, política de evidência, prompt e geração OpenAI."""

    def __init__(
        self,
        model: str | None = None,
        temperature: float = 0.1,
        max_output_tokens: int = 1200,
        retrieval_pipeline: RetrievalPipeline | None = None,
        evidence_policy: EvidencePolicy | None = None,
        client: Any | None = None,
    ) -> None:
        if load_dotenv is not None:
            load_dotenv()
        self.model = model or os.getenv("OPENAI_CHAT_MODEL") or DEFAULT_CHAT_MODEL
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.retrieval_pipeline = retrieval_pipeline or RetrievalPipeline()
        self.evidence_policy = evidence_policy or EvidencePolicy()
        self.client = client

    def answer(
        self,
        query: str,
        filters: dict[str, Any] | None = None,
    ) -> RagAnswer:
        """Gera resposta ou recusa a partir de evidência documental."""
        try:
            context_package = self.retrieval_pipeline.retrieve(query=query, filters=filters)
        except Exception as exc:
            return RagAnswer(
                query=query,
                answer="",
                status="error",
                used_context_count=0,
                used_documents=[],
                used_sources=[],
                citations=[],
                refusal_reason=None,
                model=self.model,
                metadata={"retrieval_error": f"{type(exc).__name__}: {exc}"},
            )

        citations = citations_from_source_map(context_package)
        decision = self.evidence_policy.evaluate(context_package)
        if not decision.can_answer:
            return self._refused_answer(query, context_package, citations, decision)

        prompt = build_rag_prompt(query=query, context_package=context_package, citations=citations)
        try:
            response_text = self._call_openai(prompt)
        except Exception as exc:
            return RagAnswer(
                query=query,
                answer="",
                status="error",
                used_context_count=context_package.context_count,
                used_documents=context_package.documents,
                used_sources=[citation.source_id for citation in citations],
                citations=citations,
                refusal_reason=None,
                model=self.model,
                metadata={
                    "openai_error": f"{type(exc).__name__}: {exc}",
                    "evidence_decision": decision.to_dict(),
                    "retrieval_package": context_package.to_dict(),
                    "citations": citation_metadata(citations),
                },
            )
        response_text = polish_generated_answer(response_text, citations)
        response_text, citations = compact_cited_sources(response_text, citations)

        return RagAnswer(
            query=query,
            answer=response_text,
            status="answered",
            used_context_count=context_package.context_count,
            used_documents=documents_from_citations(citations, context_package.documents),
            used_sources=[citation.source_id for citation in citations],
            citations=citations,
            refusal_reason=None,
            model=self.model,
            metadata={
                "provider": "openai",
                "temperature": self.temperature,
                "max_output_tokens": self.max_output_tokens,
                "prompt_char_count": len(prompt),
                "evidence_decision": decision.to_dict(),
                "retrieval_package": context_package.to_dict(),
                "citations": citation_metadata(citations),
                "formatted_citations": format_citations(citations),
            },
        )

    def _call_openai(self, prompt: str) -> str:
        client = self._client()
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Você responde somente com base nos contextos documentais fornecidos. "
                        "O corpus contém documentos doutrinários/confessionais e documentos "
                        "normativos, regimentais, éticos e administrativos da Aliança das "
                        "Igrejas Evangélicas Congregacionais do Brasil. "
                        "Use apenas português com alfabeto latino e pontuação comum; "
                        "não use hebraico, grego ou caracteres de línguas originais. "
                        "Organize a resposta com parágrafos curtos e cite, no próprio texto, "
                        "cada fonte documental efetivamente usada. Separe mudanças de tópico, "
                        "documento, norma ou aspecto doutrinário com uma linha em branco."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=self.temperature,
            max_completion_tokens=self.max_output_tokens,
        )
        content = response.choices[0].message.content
        if isinstance(content, str):
            return content.strip()
        return str(content).strip()

    def _client(self) -> Any:
        if self.client is not None:
            return self.client
        if OpenAI is None:
            raise RuntimeError("Pacote openai não está instalado.")
        if not os.getenv("OPENAI_API_KEY", "").strip():
            raise RuntimeError("OPENAI_API_KEY não está configurada.")
        self.client = OpenAI()
        return self.client

    def _refused_answer(
        self,
        query: str,
        context_package,
        citations,
        decision: EvidenceDecision,
    ) -> RagAnswer:
        return RagAnswer(
            query=query,
            answer=build_evidence_refusal("alliance") or DEFAULT_REFUSAL_MESSAGE,
            status="refused",
            used_context_count=context_package.context_count,
            used_documents=context_package.documents,
            used_sources=[citation.source_id for citation in citations],
            citations=citations,
            refusal_reason=decision.reason,
            model=self.model,
            metadata={
                "evidence_decision": decision.to_dict(),
                "retrieval_package": context_package.to_dict(),
                "citations": citation_metadata(citations),
                "openai_called": False,
            },
)


def compact_cited_sources(text: str, citations: list[Citation]) -> tuple[str, list[Citation]]:
    """Mantém apenas fontes citadas e renumera marcadores para uma sequência contínua."""
    if not text or not citations:
        return text, citations

    citation_numbers: list[int] = []
    seen_numbers: set[int] = set()
    for match in re.finditer(r"\[(\d+)\]", text):
        number = int(match.group(1))
        if number < 1 or number > len(citations) or number in seen_numbers:
            continue
        seen_numbers.add(number)
        citation_numbers.append(number)

    if not citation_numbers:
        return text, citations

    display_numbers = {source_number: index for index, source_number in enumerate(citation_numbers, start=1)}

    def replace_marker(match: re.Match[str]) -> str:
        source_number = int(match.group(1))
        display_number = display_numbers.get(source_number)
        if display_number is None:
            return match.group(0)
        return f"[{display_number}]"

    compacted_text = re.sub(r"\[(\d+)\]", replace_marker, text)
    compacted_citations = [citations[number - 1] for number in citation_numbers]
    return compacted_text, compacted_citations


def documents_from_citations(citations: list[Citation], fallback: list[str]) -> list[str]:
    """Deriva documentos usados das citações efetivamente exibidas."""
    documents: list[str] = []
    seen: set[str] = set()
    for citation in citations:
        document = str(getattr(citation, "document_id", "") or getattr(citation, "document", "")).strip()
        if not document or document in seen:
            continue
        seen.add(document)
        documents.append(document)
    return documents or fallback


def polish_generated_answer(text: str, citations) -> str:
    """Ajusta vícios de redação sem alterar a base doutrinária da resposta."""
    if not text:
        return text

    citation_count = len(citations or [])
    first_document = citations[0].document if citations else ""
    if first_document:
        if citation_count == 1:
            subject_ref = _document_subject_reference(first_document)
            location_ref = _document_location_reference(first_document)
        else:
            subject_ref = "As fontes documentais citadas"
            location_ref = "nas fontes documentais citadas"
        replacements = [
            (r"\bneste documento\b", location_ref),
            (r"\bnesse documento\b", location_ref),
            (r"\bneste texto\b", location_ref),
            (r"\bnesse texto\b", location_ref),
            (r"\bo documento\b", subject_ref),
            (r"\beste documento\b", subject_ref),
            (r"\besse documento\b", subject_ref),
        ]
        for pattern, replacement in replacements:
            text = re.sub(
                pattern,
                lambda match, value=replacement: _match_case_replacement(match.group(0), value),
                text,
                flags=re.IGNORECASE,
            )

    text = re.sub(r"\bessas coisas\b", "esses pontos", text, flags=re.IGNORECASE)
    text = re.sub(r"\bestas coisas\b", "estes pontos", text, flags=re.IGNORECASE)
    text = remove_original_language_scripts(text)
    text = normalize_markdown_structure(text)
    text = capitalize_sentence_starts(text)
    text = space_discussed_topics(text)
    text = remove_trailing_followup_offer(text)
    return text


def space_discussed_topics(text: str) -> str:
    """Quebra blocos longos em parágrafos quando há mudança clara de assunto."""
    if not text:
        return text

    text = re.sub(r"\s+(Observa[cç][aã]o\s*:)", r"\n\n\1", text, flags=re.IGNORECASE)
    parts = re.split(r"(\n\nObserva[cç][aã]o\s*:)", text, maxsplit=1, flags=re.IGNORECASE)
    main_text = _space_topic_text(parts[0])
    if len(parts) == 1:
        return main_text
    return f"{main_text}{''.join(parts[1:])}"


def _space_topic_text(text: str) -> str:
    paragraphs = re.split(r"\n{2,}", text.strip())
    return "\n\n".join(_space_topic_block(paragraph) for paragraph in paragraphs if paragraph.strip())


def _space_topic_block(text: str) -> str:
    block = text.strip()
    if len(block) < 360:
        return block

    transition = (
        r"(?:A|As|O|Os)\s+"
        r"(?:Confiss(?:ão|ao)|C(?:â|a)nones|Catecismo|Escrituras?)\b"
        r"|(?:Al[eé]m disso|Por isso|Desse modo|Assim),"
        r"|Isso mostra\b"
    )
    return re.sub(rf"(?<=[.!?])\s+(?={transition})", "\n\n", block)


def capitalize_sentence_starts(text: str) -> str:
    """Garante maiúscula no início de frases e blocos gerados pelo modelo."""

    def replacement(match: re.Match[str]) -> str:
        return f"{match.group(1)}{match.group(2)}{match.group(3).upper()}"

    return re.sub(
        r"(^|[.!?]\s+|\n+)(\s*(?:[\"'“”‘’(\[]\s*)?(?:\*\*)?)([a-záàâãéêíóôõúç])",
        replacement,
        text,
        flags=re.MULTILINE,
    )


def remove_original_language_scripts(text: str) -> str:
    """Remove caracteres hebraicos/gregos que o modelo possa inserir por engano."""
    text = re.sub(r"[\u0370-\u03FF\u1F00-\u1FFF\u0590-\u05FF]+", "", text)
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    text = re.sub(r"([(\[])\s+", r"\1", text)
    text = re.sub(r"[ \t\f\v]{2,}", " ", text)
    return re.sub(r"[ \t\f\v]*\n[ \t\f\v]*", "\n", text).strip()


def normalize_markdown_structure(text: str) -> str:
    """Preserva listas Markdown quando o modelo ou a limpeza deixam marcadores colados."""
    if not text:
        return text

    text = re.sub(r"(?<=[.!?\]])\s+(-\s+\*\*)", r"\n\1", text)
    text = re.sub(r"(?<=[.!?\]])\s+(-\s+)", r"\n\1", text)
    text = re.sub(r"(?<=[.!?\]])\s+(\d+\.\s+\*\*)", r"\n\1", text)
    lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            if lines and lines[-1] != "":
                lines.append("")
            continue
        is_list_item = line.startswith("- ") or bool(re.match(r"\d+\.\s+", line))
        previous = lines[-1] if lines else ""
        previous_is_list_item = previous.startswith("- ") or bool(re.match(r"\d+\.\s+", previous))
        if is_list_item and previous and not previous_is_list_item:
            lines.append("")
        lines.append(line)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def remove_trailing_followup_offer(text: str) -> str:
    """Remove convites finais genéricos que não fazem parte da resposta documental."""
    if not text:
        return text

    paragraphs = re.split(r"\n{2,}", text.strip())
    if not paragraphs:
        return text.strip()

    trailing = paragraphs[-1].strip()
    if re.match(r"^(?:se\s+(?:(?:voce|você)\s+)?quiser|caso\s+(?:voce|você)\s+queira),?\s+posso\b", trailing, flags=re.IGNORECASE):
        paragraphs = paragraphs[:-1]
    return "\n\n".join(paragraph for paragraph in paragraphs if paragraph.strip()).strip()


def _document_subject_reference(document: str) -> str:
    normalized = _normalize_document_label(document)
    if normalized.startswith("canones"):
        return document
    if normalized.startswith("catecismo"):
        return f"O {document}"
    if normalized.startswith("confissao"):
        return f"A {document}"
    return document


def _match_case_replacement(original: str, replacement: str) -> str:
    if original[:1].isupper():
        return replacement[:1].upper() + replacement[1:]
    return replacement


def _document_location_reference(document: str) -> str:
    normalized = _normalize_document_label(document)
    if normalized.startswith("canones"):
        return f"nos {document}"
    if normalized.startswith("catecismo"):
        return f"no {document}"
    if normalized.startswith("confissao"):
        return f"na {document}"
    return f"em {document}"


def _normalize_document_label(document: str) -> str:
    normalized = unicodedata.normalize("NFKD", document)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    return ascii_text.lower().strip()
