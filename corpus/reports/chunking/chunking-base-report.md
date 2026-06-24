# Chunking estrutural: Dort e Heidelberg

## Status

PARTIAL

## Resumo

Foram gerados chunks estruturais para Cânones de Dort e Catecismo de Heidelberg a partir dos JSONs estruturais e dos textos normalizados.

## Cânones de Dort

- Chunks: 107
- Arquivo: `corpus/processed/chunks/reformed/canones-de-dort.chunks.jsonl`
- Estrutura usada: `canons_structure`
- Tipos: `doctrinal_article`, `error_refutation`, `conclusion_paragraph`, `introductory_context`
- Conteúdo não doutrinário: 1 chunk introdutório
- Problemas de validação: nenhuma ocorrência

## Catecismo de Heidelberg

- Chunks: 130
- Arquivo: `corpus/processed/chunks/reformed/catecismo-heidelberg.chunks.jsonl`
- Estrutura usada: `introductory_contexts` e `catechism_units`
- Tipos: `catechism_question_answer`, `introductory_context`
- Conteúdo não doutrinário: 1 chunk introdutório
- Chunks com avisos: 5
- Problemas de validação: nenhuma ocorrência

## Fora do escopo

Westminster, Londres 1689, `all_chunks.jsonl`, embeddings, índice vetorial, OCR, chamadas à OpenAI e upload de usuário ficaram fora desta etapa.
