# Recuperação hierárquica do corpus reformado

## Status

PASS

## Entradas

- `reports/specs/reranker-retrieval.md`
- `corpus/reports/retrieval/reranker-retrieval-report.md`
- `corpus/reports/retrieval/reranker-retrieval-report.json`
- `corpus/processed/chunks/reformed/all_chunks.jsonl`
- `corpus/processed/chunks/reformed/all_chunks_for_embeddings.jsonl`
- `corpus/processed/embeddings/reformed/embedding_manifest.json`
- `corpus/indexes/chroma/reformed/`
- `config/retrieval_config.example.yaml`
- `requirements.txt`

## Código

- `src/aia/retrieval/parent_context.py`
- `src/aia/retrieval/hierarchical_retriever.py`
- `scripts/pipeline/query_hierarchical_retriever.py`

## Configuração

- Estratégia: `structural_window`
- Anchor source: `reranked_retriever`
- Reranked top-k: `5`
- Parent max chars: `9000`
- Janela de irmãos: `1` antes, `1` depois
- Filtros: `{'corpus_id': 'reformed', 'retrieval_namespace': 'reformed_confessional'}`

## Implementação

- `ParentContextBuilder` carrega os chunks e cria índices por `chunk_id` e `parent_key`.
- `HierarchicalRetriever` chama o `RerankedRetriever` e expande cada chunk âncora.
- O contexto preserva chunk âncora, chunks incluídos, páginas, fonte e scores anteriores.

## Consultas

| Consulta | Âncoras | Contextos | Documentos | Status |
| --- | ---: | ---: | --- | --- |
| O que é o batismo? | 5 | 5 | confissao-batista-londres-1689, confissao-fe-westminster | expanded |
| O que é necessário para a salvação? | 5 | 5 | catecismo-heidelberg, confissao-batista-londres-1689 | expanded |
| O que é eleição? | 5 | 5 | canones-de-dort | expanded |
| O que é justificação? | 5 | 5 | confissao-batista-londres-1689, confissao-fe-westminster | expanded |
| O que a tradição reformada ensina sobre as Escrituras? | 5 | 5 | canones-de-dort, confissao-batista-londres-1689, confissao-fe-westminster | anchor_only, expanded |
| O crente pode perder a salvação? | 5 | 5 | canones-de-dort, confissao-batista-londres-1689, confissao-fe-westminster | expanded |
| O que é regeneração? | 5 | 5 | canones-de-dort, confissao-batista-londres-1689 | expanded |
| O que é expiação? | 5 | 5 | canones-de-dort, confissao-batista-londres-1689 | anchor_only, expanded |

## Resultados agregados

- Chunks carregados: `583`
- Grupos estruturais: `152`
- Documentos: `{'confissao-batista-londres-1689': 21, 'canones-de-dort': 12, 'confissao-fe-westminster': 6, 'catecismo-heidelberg': 1}`
- Tipos de chunk âncora: `{'confessional_paragraph': 21, 'doctrinal_article': 7, 'confessional_section': 4, 'introductory_context': 4, 'error_refutation': 3, 'catechism_question_answer': 1}`
- Status das expansões: `{'expanded': 35, 'anchor_only': 5}`
- Erro ou bloqueio: nenhuma ocorrência

## Validações executadas

```bash
python scripts/pipeline/query_hierarchical_retriever.py "O que é o batismo?" --top-k 5
python scripts/pipeline/query_hierarchical_retriever.py "O que é eleição?" --top-k 5
python scripts/pipeline/query_hierarchical_retriever.py "O que é justificação?" --top-k 5
python scripts/pipeline/query_hierarchical_retriever.py --write-report
python -m py_compile src/aia/retrieval/parent_context.py
python -m py_compile src/aia/retrieval/hierarchical_retriever.py
python -m py_compile scripts/pipeline/query_hierarchical_retriever.py
python -m pytest tests/test_hierarchical_retriever.py
```

## Pontos de atenção

- Dependências: `{'sentence_transformers_available': True, 'rank_bm25_available': True, 'chromadb_available': True, 'openai_api_key_configured': True}`
- Entradas ausentes: `[]`
- Bloqueio: `nenhum`

## Fora do escopo

- chatbot final
- resposta com LLM
- chamada a modelo de chat da OpenAI
- avaliação com documentos de outras tradições
- upload de documentos pelo usuário
- alteração de chunks, embeddings ou PDFs
- nova extração, normalização, chunking ou indexação
- política de recusa baseada em evidência
