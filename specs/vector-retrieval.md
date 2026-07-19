# Retrieval vetorial do corpus reformado

## Objetivo

Implementar a primeira camada de recuperação documental do AIA, capaz de receber uma pergunta doutrinária, gerar o embedding da consulta com OpenAI, consultar a collection ChromaDB do corpus reformado e retornar chunks relevantes com metadados e fontes rastreáveis.

## Escopo

Esta etapa trabalha apenas com retrieval vetorial simples. Ela não implementa busca lexical BM25, busca híbrida, RRF, reranking, parent retrieval, chatbot final ou geração de respostas com LLM.

## Entradas

- `reports/specs/openai-embeddings.md`
- `reports/specs/chroma-vector-index.md`
- `corpus/processed/chunks/reformed/all_chunks_for_embeddings.jsonl`
- `corpus/processed/embeddings/reformed/embedding_manifest.json`
- `corpus/indexes/chroma/reformed/`

## Saídas

- `src/aia/retrieval/query_embedder.py`
- `src/aia/retrieval/retrieval_result.py`
- `src/aia/retrieval/vector_retriever.py`
- `scripts/pipeline/query_vector_retriever.py`
- `config/retrieval_config.example.yaml`
- `reports/specs/vector-retrieval.md`
- `corpus/reports/retrieval/vector-retrieval-report.md`
- `corpus/reports/retrieval/vector-retrieval-report.json`
- `tests/test_vector_retriever.py`

## Configuração

O retriever usa a collection `aia_reformed_v1`, persistida em `corpus/indexes/chroma/reformed/`. O embedding das perguntas é gerado com `text-embedding-3-large`, mantendo compatibilidade com os embeddings já indexados.

## Filtros obrigatórios

Toda consulta mantém os filtros:

```json
{
  "corpus_id": "reformed",
  "retrieval_namespace": "reformed_confessional"
}
```

Filtros adicionais, como `document_id` e `chunk_type`, podem ser combinados, mas não substituem o escopo do corpus reformado.

## Validação

As consultas de validação observam temas doutrinários básicos:

- O que é o batismo?
- O que é necessário para a salvação?
- O que é eleição?
- O que é justificação?
- O que a tradição reformada ensina sobre as Escrituras?
- O crente pode perder a salvação?

O resultado esperado não é uma resposta final, mas uma lista de chunks recuperados com documento, tipo de chunk, seção, páginas, distância e fonte.
