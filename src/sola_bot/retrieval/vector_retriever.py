"""Retriever vetorial simples para o corpus documental da Aliança."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    import chromadb
except ImportError:  # pragma: no cover - tratado no fluxo de uso
    chromadb = None

from sola_bot.retrieval.query_embedder import embed_query
from sola_bot.retrieval.retrieval_result import RetrievalResult


ROOT_DIR = Path(__file__).resolve().parents[3]
DEFAULT_PERSIST_DIRECTORY = "corpus/indexes/chroma/alliance"
DEFAULT_COLLECTION_NAME = "solabot_alliance_v1"
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-large"
DEFAULT_CHUNKS_PATH = "corpus/processed/chunks/alliance/all_chunks_for_embeddings.jsonl"
DEFAULT_FILTERS: dict[str, Any] = {}


class VectorRetrieverError(RuntimeError):
    """Erro da camada de recuperação vetorial."""


class VectorRetriever:
    """Recupera chunks por similaridade vetorial em uma collection ChromaDB."""

    def __init__(
        self,
        persist_directory: str = DEFAULT_PERSIST_DIRECTORY,
        collection_name: str = DEFAULT_COLLECTION_NAME,
        embedding_model: str = DEFAULT_EMBEDDING_MODEL,
        chunks_path: str = DEFAULT_CHUNKS_PATH,
    ) -> None:
        if chromadb is None:
            raise VectorRetrieverError("chromadb não está instalado neste ambiente.")

        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        self.chunks_path = chunks_path
        self._chunk_text_by_id = self._load_chunk_texts(chunks_path)

        persist_path = self._repo_path(persist_directory)
        if not persist_path.exists():
            raise VectorRetrieverError(f"Índice ChromaDB não encontrado: {persist_directory}")

        client = chromadb.PersistentClient(path=str(persist_path))
        try:
            self.collection = client.get_collection(collection_name)
        except Exception as exc:
            raise VectorRetrieverError(f"Collection ChromaDB não encontrada: {collection_name}") from exc

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievalResult]:
        """Recupera os chunks mais próximos da pergunta informada."""
        if top_k < 1:
            raise VectorRetrieverError("top_k deve ser maior ou igual a 1.")

        query_embedding = embed_query(query, model=self.embedding_model)
        where_filter = self.build_where_filter(filters)
        query_args: dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results": top_k,
            "include": ["documents", "metadatas", "distances"],
        }
        if where_filter:
            query_args["where"] = where_filter
        result = self.collection.query(**query_args)
        return self._parse_chroma_result(result)

    def build_where_filter(self, filters: dict[str, Any] | None = None) -> dict[str, Any] | None:
        """
        Combina filtros adicionais com os filtros padrão do corpus ativo.
        """
        merged: dict[str, Any] = dict(DEFAULT_FILTERS)
        for key, value in (filters or {}).items():
            if value is None:
                continue
            if key in DEFAULT_FILTERS and value != DEFAULT_FILTERS[key]:
                continue
            merged[key] = value

        clauses = [{key: value} for key, value in merged.items()]
        if not clauses:
            return None
        if len(clauses) == 1:
            return clauses[0]
        return {"$and": clauses}

    def _parse_chroma_result(self, result: dict[str, Any]) -> list[RetrievalResult]:
        """Converte a resposta bruta do ChromaDB para objetos estruturados."""
        ids = result.get("ids", [[]])[0]
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        parsed: list[RetrievalResult] = []
        for chunk_id, chroma_text, metadata, distance in zip(
            ids,
            documents,
            metadatas,
            distances,
            strict=False,
        ):
            text = self._chunk_text_by_id.get(chunk_id) or chroma_text or ""
            parsed.append(
                RetrievalResult.from_chroma(
                    chunk_id=chunk_id,
                    metadata=metadata or {},
                    text=text,
                    distance=distance,
                )
            )
        return parsed

    def _load_chunk_texts(self, chunks_path: str) -> dict[str, str]:
        """Carrega o texto original dos chunks para apresentação dos resultados."""
        path = self._repo_path(chunks_path)
        if not path.exists():
            return {}

        texts: dict[str, str] = {}
        with path.open("r", encoding="utf-8") as file:
            for line in file:
                if not line.strip():
                    continue
                row = json.loads(line)
                chunk_id = row.get("chunk_id")
                text = row.get("text")
                if chunk_id and text:
                    texts[chunk_id] = text
        return texts

    @staticmethod
    def _repo_path(path: str) -> Path:
        """Resolve caminhos relativos à raiz do repositório."""
        candidate = Path(path)
        if candidate.is_absolute():
            return candidate
        return ROOT_DIR / candidate
