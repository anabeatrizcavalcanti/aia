# Pipeline final de retrieval do corpus reformado

## Status

PASS

## Entradas

- `reports/specs/hierarchical-retrieval.md`
- `corpus/reports/retrieval/hierarchical-retrieval-report.md`
- `corpus/reports/retrieval/hierarchical-retrieval-report.json`
- `corpus/processed/chunks/reformed/all_chunks_for_embeddings.jsonl`
- `corpus/processed/embeddings/reformed/embedding_manifest.json`
- `corpus/indexes/chroma/reformed/`
- `config/retrieval_config.example.yaml`
- `requirements.txt`

## Código

- `src/sola_bot/retrieval/final_context.py`
- `src/sola_bot/retrieval/context_consolidator.py`
- `src/sola_bot/retrieval/retrieval_pipeline.py`
- `scripts/pipeline/query_retrieval_pipeline.py`

## Configuração

- Final top-k: `4`
- Limite total de caracteres: `18000`
- Limite por parent: `9000`
- Consolidação por parent_key: `True`
- Filtros: `{'corpus_id': 'reformed', 'retrieval_namespace': 'reformed_confessional'}`

## Implementação

- `FinalContext` e `RetrievalContextPackage` representam a saída consolidada.
- `ContextConsolidator` agrupa por `parent_key`, deduplica chunks e aplica limites de tamanho.
- `RetrievalPipeline` chama o `HierarchicalRetriever` e entrega o pacote final.

## Consultas

| Consulta | Hierárquicos | Finais | Fundidos | Dedup chunks | Caracteres | Documentos |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| O que é o batismo? | 5 | 3 | 2 | 0 | 10543 | confissao-batista-londres-1689, confissao-fe-westminster |
| O que é necessário para a salvação? | 5 | 3 | 1 | 0 | 15411 | catecismo-heidelberg, confissao-batista-londres-1689 |
| O que é eleição? | 5 | 1 | 4 | 0 | 4126 | canones-de-dort |
| O que é justificação? | 5 | 2 | 3 | 0 | 9117 | confissao-batista-londres-1689, confissao-fe-westminster |
| O que a tradição reformada ensina sobre as Escrituras? | 5 | 1 | 1 | 0 | 6721 | confissao-batista-londres-1689 |
| O crente pode perder a salvação? | 5 | 3 | 2 | 0 | 16624 | canones-de-dort, confissao-batista-londres-1689, confissao-fe-westminster |
| O que é regeneração? | 5 | 3 | 2 | 0 | 16654 | canones-de-dort, confissao-batista-londres-1689 |
| O que é expiação? | 5 | 2 | 1 | 0 | 12442 | confissao-batista-londres-1689 |

## Resultados agregados

- Contextos hierárquicos recebidos: `40`
- Contextos finais: `18`
- Contextos fundidos por parent_key: `16`
- Chunks deduplicados: `0`
- Documentos preservados: `{'confissao-batista-londres-1689': 11, 'confissao-fe-westminster': 3, 'canones-de-dort': 3, 'catecismo-heidelberg': 1}`
- Tipos de chunk preservados: `{'confessional_paragraph': 19, 'doctrinal_article': 7, 'confessional_section': 4, 'error_refutation': 3, 'catechism_question_answer': 1}`
- Erro ou bloqueio: nenhuma ocorrência

## Validações executadas

```bash
python scripts/pipeline/query_retrieval_pipeline.py "O que é o batismo?"
python scripts/pipeline/query_retrieval_pipeline.py "O que é eleição?"
python scripts/pipeline/query_retrieval_pipeline.py "O que é justificação?"
python scripts/pipeline/query_retrieval_pipeline.py "O que é expiação?"
python scripts/pipeline/query_retrieval_pipeline.py --write-report
python -m py_compile src/sola_bot/retrieval/final_context.py
python -m py_compile src/sola_bot/retrieval/context_consolidator.py
python -m py_compile src/sola_bot/retrieval/retrieval_pipeline.py
python -m py_compile scripts/pipeline/query_retrieval_pipeline.py
python -m pytest tests/test_retrieval_pipeline.py
```

## Pontos de atenção

- Dependências: `{'sentence_transformers_available': True, 'rank_bm25_available': True, 'chromadb_available': True, 'openai_api_key_configured': True}`
- Entradas ausentes: `[]`
- Bloqueio: `nenhum`
- A ordenação final usa heurística operacional documentada no JSON do relatório.

## Fora do escopo

- chatbot final
- resposta com LLM
- chamada a modelo de chat da OpenAI
- avaliação com documentos de outras tradições
- upload de documentos pelo usuário
- alteração de chunks, embeddings ou PDFs
- nova extração, normalização, chunking ou indexação
- política de recusa baseada em evidência
