# Chunking estrutural consolidado

## Status

PARTIAL

## Resumo

O corpus reformado foi consolidado em `corpus/processed/chunks/reformed/all_chunks.jsonl` com 583 chunks.

## Documentos

### Westminster

- Chunks: 187
- Arquivo: `corpus/processed/chunks/reformed/confissao-fe-westminster.chunks.jsonl`
- Tipos: `confessional_section`, `introductory_context`, `special_layout`
- Conteúdo não doutrinário: 15 chunks
- Aviso preservado: página 1 sem texto extraível

### Cânones de Dort

- Chunks: 107
- Arquivo: `corpus/processed/chunks/reformed/canones-de-dort.chunks.jsonl`
- Tipos: `doctrinal_article`, `error_refutation`, `conclusion_paragraph`, `introductory_context`
- Conteúdo não doutrinário: 1 chunk

### Catecismo de Heidelberg

- Chunks: 130
- Arquivo: `corpus/processed/chunks/reformed/catecismo-heidelberg.chunks.jsonl`
- Tipos: `catechism_question_answer`, `introductory_context`
- Conteúdo não doutrinário: 1 chunk
- Avisos de referência: 5 chunks

### Londres 1689

- Chunks: 159
- Arquivo: `corpus/processed/chunks/reformed/confissao-batista-londres-1689.chunks.jsonl`
- Tipos: `confessional_paragraph`, `special_layout`
- Conteúdo não doutrinário: 2 chunks

## Consolidação

- Arquivo: `corpus/processed/chunks/reformed/all_chunks.jsonl`
- Total: 583 chunks
- Soma por documento:
  - Westminster: 187
  - Dort: 107
  - Heidelberg: 130
  - Londres 1689: 159

## Validação

Não houve duplicidade de `chunk_id`, texto vazio, `source_path` fora de `corpus/raw/reformed/` ou divergência entre a soma por documento e o arquivo consolidado.

## Fora do escopo

Embeddings, índice vetorial, OCR, chamadas à OpenAI, avaliação com outros corpus e upload de usuário ficaram fora desta etapa.
