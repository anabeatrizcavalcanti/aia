# Relatório de retrieval híbrido

## Status

PASS

## Parâmetros

- Vector candidate k: `20`
- BM25 candidate k: `20`
- Final top-k: `5`
- RRF k: `60`
- Campo lexical BM25: `embedding_text`
- Filtros padrão: `{'corpus_id': 'reformed', 'retrieval_namespace': 'reformed_confessional'}`

## Arquivos e índices

- Chunks: `corpus/processed/chunks/reformed/all_chunks_for_embeddings.jsonl`.
- Índice ChromaDB: `corpus/indexes/chroma/reformed/`.
- Collection: `aia_reformed_v1`.
- BM25: `rank-bm25` / `BM25Okapi`, `580` chunks carregados.
- Modelo de embedding da pergunta: `text-embedding-3-large`.

## Consultas

### O que é o batismo?

- Resultados: `5`
- Documentos: `catecismo-heidelberg, confissao-batista-londres-1689`

| Rank | Chunk | Documento | Tipo | Páginas | RRF |
| ---: | --- | --- | --- | --- | ---: |
| 1 | `confissao-batista-londres-1689_capitulo-29_paragrafo-1` | `confissao-batista-londres-1689` | `confessional_paragraph` | 74-74 | 0.03252247488101534 |
| 2 | `catecismo-heidelberg_pergunta-069` | `catecismo-heidelberg` | `catechism_question_answer` | 15-15 | 0.03252247488101534 |
| 3 | `confissao-batista-londres-1689_capitulo-29_paragrafo-4` | `confissao-batista-londres-1689` | `confessional_paragraph` | 74-75 | 0.030776515151515152 |
| 4 | `catecismo-heidelberg_pergunta-073` | `catecismo-heidelberg` | `catechism_question_answer` | 15-16 | 0.030090497737556562 |
| 5 | `confissao-batista-londres-1689_capitulo-29_paragrafo-2` | `confissao-batista-londres-1689` | `confessional_paragraph` | 74-74 | 0.02976190476190476 |

### O que é necessário para a salvação?

- Resultados: `5`
- Documentos: `catecismo-heidelberg, confissao-batista-londres-1689`

| Rank | Chunk | Documento | Tipo | Páginas | RRF |
| ---: | --- | --- | --- | --- | ---: |
| 1 | `catecismo-heidelberg_pergunta-030` | `catecismo-heidelberg` | `catechism_question_answer` | 7-7 | 0.03252247488101534 |
| 2 | `confissao-batista-londres-1689_capitulo-15_paragrafo-5` | `confissao-batista-londres-1689` | `confessional_paragraph` | 36-37 | 0.02819138376017471 |
| 3 | `confissao-batista-londres-1689_capitulo-30_paragrafo-2` | `confissao-batista-londres-1689` | `confessional_paragraph` | 75-75 | 0.01639344262295082 |
| 4 | `catecismo-heidelberg_pergunta-029` | `catecismo-heidelberg` | `catechism_question_answer` | 7-7 | 0.016129032258064516 |
| 5 | `confissao-batista-londres-1689_capitulo-18_paragrafo-3` | `confissao-batista-londres-1689` | `confessional_paragraph` | 43-45 | 0.015873015873015872 |

### O que é eleição?

- Resultados: `5`
- Documentos: `canones-de-dort`

| Rank | Chunk | Documento | Tipo | Páginas | RRF |
| ---: | --- | --- | --- | --- | ---: |
| 1 | `canones-de-dort_capitulo-01_artigo-08` | `canones-de-dort` | `doctrinal_article` | 3-4 | 0.031024531024531024 |
| 2 | `canones-de-dort_capitulo-01_rejeicao-erros_erro-05` | `canones-de-dort` | `error_refutation` | 8-9 | 0.03009207275993712 |
| 3 | `canones-de-dort_capitulo-01_rejeicao-erros_erro-01` | `canones-de-dort` | `error_refutation` | 7-7 | 0.029877369007803793 |
| 4 | `canones-de-dort_capitulo-01_artigo-07` | `canones-de-dort` | `doctrinal_article` | 3-3 | 0.02938045560996381 |
| 5 | `canones-de-dort_capitulo-01_rejeicao-erros_erro-06` | `canones-de-dort` | `error_refutation` | 9-9 | 0.029211087420042643 |

### O que é justificação?

- Resultados: `5`
- Documentos: `confissao-batista-londres-1689, confissao-fe-westminster`

| Rank | Chunk | Documento | Tipo | Páginas | RRF |
| ---: | --- | --- | --- | --- | ---: |
| 1 | `confissao-batista-londres-1689_capitulo-11_paragrafo-2` | `confissao-batista-londres-1689` | `confessional_paragraph` | 29-30 | 0.03177805800756621 |
| 2 | `confissao-batista-londres-1689_capitulo-11_paragrafo-1` | `confissao-batista-londres-1689` | `confessional_paragraph` | 29-29 | 0.031544957774465976 |
| 3 | `confissao-fe-westminster_capitulo-xi_secao-i` | `confissao-fe-westminster` | `confessional_section` | 33-33 | 0.030834914611005692 |
| 4 | `confissao-fe-westminster_capitulo-xi_secao-ii` | `confissao-fe-westminster` | `confessional_section` | 33-33 | 0.0304147465437788 |
| 5 | `confissao-batista-londres-1689_capitulo-11_paragrafo-4` | `confissao-batista-londres-1689` | `confessional_paragraph` | 30-31 | 0.02976190476190476 |

### O que a tradição reformada ensina sobre as Escrituras?

- Resultados: `5`
- Documentos: `confissao-batista-londres-1689`

| Rank | Chunk | Documento | Tipo | Páginas | RRF |
| ---: | --- | --- | --- | --- | ---: |
| 1 | `confissao-batista-londres-1689_capitulo-1_paragrafo-6` | `confissao-batista-londres-1689` | `confessional_paragraph` | 4-5 | 0.03177805800756621 |
| 2 | `confissao-batista-londres-1689_capitulo-1_paragrafo-5` | `confissao-batista-londres-1689` | `confessional_paragraph` | 4-4 | 0.03128054740957967 |
| 3 | `confissao-batista-londres-1689_capitulo-1_paragrafo-10` | `confissao-batista-londres-1689` | `confessional_paragraph` | 6-6 | 0.029877369007803793 |
| 4 | `confissao-batista-londres-1689_capitulo-1_paragrafo-4` | `confissao-batista-londres-1689` | `confessional_paragraph` | 3-4 | 0.02928692699490662 |
| 5 | `confissao-batista-londres-1689_capitulo-1_paragrafo-1` | `confissao-batista-londres-1689` | `confessional_paragraph` | 2-2 | 0.028958333333333336 |

### O crente pode perder a salvação?

- Resultados: `5`
- Documentos: `canones-de-dort, confissao-batista-londres-1689, confissao-fe-westminster`

| Rank | Chunk | Documento | Tipo | Páginas | RRF |
| ---: | --- | --- | --- | --- | ---: |
| 1 | `confissao-batista-londres-1689_capitulo-18_paragrafo-3` | `confissao-batista-londres-1689` | `confessional_paragraph` | 43-45 | 0.03131881575727918 |
| 2 | `confissao-batista-londres-1689_capitulo-18_paragrafo-4` | `confissao-batista-londres-1689` | `confessional_paragraph` | 45-46 | 0.030798389007344232 |
| 3 | `canones-de-dort_capitulo-04_rejeicao-erros_erro-03` | `canones-de-dort` | `error_refutation` | 29-29 | 0.03028233151183971 |
| 4 | `canones-de-dort_capitulo-04_artigo-08` | `canones-de-dort` | `doctrinal_article` | 25-26 | 0.029236022193768675 |
| 5 | `confissao-fe-westminster_capitulo-xviii_secao-iii` | `confissao-fe-westminster` | `confessional_section` | 41-41 | 0.029138513513513514 |

### O que é regeneração?

- Resultados: `5`
- Documentos: `canones-de-dort`

| Rank | Chunk | Documento | Tipo | Páginas | RRF |
| ---: | --- | --- | --- | --- | ---: |
| 1 | `canones-de-dort_capitulo-03_artigo-12` | `canones-de-dort` | `doctrinal_article` | 19-19 | 0.03278688524590164 |
| 2 | `canones-de-dort_capitulo-03_artigo-13` | `canones-de-dort` | `doctrinal_article` | 19-19 | 0.03225806451612903 |
| 3 | `canones-de-dort_capitulo-04_rejeicao-erros_erro-08` | `canones-de-dort` | `error_refutation` | 31-31 | 0.03149801587301587 |
| 4 | `canones-de-dort_capitulo-04_artigo-07` | `canones-de-dort` | `doctrinal_article` | 25-25 | 0.029857397504456328 |
| 5 | `canones-de-dort_capitulo-03_rejeicao-erros_erro-08` | `canones-de-dort` | `error_refutation` | 23-23 | 0.02976190476190476 |

### O que é expiação?

- Resultados: `5`
- Documentos: `canones-de-dort, catecismo-heidelberg, confissao-batista-londres-1689`

| Rank | Chunk | Documento | Tipo | Páginas | RRF |
| ---: | --- | --- | --- | --- | ---: |
| 1 | `catecismo-heidelberg_pergunta-037` | `catecismo-heidelberg` | `catechism_question_answer` | 9-9 | 0.0315136476426799 |
| 2 | `catecismo-heidelberg_pergunta-012` | `catecismo-heidelberg` | `catechism_question_answer` | 3-3 | 0.01639344262295082 |
| 3 | `canones-de-dort_introducao_pagina-01` | `canones-de-dort` | `introductory_context` | 1-1 | 0.01639344262295082 |
| 4 | `catecismo-heidelberg_pergunta-056` | `catecismo-heidelberg` | `catechism_question_answer` | 12-12 | 0.016129032258064516 |
| 5 | `confissao-batista-londres-1689_capitulo-15_paragrafo-5` | `confissao-batista-londres-1689` | `confessional_paragraph` | 36-37 | 0.015873015873015872 |

## Agregados

Documentos:

{
  "confissao-batista-londres-1689": 17,
  "canones-de-dort": 13,
  "catecismo-heidelberg": 7,
  "confissao-fe-westminster": 3
}

Tipos de chunk:

{
  "confessional_paragraph": 17,
  "catechism_question_answer": 7,
  "doctrinal_article": 6,
  "error_refutation": 6,
  "confessional_section": 3,
  "introductory_context": 1
}

## Fora do escopo

- Sem reranking neural.
- Sem recuperação hierárquica de documentos-pai.
- Sem geração de resposta com LLM.
