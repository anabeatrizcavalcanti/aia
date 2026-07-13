# Geração RAG com fontes do corpus reformado

## Status

PASS

## Entradas

- `reports/specs/retrieval-pipeline.md`
- `corpus/reports/retrieval/retrieval-pipeline-report.md`
- `corpus/reports/retrieval/retrieval-pipeline-report.json`
- `corpus/processed/chunks/reformed/all_chunks_for_embeddings.jsonl`
- `corpus/processed/embeddings/reformed/embedding_manifest.json`
- `corpus/indexes/chroma/reformed/`
- `config/retrieval_config.example.yaml`
- `requirements.txt`

## Código

- `src/sola_bot/generation/prompt_builder.py`
- `src/sola_bot/generation/evidence_policy.py`
- `src/sola_bot/generation/citation_formatter.py`
- `src/sola_bot/generation/rag_answer.py`
- `src/sola_bot/generation/rag_generator.py`
- `scripts/pipeline/query_rag_generator.py`

## Configuração

- Provider: `openai`
- Modelo: `gpt-5.4-mini`
- Temperature: `0.1`
- Max output tokens: `1200`
- Filtros: `{'corpus_id': 'reformed', 'retrieval_namespace': 'reformed_confessional'}`

## Implementação

- O caminho oficial de geração é `RagGenerator -> RetrievalPipeline -> EvidencePolicy -> PromptBuilder -> CitationFormatter -> OpenAI -> RagAnswer`.
- `RagGenerator` chama a `RetrievalPipeline`, aplica `EvidencePolicy`, monta prompt e chama OpenAI quando permitido.
- `EvidencePolicy` bloqueia geração sem contexto suficiente, sem source_map, apenas introdutória, sem contexto doutrinário ou sem sobreposição mínima com a pergunta.
- A política de evidência foi generalizada; não há recusa por lista fixa de temas específicos.
- `CitationFormatter` transforma `source_map` em citações rastreáveis.
- `RagAnswer` registra resposta, status, fontes, recusas e metadados técnicos.

## Consultas

| Consulta | Tipo | Status | Contextos | Documentos | Recusa | Modelo |
| --- | --- | --- | ---: | --- | --- | --- |
| O que é o batismo? | main | answered | 3 | confissao-batista-londres-1689, confissao-fe-westminster | não | gpt-5.4-mini |
| O que é necessário para a salvação? | main | answered | 3 | catecismo-heidelberg, confissao-batista-londres-1689 | não | gpt-5.4-mini |
| O que é eleição? | main | answered | 1 | canones-de-dort | não | gpt-5.4-mini |
| O que é justificação? | main | answered | 2 | confissao-batista-londres-1689, confissao-fe-westminster | não | gpt-5.4-mini |
| O que a tradição reformada ensina sobre as Escrituras? | main | answered | 1 | confissao-batista-londres-1689 | não | gpt-5.4-mini |
| O crente pode perder a salvação? | main | answered | 3 | canones-de-dort, confissao-batista-londres-1689, confissao-fe-westminster | não | gpt-5.4-mini |
| O que é regeneração? | main | answered | 3 | canones-de-dort, confissao-batista-londres-1689 | não | gpt-5.4-mini |
| O que é expiação? | main | answered | 2 | confissao-batista-londres-1689 | não | gpt-5.4-mini |
| O que a tradição reformada ensina sobre a sucessão papal? | refusal | refused | 4 | canones-de-dort, confissao-fe-westminster | insufficient_query_context_overlap | gpt-5.4-mini |
| Qual é a posição reformada sobre um documento que não está no corpus? | refusal | refused | 2 | canones-de-dort, confissao-batista-londres-1689 | requested_material_outside_active_corpus | gpt-5.4-mini |
| Segundo os documentos reformados disponíveis, qual é a doutrina da assunção de Maria? | refusal | refused | 4 | canones-de-dort, confissao-fe-westminster | only_introductory_context | gpt-5.4-mini |

## Resultados agregados

- Respostas geradas: `8`
- Recusas geradas: `3`
- Erros técnicos: `0`
- Status por consulta: `{'answered': 8, 'refused': 3}`
- Documentos usados: `{'confissao-batista-londres-1689': 8, 'canones-de-dort': 6, 'confissao-fe-westminster': 5, 'catecismo-heidelberg': 1}`
- Erro de preparação: `nenhum`

## Validações executadas

```bash
python scripts/pipeline/query_rag_generator.py "O que é o batismo?"
python scripts/pipeline/query_rag_generator.py "O que é eleição?"
python scripts/pipeline/query_rag_generator.py "O que é justificação?"
python scripts/pipeline/query_rag_generator.py "Segundo os documentos reformados disponíveis, qual é a doutrina da assunção de Maria?"
python scripts/pipeline/query_rag_generator.py --write-report
python -m py_compile src/sola_bot/generation/prompt_builder.py
python -m py_compile src/sola_bot/generation/evidence_policy.py
python -m py_compile src/sola_bot/generation/citation_formatter.py
python -m py_compile src/sola_bot/generation/rag_answer.py
python -m py_compile src/sola_bot/generation/rag_generator.py
python -m py_compile src/sola_bot/generation/rag_chain.py
python -m py_compile src/sola_bot/generation/source_grounded_prompt.py
python -m py_compile scripts/pipeline/query_rag_generator.py
python -m pytest tests/test_rag_answer_generation.py
```

## Pontos de atenção

- Dependências: `{'openai_available': True, 'sentence_transformers_available': True, 'rank_bm25_available': True, 'chromadb_available': True, 'openai_api_key_configured': True, 'openai_chat_model_configured': True}`
- Entradas ausentes: `[]`
- Bloqueio: `nenhum`
- As recusas são aplicadas por critérios documentais gerais e registram a razão técnica da decisão.
- Os testes cobrem recusa sem contexto, sem source_map, apenas introdutória, por baixa aderência entre pergunta e contexto e por pedido explicitamente fora do corpus.

## Fora do escopo

- interface web
- upload de documentos pelo usuário
- avaliação com documentos de outras tradições
- avaliação automática com RAGAS ou ARES
- alteração de chunks, embeddings ou PDFs
- nova extração, normalização, chunking ou indexação
- treinamento ou fine-tuning de modelo
