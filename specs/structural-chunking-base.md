# Base do chunking estrutural

## Objetivo

Criar a infraestrutura comum do chunking estrutural do corpus reformado e gerar os chunks iniciais para dois documentos:

- `canones-de-dort`
- `catecismo-heidelberg`

Westminster, Confissão Batista de Londres de 1689 e `all_chunks.jsonl` ficam fora desta etapa e serão tratados na chunking estrutural final.

## Entradas

- manifesto reformado em `corpus/raw/reformed_manifest.json`
- textos normalizados em `corpus/processed/normalized/reformed/`
- relatórios estruturais em `corpus/reports/structure_analysis/`
- relatórios das etapas anteriores em `reports/specs/`
- auditorias disponíveis em `reports/audits/`

## Saídas

- `corpus/processed/chunks/reformed/canones-de-dort.chunks.jsonl`
- `corpus/processed/chunks/reformed/catecismo-heidelberg.chunks.jsonl`
- relatório de chunking em `corpus/reports/chunking/`
- relatório da etapa em `reports/specs/chunking estrutural base-structural-chunking-base.md`

## Escopo

Esta etapa usa as estruturas já preparadas na fundação do corpus reformado:

- `canons_structure` para os Cânones de Dort;
- `introductory_contexts` para o material introdutório do Catecismo de Heidelberg;
- `catechism_units` para as unidades pergunta-resposta do Catecismo de Heidelberg.

Não há geração de embeddings, índice vetorial, chatbot, OCR, upload de documentos ou avaliação com documentos de outras tradições.
