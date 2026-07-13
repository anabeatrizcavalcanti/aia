"""API local para usar o SolaBot no navegador."""

from __future__ import annotations

import os
import sys
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field


ROOT_DIR = Path(__file__).resolve().parents[3]
SRC_DIR = ROOT_DIR / "src"
WEB_DIR = ROOT_DIR / "web"
WEB_DIST_DIR = WEB_DIR / "dist"
WEB_DIST_ASSETS_DIR = WEB_DIST_DIR / "assets"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from sola_bot.generation.rag_answer import RagAnswer  # noqa: E402
from sola_bot.generation.rag_generator import RagGenerator  # noqa: E402


if load_dotenv is not None:
    load_dotenv(ROOT_DIR / ".env")


class ChatRequest(BaseModel):
    """Entrada esperada pelo endpoint de chat."""

    question: str = Field(..., min_length=1)
    document_id: str | None = None
    chunk_type: str | None = None


class SuggestionRequest(BaseModel):
    """Entrada para gerar perguntas sugeridas depois de uma resposta."""

    question: str = Field(..., min_length=1)
    answer: str | None = None
    used_documents: list[str] = Field(default_factory=list)
    citations: list[dict[str, Any]] = Field(default_factory=list)
    max_suggestions: int = Field(default=6, ge=3, le=7)


app = FastAPI(title="FonteAliança Web", version="0.1.0")


if WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")
if WEB_DIST_ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=WEB_DIST_ASSETS_DIR), name="vite-assets")


@lru_cache(maxsize=1)
def get_generator() -> RagGenerator:
    """Mantém uma instância local do gerador RAG para uso no servidor."""
    return RagGenerator()


@app.get("/", response_model=None)
def index():
    """Serve a interface web local."""
    index_path = WEB_DIST_DIR / "index.html"
    if not index_path.exists():
        index_path = WEB_DIR / "index.html"
    if not index_path.exists():
        return JSONResponse(
            status_code=404,
            content={"status": "error", "message": "web/index.html não foi encontrado."},
        )
    return FileResponse(index_path)


@app.get("/api/health")
def health() -> dict[str, str]:
    """Verifica se a API local está ativa."""
    return {"status": "ok", "service": "solabot-web"}


@app.get("/api/documents")
def documents() -> dict[str, Any]:
    """Lista documentos disponíveis na base documental atual."""
    manifest_paths = [
        ROOT_DIR / "corpus" / "raw" / "reformed_manifest.json",
        ROOT_DIR / "corpus" / "raw" / "normative_manifest.json",
    ]
    documents = []
    for manifest_path in manifest_paths:
        if not manifest_path.exists():
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        raw_documents = manifest.get("documents", [])
        if not isinstance(raw_documents, list):
            continue
        for document in raw_documents:
            if not isinstance(document, dict):
                continue
            title = str(document.get("title") or "").strip()
            document_id = str(document.get("document_id") or document.get("doc_id") or "").strip()
            if not title or not document_id:
                continue
            documents.append(
                {
                    "document_id": document_id,
                    "title": title,
                    "document_type": str(document.get("document_type") or "").strip(),
                    "source_category": str(document.get("source_category") or "").strip(),
                    "denomination": str(document.get("denomination") or "").strip(),
                    "tradition": str(document.get("tradition") or "").strip(),
                    "language": str(document.get("language") or "").strip(),
                    "status": str(document.get("status") or "").strip(),
                }
            )

    return {
        "status": "ok",
        "corpus_name": "Documentos doutrinários e normativos da Aliança",
        "documents": documents,
    }


@app.post("/api/chat")
def chat(request: ChatRequest) -> JSONResponse:
    """Recebe pergunta, executa o gerador RAG oficial e retorna JSON serializável."""
    question = request.question.strip()
    if not question:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "A pergunta não pode ficar vazia."},
        )

    filters = build_filters(request.document_id, request.chunk_type)
    try:
        answer = get_generator().answer(question, filters=filters)
    except Exception as exc:  # pragma: no cover - proteção do servidor local
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": sanitize_error(exc)},
        )

    return JSONResponse(content=answer_to_response(answer))


@app.post("/api/suggestions")
def suggestions(request: SuggestionRequest) -> JSONResponse:
    """Gera perguntas de continuação a partir da última pergunta do usuário."""
    try:
        suggested_questions = build_suggested_questions(request)
    except Exception as exc:  # pragma: no cover - proteção do servidor local
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": sanitize_error(exc), "suggestions": []},
        )

    return JSONResponse(content={"status": "ok", "suggestions": suggested_questions})


def build_filters(document_id: str | None, chunk_type: str | None) -> dict[str, str] | None:
    """Monta filtros opcionais sem remover os filtros internos do pipeline."""
    filters: dict[str, str] = {}
    if document_id:
        filters["document_id"] = document_id
    if chunk_type:
        filters["chunk_type"] = chunk_type
    return filters or None


def build_suggested_questions(request: SuggestionRequest) -> list[dict[str, str]]:
    """Usa OpenAI para sugerir perguntas relacionadas e úteis para o usuário."""
    prompt = build_suggestions_prompt(request)
    generator = get_generator()
    client = generator._client()
    response = client.chat.completions.create(
        model=generator.model,
        messages=[
            {
                "role": "system",
                "content": (
                    "Você sugere perguntas de continuidade para um chatbot RAG sobre "
                    "documentos doutrinários e normativos da Aliança. Responda somente com JSON válido."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.35,
        max_completion_tokens=500,
    )
    content = response.choices[0].message.content
    return parse_suggested_questions(str(content), request.max_suggestions)


def build_suggestions_prompt(request: SuggestionRequest) -> str:
    """Monta prompt curto para sugestões de perguntas."""
    documents = ", ".join(request.used_documents[:6]) or "não informado"
    citation_titles = []
    for citation in request.citations[:5]:
        if not isinstance(citation, dict):
            continue
        document = str(citation.get("document") or "").strip()
        parent_title = str(citation.get("parent_title") or "").strip()
        if document and parent_title:
            citation_titles.append(f"{document} — {parent_title}")
        elif document:
            citation_titles.append(document)

    citation_text = "; ".join(citation_titles) or "não informado"
    answer = (request.answer or "").strip()
    answer_excerpt = answer[:1600] if answer else "não informado"

    return f"""
Gere {request.max_suggestions} novas perguntas em português para continuar uma consulta documental.

Baseie-se na última pergunta do usuário, na resposta gerada e nos documentos recuperados.
As perguntas devem ser específicas, naturais, úteis para RAG e adequadas ao corpus doutrinário e normativo da Aliança.
Não repita literalmente a pergunta original.
Não crie respostas.
Não prometa cobertura fora dos documentos.

Última pergunta:
{request.question.strip()}

Resposta gerada:
{answer_excerpt}

Documentos usados:
{documents}

Fontes recuperadas:
{citation_text}

Retorne apenas JSON válido neste formato:
{{
  "suggestions": [
    {{
      "question": "pergunta completa",
      "title": "rótulo curto com 1 a 4 palavras",
      "detail": "descrição curta com 3 a 8 palavras"
    }}
  ]
}}
""".strip()


def parse_suggested_questions(content: str, max_suggestions: int) -> list[dict[str, str]]:
    """Extrai e valida sugestões retornadas pelo modelo."""
    text = content.strip()
    if text.startswith("```"):
        text = text.strip("`").strip()
        if text.lower().startswith("json"):
            text = text[4:].strip()

    parsed = json.loads(text)
    raw_suggestions = parsed.get("suggestions") if isinstance(parsed, dict) else parsed
    if not isinstance(raw_suggestions, list):
        return []

    suggestions: list[dict[str, str]] = []
    seen_questions: set[str] = set()
    for item in raw_suggestions:
        if not isinstance(item, dict):
            continue
        question = str(item.get("question") or "").strip()
        if not question or question.lower() in seen_questions:
            continue
        seen_questions.add(question.lower())
        suggestions.append(
            {
                "question": question[:220],
                "title": str(item.get("title") or "Pergunta sugerida").strip()[:60],
                "detail": str(item.get("detail") or "continuação da conversa").strip()[:90],
            }
        )
        if len(suggestions) >= max_suggestions:
            break

    return suggestions


def answer_to_response(answer: RagAnswer) -> dict[str, Any]:
    """Reduz a resposta RAG para o contrato público da API local."""
    metadata = answer.metadata or {}
    retrieval_package = metadata.get("retrieval_package", {})
    evidence_decision = metadata.get("evidence_decision", {})
    compact_metadata = {
        "provider": metadata.get("provider", "openai"),
        "temperature": metadata.get("temperature"),
        "max_output_tokens": metadata.get("max_output_tokens"),
        "prompt_char_count": metadata.get("prompt_char_count"),
        "total_context_chars": retrieval_package.get("total_context_chars"),
        "evidence_reason": evidence_decision.get("reason"),
        "openai_called": metadata.get("openai_called", answer.status == "answered"),
    }
    if "retrieval_error" in metadata:
        compact_metadata["retrieval_error"] = metadata["retrieval_error"]
    if "openai_error" in metadata:
        compact_metadata["openai_error"] = sanitize_message(str(metadata["openai_error"]))

    citations = [citation.to_dict() for citation in answer.citations]
    enrich_citations_with_context(citations, retrieval_package)

    return {
        "query": answer.query,
        "status": answer.status,
        "answer": answer.answer,
        "used_context_count": answer.used_context_count,
        "used_documents": answer.used_documents,
        "used_sources": answer.used_sources,
        "citations": citations,
        "refusal_reason": answer.refusal_reason,
        "model": answer.model,
        "metadata": compact_metadata,
    }


def enrich_citations_with_context(citations: list[dict[str, Any]], retrieval_package: dict[str, Any]) -> None:
    """Inclui contexto textual recuperado nas citações públicas da API."""
    contexts = retrieval_package.get("contexts")
    if not isinstance(contexts, list):
        return

    context_by_source_id = {
        f"source_{index}": context
        for index, context in enumerate(contexts, start=1)
        if isinstance(context, dict)
    }

    for citation in citations:
        source_id = str(citation.get("source_id") or "")
        context = context_by_source_id.get(source_id)
        if not context:
            continue
        citation["context_text"] = context.get("context_text")
        citation["context_status"] = context.get("context_status")
        citation["content_priority"] = context.get("content_priority")
        citation["parent_key"] = context.get("parent_key")
        citation["page_start"] = context.get("page_start")
        citation["page_end"] = context.get("page_end")
        metadata = context.get("metadata") if isinstance(context.get("metadata"), dict) else {}
        citation["document_type"] = citation.get("document_type") or metadata.get("document_type")
        citation["source_category"] = citation.get("source_category") or metadata.get("source_category")
        citation["full_reference"] = citation.get("full_reference") or metadata.get("full_reference")
        citation["document_structure_type"] = citation.get("document_structure_type") or metadata.get("document_structure_type")
        citation["structural_reference"] = build_structural_reference(context)
        citation["chunk_texts"] = build_chunk_texts(context, citation)


def build_structural_reference(context: dict[str, Any]) -> str | None:
    """Deriva uma referência estrutural amigável dos chunks incluídos."""
    metadata = context.get("metadata")
    if not isinstance(metadata, dict):
        return None
    full_reference = str(metadata.get("full_reference") or "").strip()
    if full_reference:
        return full_reference
    chunks = metadata.get("included_chunks")
    if not isinstance(chunks, list):
        return None

    full_references = _unique_values(chunk.get("full_reference") for chunk in chunks if isinstance(chunk, dict))
    if full_references:
        return _join_pt(full_references)

    paragraph_numbers = _unique_values(chunk.get("paragraph_number") for chunk in chunks if isinstance(chunk, dict))
    if paragraph_numbers:
        return _numbered_reference("Parágrafo", "Parágrafos", paragraph_numbers)

    paragraph_labels = _unique_values(chunk.get("paragraph_label") for chunk in chunks if isinstance(chunk, dict))
    if paragraph_labels:
        return _join_pt(paragraph_labels)

    article_numbers = _unique_values(chunk.get("article_number") for chunk in chunks if isinstance(chunk, dict))
    if article_numbers:
        return _numbered_reference("Artigo", "Artigos", article_numbers)

    section_refs = _unique_values(
        _clean_section_reference(chunk.get("section_reference"))
        for chunk in chunks
        if isinstance(chunk, dict)
    )
    section_refs = [ref for ref in section_refs if ref and not ref.lower().startswith("página")]
    if section_refs:
        label = "Seção" if len(section_refs) == 1 else "Seções"
        return f"{label} {_join_pt(section_refs)}"

    return None


def build_chunk_texts(context: dict[str, Any], citation: dict[str, Any]) -> list[dict[str, str]]:
    """Retorna apenas textos dos chunks usados na fonte, sem cabeçalhos técnicos."""
    metadata = context.get("metadata")
    if not isinstance(metadata, dict):
        return []
    chunks = metadata.get("included_chunks")
    if not isinstance(chunks, list):
        return []

    allowed_ids = {
        str(chunk_id)
        for chunk_id in citation.get("included_chunk_ids", [])
        if chunk_id
    }
    result: list[dict[str, str]] = []
    for chunk in chunks:
        if not isinstance(chunk, dict):
            continue
        chunk_id = str(chunk.get("chunk_id") or "")
        if allowed_ids and chunk_id not in allowed_ids:
            continue
        text = str(chunk.get("text") or "").strip()
        if not chunk_id or not text:
            continue
        result.append({"chunk_id": chunk_id, "text": text})
    return result


def _clean_section_reference(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    for prefix in ("Parágrafo ", "Artigo ", "Seção "):
        if text.lower().startswith(prefix.lower()):
            return text[len(prefix) :].strip()
    return text


def _unique_values(values) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _numbered_reference(singular: str, plural: str, values: list[str]) -> str:
    label = singular if len(values) == 1 else plural
    return f"{label} {_join_pt(values)}"


def _join_pt(values: list[str]) -> str:
    if not values:
        return ""
    if len(values) == 1:
        return values[0]
    if len(values) == 2:
        return f"{values[0]} e {values[1]}"
    return f"{', '.join(values[:-1])} e {values[-1]}"


def sanitize_error(exc: Exception) -> str:
    """Preserva erro técnico útil sem expor variáveis sensíveis."""
    return sanitize_message(f"{type(exc).__name__}: {exc}")


def sanitize_message(message: str) -> str:
    """Remove qualquer aparição acidental da chave da OpenAI de mensagens de erro."""
    api_key = os.getenv("OPENAI_API_KEY", "")
    if api_key:
        message = message.replace(api_key, "[OPENAI_API_KEY]")
    return message
