# Relatório de reranking neural

## Status

PASS

## Parâmetros

- Hybrid candidate k: `20`
- Final top-k: `5`
- Reranker model: `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`
- Max text chars: `3500`
- Filtros padrão: `{'corpus_id': 'reformed', 'retrieval_namespace': 'reformed_confessional'}`

## Arquivos e índices

- Hybrid report: `corpus/reports/retrieval/hybrid-retrieval-report.json`.
- Chunks: `corpus/processed/chunks/reformed/all_chunks_for_embeddings.jsonl`.
- Índice ChromaDB: `corpus/indexes/chroma/reformed/`.
- Collection: `solabot_reformed_v1`.

## Dependências

- sentence-transformers: `True`
- CrossEncoder: `sentence_transformers.CrossEncoder`
- Modelo: `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`

## Consultas

### O que é o batismo?

- Candidatos híbridos: `20`
- Resultados finais: `5`

| Rank | Chunk | Documento | Tipo | Páginas | Pré-rank | RRF | Reranker |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: |
| 1 | `confissao-batista-londres-1689_capitulo-29_paragrafo-1` | `confissao-batista-londres-1689` | `confessional_paragraph` | 74-74 | 1 | 0.03252247488101534 | 4.666769027709961 |
| 2 | `confissao-fe-westminster_capitulo-xxviii_secao-i` | `confissao-fe-westminster` | `confessional_section` | 54-54 | 10 | 0.028373015873015873 | 3.4914698600769043 |
| 3 | `confissao-batista-londres-1689_capitulo-28_paragrafo-1` | `confissao-batista-londres-1689` | `confessional_paragraph` | 73-73 | 9 | 0.02844551282051282 | 0.0654543861746788 |
| 4 | `confissao-batista-londres-1689_capitulo-29_paragrafo-2` | `confissao-batista-londres-1689` | `confessional_paragraph` | 74-74 | 5 | 0.02976190476190476 | -1.2073619365692139 |
| 5 | `confissao-batista-londres-1689_capitulo-29_paragrafo-4` | `confissao-batista-londres-1689` | `confessional_paragraph` | 74-75 | 3 | 0.030776515151515152 | -1.5952078104019165 |

### O que é necessário para a salvação?

- Candidatos híbridos: `20`
- Resultados finais: `5`

| Rank | Chunk | Documento | Tipo | Páginas | Pré-rank | RRF | Reranker |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: |
| 1 | `confissao-batista-londres-1689_capitulo-1_paragrafo-1` | `confissao-batista-londres-1689` | `confessional_paragraph` | 2-2 | 10 | 0.015384615384615385 | -2.0728206634521484 |
| 2 | `confissao-batista-londres-1689_capitulo-15_paragrafo-5` | `confissao-batista-londres-1689` | `confessional_paragraph` | 36-37 | 2 | 0.02819138376017471 | -2.4478888511657715 |
| 3 | `confissao-batista-londres-1689_capitulo-14_paragrafo-2` | `confissao-batista-londres-1689` | `confessional_paragraph` | 34-35 | 9 | 0.015384615384615385 | -2.480576753616333 |
| 4 | `catecismo-heidelberg_pergunta-040` | `catecismo-heidelberg` | `catechism_question_answer` | 9-9 | 20 | 0.014084507042253521 | -3.581123113632202 |
| 5 | `confissao-batista-londres-1689_capitulo-15_paragrafo-3` | `confissao-batista-londres-1689` | `confessional_paragraph` | 36-36 | 18 | 0.014285714285714285 | -3.607107162475586 |

### O que é eleição?

- Candidatos híbridos: `20`
- Resultados finais: `5`

| Rank | Chunk | Documento | Tipo | Páginas | Pré-rank | RRF | Reranker |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: |
| 1 | `canones-de-dort_capitulo-01_artigo-07` | `canones-de-dort` | `doctrinal_article` | 3-3 | 4 | 0.02938045560996381 | 3.167187213897705 |
| 2 | `canones-de-dort_capitulo-01_artigo-09` | `canones-de-dort` | `doctrinal_article` | 4-4 | 8 | 0.02854251012145749 | -0.32958459854125977 |
| 3 | `canones-de-dort_capitulo-01_artigo-10` | `canones-de-dort` | `doctrinal_article` | 4-4 | 7 | 0.028991596638655463 | -1.4851658344268799 |
| 4 | `canones-de-dort_capitulo-01_rejeicao-erros_erro-05` | `canones-de-dort` | `error_refutation` | 8-9 | 2 | 0.03009207275993712 | -1.595402717590332 |
| 5 | `canones-de-dort_capitulo-01_rejeicao-erros_erro-01` | `canones-de-dort` | `error_refutation` | 7-7 | 3 | 0.029877369007803793 | -1.8651840686798096 |

### O que é justificação?

- Candidatos híbridos: `20`
- Resultados finais: `5`

| Rank | Chunk | Documento | Tipo | Páginas | Pré-rank | RRF | Reranker |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: |
| 1 | `confissao-batista-londres-1689_capitulo-11_paragrafo-1` | `confissao-batista-londres-1689` | `confessional_paragraph` | 29-29 | 2 | 0.031544957774465976 | -0.11080422252416611 |
| 2 | `confissao-batista-londres-1689_capitulo-11_paragrafo-3` | `confissao-batista-londres-1689` | `confessional_paragraph` | 30-30 | 9 | 0.029211087420042643 | -1.272689700126648 |
| 3 | `confissao-batista-londres-1689_capitulo-11_paragrafo-5` | `confissao-batista-londres-1689` | `confessional_paragraph` | 31-31 | 10 | 0.02844551282051282 | -1.3412655591964722 |
| 4 | `confissao-fe-westminster_capitulo-xi_secao-i` | `confissao-fe-westminster` | `confessional_section` | 33-33 | 3 | 0.030834914611005692 | -1.9190847873687744 |
| 5 | `confissao-batista-londres-1689_capitulo-11_paragrafo-4` | `confissao-batista-londres-1689` | `confessional_paragraph` | 30-31 | 5 | 0.02976190476190476 | -1.9942662715911865 |

### O que a tradição reformada ensina sobre as Escrituras?

- Candidatos híbridos: `20`
- Resultados finais: `5`

| Rank | Chunk | Documento | Tipo | Páginas | Pré-rank | RRF | Reranker |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: |
| 1 | `confissao-fe-westminster_introducao_pagina-12` | `confissao-fe-westminster` | `introductory_context` | 12-12 | 12 | 0.015873015873015872 | 0.6452843546867371 |
| 2 | `canones-de-dort_introducao_pagina-01` | `canones-de-dort` | `introductory_context` | 1-1 | 17 | 0.014705882352941176 | -1.046289324760437 |
| 3 | `confissao-fe-westminster_introducao_pagina-08` | `confissao-fe-westminster` | `introductory_context` | 8-8 | 10 | 0.01639344262295082 | -1.0743252038955688 |
| 4 | `confissao-batista-londres-1689_capitulo-1_paragrafo-5` | `confissao-batista-londres-1689` | `confessional_paragraph` | 4-4 | 2 | 0.03128054740957967 | -3.380352020263672 |
| 5 | `confissao-batista-londres-1689_capitulo-1_paragrafo-6` | `confissao-batista-londres-1689` | `confessional_paragraph` | 4-5 | 1 | 0.03177805800756621 | -3.886536121368408 |

### O crente pode perder a salvação?

- Candidatos híbridos: `20`
- Resultados finais: `5`

| Rank | Chunk | Documento | Tipo | Páginas | Pré-rank | RRF | Reranker |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: |
| 1 | `confissao-fe-westminster_capitulo-xviii_secao-iv` | `confissao-fe-westminster` | `confessional_section` | 41-41 | 9 | 0.015625 | 5.447536468505859 |
| 2 | `canones-de-dort_capitulo-04_rejeicao-erros_erro-03` | `canones-de-dort` | `error_refutation` | 29-29 | 3 | 0.03028233151183971 | 3.508094072341919 |
| 3 | `confissao-batista-londres-1689_capitulo-18_paragrafo-4` | `confissao-batista-londres-1689` | `confessional_paragraph` | 45-46 | 2 | 0.030798389007344232 | 2.078270673751831 |
| 4 | `canones-de-dort_capitulo-04_artigo-09` | `canones-de-dort` | `doctrinal_article` | 26-26 | 13 | 0.014705882352941176 | 0.6150314807891846 |
| 5 | `confissao-fe-westminster_capitulo-xviii_secao-iii` | `confissao-fe-westminster` | `confessional_section` | 41-41 | 5 | 0.029138513513513514 | -0.005078836344182491 |

### O que é regeneração?

- Candidatos híbridos: `20`
- Resultados finais: `5`

| Rank | Chunk | Documento | Tipo | Páginas | Pré-rank | RRF | Reranker |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: |
| 1 | `canones-de-dort_capitulo-03_artigo-12` | `canones-de-dort` | `doctrinal_article` | 19-19 | 1 | 0.03278688524590164 | 0.38462033867836 |
| 2 | `confissao-batista-londres-1689_capitulo-13_paragrafo-1` | `confissao-batista-londres-1689` | `confessional_paragraph` | 32-33 | 20 | 0.0136986301369863 | -2.4173238277435303 |
| 3 | `canones-de-dort_capitulo-03_artigo-13` | `canones-de-dort` | `doctrinal_article` | 19-19 | 2 | 0.03225806451612903 | -2.531557321548462 |
| 4 | `canones-de-dort_capitulo-03_artigo-16` | `canones-de-dort` | `doctrinal_article` | 20-20 | 6 | 0.028205128205128206 | -2.7363061904907227 |
| 5 | `confissao-batista-londres-1689_capitulo-15_paragrafo-1` | `confissao-batista-londres-1689` | `confessional_paragraph` | 35-36 | 13 | 0.014492753623188406 | -2.8636913299560547 |

### O que é expiação?

- Candidatos híbridos: `20`
- Resultados finais: `5`

| Rank | Chunk | Documento | Tipo | Páginas | Pré-rank | RRF | Reranker |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: |
| 1 | `canones-de-dort_introducao_pagina-01` | `canones-de-dort` | `introductory_context` | 1-1 | 3 | 0.01639344262295082 | -2.8270480632781982 |
| 2 | `confissao-batista-londres-1689_capitulo-11_paragrafo-3` | `confissao-batista-londres-1689` | `confessional_paragraph` | 30-30 | 18 | 0.014285714285714285 | -4.455896854400635 |
| 3 | `confissao-batista-londres-1689_capitulo-11_paragrafo-5` | `confissao-batista-londres-1689` | `confessional_paragraph` | 31-31 | 12 | 0.014925373134328358 | -4.639720916748047 |
| 4 | `confissao-batista-londres-1689_capitulo-2_paragrafo-1` | `confissao-batista-londres-1689` | `confessional_paragraph` | 6-8 | 19 | 0.014285714285714285 | -4.8266072273254395 |
| 5 | `confissao-batista-londres-1689_capitulo-15_paragrafo-3` | `confissao-batista-londres-1689` | `confessional_paragraph` | 36-36 | 16 | 0.014492753623188406 | -4.940528869628906 |

## Mudanças de ranking

{
  "items_with_rank_delta": 40,
  "moved_up": 27,
  "moved_down": 8,
  "unchanged": 5,
  "max_position_gain": 18,
  "max_position_loss": -4
}

## Agregados

Documentos:

{
  "confissao-batista-londres-1689": 21,
  "canones-de-dort": 12,
  "confissao-fe-westminster": 6,
  "catecismo-heidelberg": 1
}

Tipos de chunk:

{
  "confessional_paragraph": 21,
  "doctrinal_article": 7,
  "confessional_section": 4,
  "introductory_context": 4,
  "error_refutation": 3,
  "catechism_question_answer": 1
}

## Notas técnicas

- Execução real do CrossEncoder: `executada`.
- Bloqueio: `nenhum`.

## Limitações

- Sem parent/hierarchical retrieval.
- Sem política de recusa baseada em evidência.
- Sem geração de resposta.
