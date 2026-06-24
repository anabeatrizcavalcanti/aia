# Chunking estrutural: Dort e Heidelberg

## Status

PARTIAL

## Registro

Esta etapa criou a base comum do chunking estrutural e gerou os chunks de `canones-de-dort` e `catecismo-heidelberg`.

| document_id | Arquivo | Chunks |
| --- | --- | ---: |
| `canones-de-dort` | `corpus/processed/chunks/reformed/canones-de-dort.chunks.jsonl` | 107 |
| `catecismo-heidelberg` | `corpus/processed/chunks/reformed/catecismo-heidelberg.chunks.jsonl` | 130 |

## Estratégia

O script `scripts/pipeline/chunk_reformed_corpus.py` passou a centralizar funções de leitura, montagem de `chunk_id`, cálculo de `text_hash`, criação de `embedding_text`, escrita JSONL e validação básica dos chunks.

Nos Cânones de Dort, o chunking usa `canons_structure`: artigos, pares erro/refutação, conclusão e introdução ficam em unidades separadas.

No Catecismo de Heidelberg, o chunking usa `introductory_contexts` e `catechism_units`: cada pergunta-resposta vira um chunk único, preservando Parte, Dia do Senhor, referências e avisos de parsing.

## Tipos gerados

`canones-de-dort`:

- `introductory_context`: 1
- `doctrinal_article`: 59
- `error_refutation`: 34
- `conclusion_paragraph`: 13

`catecismo-heidelberg`:

- `introductory_context`: 1
- `catechism_question_answer`: 129

## Validação

```bash
python scripts/pipeline/chunk_reformed_corpus.py --documents canones-de-dort catecismo-heidelberg
python -m py_compile scripts/pipeline/chunk_reformed_corpus.py
python -m pytest tests/test_structural_chunking_part_a.py
```

Os JSONL foram lidos linha a linha. Não houve `chunk_id` duplicado, texto vazio ou `source_path` fora de `corpus/raw/reformed/`.

## Observações

O status ficou `PARTIAL` porque o Catecismo ainda mantém avisos de referência nas perguntas 10, 20, 29, 60 e 98. O texto das perguntas e respostas foi preservado, então esses avisos não bloquearam a geração dos chunks.

Westminster, Londres 1689 e `all_chunks.jsonl` ficaram fora desta etapa.
