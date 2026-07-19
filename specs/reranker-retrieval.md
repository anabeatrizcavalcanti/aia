# Reranking neural do corpus reformado

## Componentes

- `HybridRetriever`
- `CrossEncoderReranker`
- modelo Cross-Encoder via `sentence-transformers`

## Entradas

- `reports/specs/hybrid-retrieval.md`
- `corpus/reports/retrieval/hybrid-retrieval-report.json`
- `corpus/processed/chunks/reformed/all_chunks_for_embeddings.jsonl`
- `corpus/processed/embeddings/reformed/embedding_manifest.json`
- `corpus/indexes/chroma/reformed/`
- `config/retrieval_config.example.yaml`

## Saídas

- `src/aia/retrieval/cross_encoder_reranker.py`
- `src/aia/retrieval/reranked_retriever.py`
- `scripts/pipeline/query_reranked_retriever.py`
- `reports/specs/reranker-retrieval.md`
- `corpus/reports/retrieval/reranker-retrieval-report.md`
- `corpus/reports/retrieval/reranker-retrieval-report.json`

## Parâmetros padrão

- `model_name`: `cross-encoder/ms-marco-TinyBERT-L2-v2`
- `hybrid_candidate_k`: 20
- `final_top_k`: 5
- `max_text_chars`: 3500
- `include_metadata_in_reranker_text`: true

## Fora do escopo

- chatbot final;
- geração de resposta;
- parent retrieval;
- política de recusa baseada em evidência;
- avaliação com documentos de outras tradições.
