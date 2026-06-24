# Chunking estrutural final

## Objetivo

Completar o chunking estrutural do corpus reformado com:

- `confissao-fe-westminster`;
- `confissao-batista-londres-1689`.

Esta etapa preserva os chunks de `canones-de-dort` e `catecismo-heidelberg` gerados na chunking estrutural base e consolida os quatro documentos em:

```txt
corpus/processed/chunks/reformed/all_chunks.jsonl
```

## Entradas

- manifesto reformado em `corpus/raw/reformed_manifest.json`;
- textos normalizados em `corpus/processed/normalized/reformed/`;
- relatórios estruturais em `corpus/reports/structure_analysis/`;
- chunks da chunking estrutural base em `corpus/processed/chunks/reformed/`;
- relatórios das etapas anteriores em `reports/specs/`;
- auditorias disponíveis em `reports/audits/`.

## Estratégia

Westminster usa `westminster_structure.chapters[].sections[]` como base para chunks `confessional_section`.

Londres 1689 usa `london_baptist_structure.chapters[].paragraphs[]` como base para chunks `confessional_paragraph`.

Layouts especiais, como tabelas de livros bíblicos, são preservados como `special_layout` e não são tratados como chunks doutrinários independentes.

## Saídas

- `corpus/processed/chunks/reformed/confissao-fe-westminster.chunks.jsonl`;
- `corpus/processed/chunks/reformed/confissao-batista-londres-1689.chunks.jsonl`;
- `corpus/processed/chunks/reformed/all_chunks.jsonl`;
- relatório de chunking em `corpus/reports/chunking/`;
- relatório da etapa em `reports/specs/chunking estrutural final-structural-chunking-final.md`.

## Fora de escopo

Não há geração de embeddings, índice vetorial, chatbot, OCR, upload de documentos ou avaliação com documentos de outras tradições nesta etapa.
