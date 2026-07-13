# Pipeline final de retrieval do corpus reformado

## Escopo

Camada final de preparação de contexto documental para a geração RAG. A etapa consome os contextos hierárquicos e entrega um pacote consolidado, deduplicado e limitado por tamanho.

Esta etapa não gera resposta ao usuário e não chama modelo de chat.

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

## Estratégia

Fluxo:

```txt
Pergunta
→ HierarchicalRetriever
→ ContextConsolidator
→ RetrievalContextPackage
```

O consolidador agrupa contextos por `parent_key`, preserva âncoras, deduplica chunks incluídos e aplica limites de caracteres. Contextos doutrinários têm prioridade sobre material introdutório em perguntas doutrinárias.

## Configuração

Parâmetros adicionados em `config/retrieval_config.example.yaml`:

```yaml
retrieval_pipeline:
  enabled: true
  source: hierarchical_retriever
  final_context_top_k: 4
  max_total_context_chars: 18000
  max_context_chars_per_parent: 9000
  consolidate_by_parent_key: true
  deduplicate_included_chunks: true
  prefer_expanded_contexts: true
  reduce_introductory_context_for_doctrinal_queries: true
  keep_anchor_only_when_no_expanded_alternative: true
  preserve_document_diversity: true
  max_contexts_per_parent_key: 1
  include_context_package_header: true
  include_source_map: true
```

## Saídas

- `reports/specs/retrieval-pipeline.md`
- `corpus/reports/retrieval/retrieval-pipeline-report.md`
- `corpus/reports/retrieval/retrieval-pipeline-report.json`

## Fora do escopo

- chatbot final
- resposta com LLM
- chamada a modelo de chat da OpenAI
- avaliação com documentos de outras tradições
- upload de documentos pelo usuário
- alteração de chunks, embeddings ou PDFs
- nova extração, normalização, chunking ou indexação
- política de recusa baseada em evidência
