# Recuperação hierárquica do corpus reformado

## Escopo

Camada de expansão estrutural aplicada após o reranking neural. A entrada operacional é uma pergunta doutrinária; a busca inicial continua sendo feita pelo `RerankedRetriever`. Esta etapa usa os chunks recuperados como âncoras e monta contextos documentais maiores a partir da estrutura já presente em `all_chunks_for_embeddings.jsonl`.

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

## Estratégia

Nome da estratégia: `structural_window`.

O chunk retornado pelo reranker é tratado como âncora. O construtor de contexto localiza esse chunk no arquivo de chunks processados, calcula uma chave estrutural superior e inclui trechos do mesmo grupo documental. O chunk âncora aparece primeiro no contexto.

Prioridade da chave estrutural:

1. `document_id + chapter_reference`
2. `document_id + chapter_title`
3. `document_id + section_reference`
4. `document_id + section_title`
5. `document_id + chunk_type`
6. `document_id + chunk_id`

Para o Catecismo de Heidelberg, `Dia do Senhor` é tratado como grupo catequético porque cada pergunta possui `section_reference` própria.

## Configuração

Parâmetros adicionados em `config/retrieval_config.example.yaml`:

```yaml
hierarchical_retrieval:
  enabled: true
  strategy: structural_window
  anchor_source: reranked_retriever
  reranked_top_k: 5
  parent_context_max_chars: 9000
  sibling_window_before: 1
  sibling_window_after: 1
  include_full_parent_when_small: true
  full_parent_max_chars: 7000
  include_metadata_header: true
  preserve_anchor_first: true
```

## Saídas

- `reports/specs/hierarchical-retrieval.md`
- `corpus/reports/retrieval/hierarchical-retrieval-report.md`
- `corpus/reports/retrieval/hierarchical-retrieval-report.json`

## Fora do escopo

- chatbot final
- resposta com LLM
- chamada a modelo de chat da OpenAI
- avaliação com documentos de outras tradições
- upload de documentos pelo usuário
- alteração de chunks, embeddings ou PDFs
- nova extração, normalização, chunking ou indexação
- política de recusa baseada em evidência
