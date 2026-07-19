# Índice vetorial ChromaDB e validação de retrieval

## Objetivo

Criar uma collection ChromaDB persistente para o corpus reformado usando os embeddings gerados na seleção de chunks e embeddings OpenAI.

## Entrada principal

```txt
corpus/processed/embeddings/reformed/openai_embeddings.jsonl
```

## Saída principal

```txt
corpus/indexes/chroma/reformed/
```

## Collection

```txt
aia_reformed_v1
```

## Escopo

Esta etapa não gera novos embeddings dos chunks, não implementa chatbot, não gera respostas com LLM e não altera texto doutrinário.
