# Extração e normalização do corpus reformado

## Objetivo

Implementar a extração textual e a normalização inicial dos quatro documentos do corpus reformado do AIA, preservando rastreabilidade por página e metadados documentais suficientes para a etapa posterior de chunking estrutural.

## Entradas

- `corpus/raw/reformed_manifest.json`
- relatórios estruturais em `corpus/reports/structure_analysis/`
- relatórios e auditorias da fundação do corpus reformado disponíveis em `reports/specs/` e `reports/audits/`

## Saídas Esperadas

- arquivos extraídos em `corpus/processed/extracted/reformed/`
- arquivos normalizados em `corpus/processed/normalized/reformed/`
- relatórios de extração em `corpus/reports/extraction/`
- relatórios de normalização em `corpus/reports/normalization/`
- relatório final da etapa em `reports/specs/extração e normalização-extraction-normalization.md`

## Escopo

A extração e normalização cobre somente extração e normalização mecânica segura. Não inclui chunking final, embeddings, índice vetorial, chatbot, OCR, chamadas à OpenAI, upload de documentos pelo usuário ou avaliação com documentos de outras tradições.

## Critérios de Aceite

- os quatro documentos reformados são processados;
- cada documento recebe arquivos `.json` e `.txt` extraídos;
- cada documento recebe arquivos `.json` e `.txt` normalizados;
- os metadados `document_id`, `raw_path`, `document_type`, tradição e páginas são preservados;
- os JSONs gerados são válidos;
- os principais marcadores estruturais permanecem visíveis no texto normalizado;
- os scripts compilam;
- os testes da etapa passam.
