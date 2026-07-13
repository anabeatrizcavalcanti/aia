# Seleção de chunks e geração de embeddings com OpenAI

## Objetivo

Selecionar chunks elegíveis do corpus reformado e gerar embeddings com OpenAI para preparar a futura indexação no ChromaDB.

## Entrada principal

```txt
corpus/processed/chunks/reformed/all_chunks.jsonl
```

## Saídas

- `corpus/processed/chunks/reformed/all_chunks_for_embeddings.jsonl`
- `corpus/processed/embeddings/reformed/openai_embeddings.jsonl`
- `corpus/processed/embeddings/reformed/embedding_manifest.json`
- `corpus/reports/embeddings/openai-embedding-report.md`
- `corpus/reports/embeddings/openai-embedding-report.json`
- `reports/specs/openai-embeddings.md`

## Modelo

- Provedor: OpenAI
- Modelo padrão: `text-embedding-3-large`
- Dimensões solicitadas: 3072
- Campo de entrada: `embedding_text`

## Escopo

Esta etapa não cria índice ChromaDB, não implementa chatbot, não gera respostas com LLM e não altera texto doutrinário.
