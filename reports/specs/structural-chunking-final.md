# Chunking estrutural final do corpus reformado

## Status

PARTIAL

## Registro

O chunking estrutural foi completado para os quatro documentos reformados. Westminster e Londres 1689 foram processados nesta etapa; Dort e Heidelberg foram preservados da etapa anterior.

| document_id | Chunks |
| --- | ---: |
| `confissao-fe-westminster` | 187 |
| `canones-de-dort` | 107 |
| `catecismo-heidelberg` | 130 |
| `confissao-batista-londres-1689` | 159 |

Total consolidado: 583 chunks em `corpus/processed/chunks/reformed/all_chunks.jsonl`.

## Estratégia por documento

Westminster usa `westminster_structure.chapters[].sections[]`. Cada seção confessional vira `confessional_section`. O material histórico das páginas 4 a 17 fica como `introductory_context`, e a lista dos livros bíblicos fica como `special_layout`.

Londres 1689 usa `london_baptist_structure.chapters[].paragraphs[]`. Cada parágrafo numerado vira `confessional_paragraph`, com referências bíblicas associadas preservadas no mesmo chunk. As tabelas do Antigo e do Novo Testamento ficam como `special_layout`.

Dort e Heidelberg foram apenas revalidados antes da consolidação.

## Tipos no corpus consolidado

- `confessional_section`: 172
- `confessional_paragraph`: 157
- `catechism_question_answer`: 129
- `doctrinal_article`: 59
- `error_refutation`: 34
- `introductory_context`: 16
- `conclusion_paragraph`: 13
- `special_layout`: 3

## Conteúdo não doutrinário

Foram marcados como `is_doctrinal=false`: introduções históricas, contextos documentais e layouts especiais. Esses chunks foram preservados para rastreabilidade e contexto, mas não recebem o mesmo papel dos chunks doutrinários.

## Validação

```bash
python scripts/pipeline/chunk_reformed_corpus.py --documents confissao-fe-westminster confissao-batista-londres-1689 --consolidate
python -m py_compile scripts/pipeline/chunk_reformed_corpus.py
python -m pytest tests/test_structural_chunking_final.py
```

Os arquivos JSONL foram validados linha a linha. Não houve duplicidade de `chunk_id`, texto vazio, `source_path` fora do corpus reformado ou diferença entre a soma dos arquivos por documento e `all_chunks.jsonl`.

## Observações

O status ficou `PARTIAL` por dois motivos conhecidos:

- a página 1 de Westminster não retornou texto extraível;
- o Catecismo de Heidelberg ainda mantém avisos de referência nas perguntas 10, 20, 29, 60 e 98.

Não foram gerados embeddings, índice vetorial ou respostas com LLM nesta etapa.
