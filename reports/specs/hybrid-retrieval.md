# Retrieval híbrido do corpus reformado

## Status

PASS

## Entradas

- `reports/specs/vector-retrieval.md`
- `corpus/reports/retrieval/vector-retrieval-report.md`
- `corpus/reports/retrieval/vector-retrieval-report.json`
- `corpus/processed/chunks/reformed/all_chunks_for_embeddings.jsonl`
- `corpus/processed/embeddings/reformed/embedding_manifest.json`
- `corpus/indexes/chroma/reformed/`

## Código

- `src/aia/retrieval/bm25_retriever.py`
- `src/aia/retrieval/rrf.py`
- `src/aia/retrieval/hybrid_retriever.py`
- `scripts/pipeline/query_hybrid_retriever.py`

## Configuração

- Vector candidate k: `20`
- BM25 candidate k: `20`
- Final top-k: `5`
- RRF k: `60`
- BM25 text field: `embedding_text`
- Filtros: `{'corpus_id': 'reformed', 'retrieval_namespace': 'reformed_confessional'}`

## Consultas

| Consulta | Resultados | Documentos | Tipos de chunk |
| --- | ---: | --- | --- |
| O que é o batismo? | 5 | catecismo-heidelberg, confissao-batista-londres-1689 | catechism_question_answer, confessional_paragraph |
| O que é necessário para a salvação? | 5 | catecismo-heidelberg, confissao-batista-londres-1689 | catechism_question_answer, confessional_paragraph |
| O que é eleição? | 5 | canones-de-dort | doctrinal_article, error_refutation |
| O que é justificação? | 5 | confissao-batista-londres-1689, confissao-fe-westminster | confessional_paragraph, confessional_section |
| O que a tradição reformada ensina sobre as Escrituras? | 5 | confissao-batista-londres-1689 | confessional_paragraph |
| O crente pode perder a salvação? | 5 | canones-de-dort, confissao-batista-londres-1689, confissao-fe-westminster | confessional_paragraph, confessional_section, doctrinal_article, error_refutation |
| O que é regeneração? | 5 | canones-de-dort | doctrinal_article, error_refutation |
| O que é expiação? | 5 | canones-de-dort, catecismo-heidelberg, confissao-batista-londres-1689 | catechism_question_answer, confessional_paragraph, introductory_context |

## Agregados

- Documentos mais recuperados: `{'confissao-batista-londres-1689': 17, 'canones-de-dort': 13, 'catecismo-heidelberg': 7, 'confissao-fe-westminster': 3}`
- Tipos de chunk mais recuperados: `{'confessional_paragraph': 17, 'catechism_question_answer': 7, 'doctrinal_article': 6, 'error_refutation': 6, 'confessional_section': 3, 'introductory_context': 1}`
- Erro ou bloqueio: nenhuma ocorrência

## Validações executadas

```bash
python scripts/pipeline/query_hybrid_retriever.py "O que é o batismo?" --top-k 5
python scripts/pipeline/query_hybrid_retriever.py "O que é eleição?" --top-k 5
python scripts/pipeline/query_hybrid_retriever.py "O que é justificação?" --top-k 5
python scripts/pipeline/query_hybrid_retriever.py --write-report
python -m py_compile src/aia/retrieval/bm25_retriever.py
python -m py_compile src/aia/retrieval/rrf.py
python -m py_compile src/aia/retrieval/hybrid_retriever.py
python -m py_compile scripts/pipeline/query_hybrid_retriever.py
python -m pytest tests/test_hybrid_retriever.py
```

## Pontos de atenção

- Dependências: `{'rank_bm25_available': True, 'chromadb_available': True, 'openai_api_key_configured': True}`.
- Entradas ausentes: `[]`.

## Fora do escopo

- chatbot final
- resposta com LLM
- chamada a modelo de chat da OpenAI
- avaliação com documentos de outras tradições
- upload de documentos pelo usuário
- alteração de chunks, embeddings ou PDFs
- nova extração, normalização, chunking ou indexação
- reranking neural
- parent/hierarchical retrieval
