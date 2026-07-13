# Retrieval híbrido do corpus reformado

## Componentes

- busca vetorial no índice ChromaDB já criado;
- busca lexical BM25 sobre os chunks elegíveis;
- fusão dos rankings por Reciprocal Rank Fusion.

## Entradas

- `corpus/processed/chunks/reformed/all_chunks_for_embeddings.jsonl`
- `corpus/processed/embeddings/reformed/embedding_manifest.json`
- `corpus/indexes/chroma/reformed/`
- `reports/specs/vector-retrieval.md`
- `corpus/reports/retrieval/vector-retrieval-report.md`

## Saídas

- `src/sola_bot/retrieval/bm25_retriever.py`
- `src/sola_bot/retrieval/rrf.py`
- `src/sola_bot/retrieval/hybrid_retriever.py`
- `scripts/pipeline/query_hybrid_retriever.py`
- `reports/specs/hybrid-retrieval.md`
- `corpus/reports/retrieval/hybrid-retrieval-report.md`
- `corpus/reports/retrieval/hybrid-retrieval-report.json`

## Parâmetros padrão

- `vector_candidate_k`: 20
- `bm25_candidate_k`: 20
- `final_top_k`: 5
- `rrf_k`: 60
- `bm25_text_field`: `embedding_text`
- `corpus_id`: `reformed`
- `retrieval_namespace`: `reformed_confessional`

## Restrição BM25

- biblioteca: `rank-bm25`
- classe: `BM25Okapi`
- fallback manual: não

## Escopo

- chatbot final;
- geração de resposta;
- reranking neural;
- parent retrieval;
- avaliação com documentos de outras tradições.
