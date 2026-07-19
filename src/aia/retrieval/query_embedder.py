"""Geração de embeddings para perguntas do usuário."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - fallback para ambientes mínimos
    load_dotenv = None


OPENAI_EMBEDDINGS_URL = "https://api.openai.com/v1/embeddings"
DEFAULT_QUERY_EMBEDDING_MODEL = "text-embedding-3-large"
DEFAULT_QUERY_EMBEDDING_DIMENSIONS = 3072


class QueryEmbeddingError(RuntimeError):
    """Erro de geração de embedding de consulta."""


def _load_environment() -> None:
    """Carrega variáveis locais de ambiente quando python-dotenv estiver disponível."""
    if load_dotenv is not None:
        load_dotenv()


def embed_query(
    query: str,
    model: str = DEFAULT_QUERY_EMBEDDING_MODEL,
    dimensions: int = DEFAULT_QUERY_EMBEDDING_DIMENSIONS,
    max_retries: int = 3,
) -> list[float]:
    """
    Gera embedding para uma pergunta do usuário usando OpenAI.

    A chave da OpenAI é lida apenas do ambiente. Esta função não grava chaves
    nem persiste qualquer dado sensível em arquivos.
    """
    _load_environment()
    cleaned_query = query.strip()
    if not cleaned_query:
        raise QueryEmbeddingError("A pergunta não pode estar vazia.")

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise QueryEmbeddingError("OPENAI_API_KEY não está configurada no ambiente.")

    payload = json.dumps(
        {
            "model": model,
            "input": cleaned_query,
            "dimensions": dimensions,
        }
    ).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    for attempt in range(1, max_retries + 1):
        request = urllib.request.Request(
            OPENAI_EMBEDDINGS_URL,
            data=payload,
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                body = json.loads(response.read().decode("utf-8"))
            return body["data"][0]["embedding"]
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            if exc.code in {429, 500, 502, 503, 504} and attempt < max_retries:
                time.sleep(2 * attempt)
                continue
            raise QueryEmbeddingError(
                f"A API de embeddings da OpenAI retornou HTTP {exc.code}: {error_body[:500]}"
            ) from exc
        except urllib.error.URLError as exc:
            if attempt < max_retries:
                time.sleep(2 * attempt)
                continue
            raise QueryEmbeddingError(f"Falha de rede ao chamar a API de embeddings: {exc}") from exc

    raise QueryEmbeddingError("A geração de embedding falhou após as tentativas configuradas.")
