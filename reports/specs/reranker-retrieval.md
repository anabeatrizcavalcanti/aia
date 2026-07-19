# Reranking neural do corpus reformado

## Status

PASS

## Entradas

- `reports/specs/hybrid-retrieval.md`
- `corpus/reports/retrieval/hybrid-retrieval-report.md`
- `corpus/reports/retrieval/hybrid-retrieval-report.json`
- `corpus/processed/chunks/reformed/all_chunks_for_embeddings.jsonl`
- `corpus/processed/embeddings/reformed/embedding_manifest.json`
- `corpus/indexes/chroma/reformed/`
- `config/retrieval_config.example.yaml`
- `requirements.txt`

## Código

- `src/aia/retrieval/cross_encoder_reranker.py`
- `src/aia/retrieval/reranked_retriever.py`
- `scripts/pipeline/query_reranked_retriever.py`

## Configuração

- Hybrid candidate k: `20`
- Final top-k: `5`
- Reranker model: `cross-encoder/ms-marco-TinyBERT-L2-v2`
- Max text chars: `3500`
- Filtros: `{'corpus_id': 'reformed', 'retrieval_namespace': 'reformed_confessional'}`

## Implementação

- `CrossEncoderReranker`: montagem dos pares pergunta/chunk e pontuação por `CrossEncoder`.
- `RerankedRetriever`: recuperação híbrida inicial e reordenação pelo reranker.
- Metadados registrados: `reranker_provider`, `reranker_model`, `reranker_score`, `pre_rerank_rank`, `pre_rerank_score`, `pre_rerank_sources`.

## Consultas

| Consulta | Candidatos híbridos | Resultados finais | Documentos | Tipos de chunk |
| --- | ---: | ---: | --- | --- |
| O que é o batismo? | 20 | 5 | confissao-batista-londres-1689, confissao-fe-westminster | confessional_paragraph, confessional_section |
| O que é necessário para a salvação? | 20 | 5 | catecismo-heidelberg, confissao-batista-londres-1689 | catechism_question_answer, confessional_paragraph |
| O que é eleição? | 20 | 5 | canones-de-dort | doctrinal_article, error_refutation |
| O que é justificação? | 20 | 5 | confissao-batista-londres-1689, confissao-fe-westminster | confessional_paragraph, confessional_section |
| O que a tradição reformada ensina sobre as Escrituras? | 20 | 5 | canones-de-dort, confissao-batista-londres-1689, confissao-fe-westminster | confessional_paragraph, introductory_context |
| O crente pode perder a salvação? | 20 | 5 | canones-de-dort, confissao-batista-londres-1689, confissao-fe-westminster | confessional_paragraph, confessional_section, doctrinal_article, error_refutation |
| O que é regeneração? | 20 | 5 | canones-de-dort, confissao-batista-londres-1689 | confessional_paragraph, doctrinal_article |
| O que é expiação? | 20 | 5 | canones-de-dort, confissao-batista-londres-1689 | confessional_paragraph, introductory_context |

## Resultados agregados

- Documentos mais recuperados: `{'confissao-batista-londres-1689': 21, 'canones-de-dort': 12, 'confissao-fe-westminster': 6, 'catecismo-heidelberg': 1}`
- Tipos de chunk mais recuperados: `{'confessional_paragraph': 21, 'doctrinal_article': 7, 'confessional_section': 4, 'introductory_context': 4, 'error_refutation': 3, 'catechism_question_answer': 1}`
- Mudanças de ranking: `{'items_with_rank_delta': 40, 'moved_up': 27, 'moved_down': 8, 'unchanged': 5, 'max_position_gain': 18, 'max_position_loss': -4}`
- Erro ou bloqueio: nenhuma ocorrência

## Validações executadas

```bash
python scripts/pipeline/query_reranked_retriever.py "O que é o batismo?" --top-k 5
python scripts/pipeline/query_reranked_retriever.py "O que é eleição?" --top-k 5
python scripts/pipeline/query_reranked_retriever.py "O que é justificação?" --top-k 5
python scripts/pipeline/query_reranked_retriever.py --write-report
python -m py_compile src/aia/retrieval/cross_encoder_reranker.py
python -m py_compile src/aia/retrieval/reranked_retriever.py
python -m py_compile scripts/pipeline/query_reranked_retriever.py
python -m pytest tests/test_reranker_retriever.py
```

## Pontos de atenção

- Dependências: `{'sentence_transformers_available': True, 'rank_bm25_available': True, 'chromadb_available': True, 'openai_api_key_configured': True}`.
- Entradas ausentes: `[]`.

## Fora do escopo

- chatbot final
- resposta com LLM
- chamada a modelo de chat da OpenAI
- avaliação com documentos de outras tradições
- upload de documentos pelo usuário
- alteração de chunks, embeddings ou PDFs
- nova extração, normalização, chunking ou indexação
- parent/hierarchical retrieval
- política de recusa baseada em evidência
