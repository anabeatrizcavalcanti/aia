# Relatório de recuperação hierárquica

## Status

PASS

## Configuração

{
  "strategy": "structural_window",
  "anchor_source": "reranked_retriever",
  "reranked_top_k": 5,
  "parent_context_max_chars": 9000,
  "sibling_window_before": 1,
  "sibling_window_after": 1,
  "include_full_parent_when_small": true,
  "full_parent_max_chars": 7000,
  "include_metadata_header": true,
  "preserve_anchor_first": true,
  "default_filters": {
    "corpus_id": "reformed",
    "retrieval_namespace": "reformed_confessional"
  }
}

## Corpus hierárquico

- Arquivo de chunks: `corpus/processed/chunks/reformed/all_chunks_for_embeddings.jsonl`
- Chunks carregados: `583`
- Grupos estruturais identificados: `152`

## Consultas

### O que é o batismo?

- Top-k de âncoras: `5`
- Contextos gerados: `5`

| Rank | Âncora | Documento | Unidade | Chunks | Páginas | Status |
| ---: | --- | --- | --- | ---: | --- | --- |
| 1 | `confissao-batista-londres-1689_capitulo-29_paragrafo-1` | `confissao-batista-londres-1689` | `CAPÍTULO 29 — BATISMO` | 4 | 74-75 | `expanded` |
| 2 | `confissao-fe-westminster_capitulo-xxviii_secao-i` | `confissao-fe-westminster` | `CAPÍTULO XXVIII — DO BATISMO` | 7 | 54 | `expanded` |
| 3 | `confissao-batista-londres-1689_capitulo-28_paragrafo-1` | `confissao-batista-londres-1689` | `CAPÍTULO 28 — BATISMO E CEIA DO SENHOR` | 2 | 73 | `expanded` |
| 4 | `confissao-batista-londres-1689_capitulo-29_paragrafo-2` | `confissao-batista-londres-1689` | `CAPÍTULO 29 — BATISMO` | 4 | 74-75 | `expanded` |
| 5 | `confissao-batista-londres-1689_capitulo-29_paragrafo-4` | `confissao-batista-londres-1689` | `CAPÍTULO 29 — BATISMO` | 4 | 74-75 | `expanded` |

### O que é necessário para a salvação?

- Top-k de âncoras: `5`
- Contextos gerados: `5`

| Rank | Âncora | Documento | Unidade | Chunks | Páginas | Status |
| ---: | --- | --- | --- | ---: | --- | --- |
| 1 | `confissao-batista-londres-1689_capitulo-1_paragrafo-1` | `confissao-batista-londres-1689` | `CAPÍTULO 1 — AS SAGRADAS ESCRITURAS` | 2 | 2-3 | `expanded` |
| 2 | `confissao-batista-londres-1689_capitulo-15_paragrafo-5` | `confissao-batista-londres-1689` | `CAPÍTULO 15 — ARREPENDIMENTO PARA VIDA E SALVAÇÃO` | 5 | 35-37 | `expanded` |
| 3 | `confissao-batista-londres-1689_capitulo-14_paragrafo-2` | `confissao-batista-londres-1689` | `CAPÍTULO 14 — FÉ SALVADORA` | 3 | 34-35 | `expanded` |
| 4 | `catecismo-heidelberg_pergunta-040` | `catecismo-heidelberg` | `Dia do Senhor 16` | 5 | 9-10 | `expanded` |
| 5 | `confissao-batista-londres-1689_capitulo-15_paragrafo-3` | `confissao-batista-londres-1689` | `CAPÍTULO 15 — ARREPENDIMENTO PARA VIDA E SALVAÇÃO` | 5 | 35-37 | `expanded` |

### O que é eleição?

- Top-k de âncoras: `5`
- Contextos gerados: `5`

| Rank | Âncora | Documento | Unidade | Chunks | Páginas | Status |
| ---: | --- | --- | --- | ---: | --- | --- |
| 1 | `canones-de-dort_capitulo-01_artigo-07` | `canones-de-dort` | `Primeiro Capítulo da Doutrina — A Eleição e a Reprovação Divinas` | 3 | 3-4 | `expanded` |
| 2 | `canones-de-dort_capitulo-01_artigo-09` | `canones-de-dort` | `Primeiro Capítulo da Doutrina — A Eleição e a Reprovação Divinas` | 3 | 3-4 | `expanded` |
| 3 | `canones-de-dort_capitulo-01_artigo-10` | `canones-de-dort` | `Primeiro Capítulo da Doutrina — A Eleição e a Reprovação Divinas` | 3 | 4 | `expanded` |
| 4 | `canones-de-dort_capitulo-01_rejeicao-erros_erro-05` | `canones-de-dort` | `Primeiro Capítulo da Doutrina — A Eleição e a Reprovação Divinas` | 3 | 8-9 | `expanded` |
| 5 | `canones-de-dort_capitulo-01_rejeicao-erros_erro-01` | `canones-de-dort` | `Primeiro Capítulo da Doutrina — A Eleição e a Reprovação Divinas` | 3 | 6-7 | `expanded` |

### O que é justificação?

- Top-k de âncoras: `5`
- Contextos gerados: `5`

| Rank | Âncora | Documento | Unidade | Chunks | Páginas | Status |
| ---: | --- | --- | --- | ---: | --- | --- |
| 1 | `confissao-batista-londres-1689_capitulo-11_paragrafo-1` | `confissao-batista-londres-1689` | `CAPÍTULO 11 — A JUSTIFICAÇÃO` | 2 | 29-30 | `expanded` |
| 2 | `confissao-batista-londres-1689_capitulo-11_paragrafo-3` | `confissao-batista-londres-1689` | `CAPÍTULO 11 — A JUSTIFICAÇÃO` | 3 | 29-31 | `expanded` |
| 3 | `confissao-batista-londres-1689_capitulo-11_paragrafo-5` | `confissao-batista-londres-1689` | `CAPÍTULO 11 — A JUSTIFICAÇÃO` | 3 | 30-31 | `expanded` |
| 4 | `confissao-fe-westminster_capitulo-xi_secao-i` | `confissao-fe-westminster` | `CAPÍTULO XI — DA JUSTIFICAÇÃO` | 6 | 33 | `expanded` |
| 5 | `confissao-batista-londres-1689_capitulo-11_paragrafo-4` | `confissao-batista-londres-1689` | `CAPÍTULO 11 — A JUSTIFICAÇÃO` | 3 | 30-31 | `expanded` |

### O que a tradição reformada ensina sobre as Escrituras?

- Top-k de âncoras: `5`
- Contextos gerados: `5`

| Rank | Âncora | Documento | Unidade | Chunks | Páginas | Status |
| ---: | --- | --- | --- | ---: | --- | --- |
| 1 | `confissao-fe-westminster_introducao_pagina-12` | `confissao-fe-westminster` | `Material introdutório` | 1 | 12 | `anchor_only` |
| 2 | `canones-de-dort_introducao_pagina-01` | `canones-de-dort` | `Material introdutório` | 1 | 1 | `anchor_only` |
| 3 | `confissao-fe-westminster_introducao_pagina-08` | `confissao-fe-westminster` | `Material introdutório` | 1 | 8 | `anchor_only` |
| 4 | `confissao-batista-londres-1689_capitulo-1_paragrafo-5` | `confissao-batista-londres-1689` | `CAPÍTULO 1 — AS SAGRADAS ESCRITURAS` | 3 | 3-5 | `expanded` |
| 5 | `confissao-batista-londres-1689_capitulo-1_paragrafo-6` | `confissao-batista-londres-1689` | `CAPÍTULO 1 — AS SAGRADAS ESCRITURAS` | 3 | 4-5 | `expanded` |

### O crente pode perder a salvação?

- Top-k de âncoras: `5`
- Contextos gerados: `5`

| Rank | Âncora | Documento | Unidade | Chunks | Páginas | Status |
| ---: | --- | --- | --- | ---: | --- | --- |
| 1 | `confissao-fe-westminster_capitulo-xviii_secao-iv` | `confissao-fe-westminster` | `CAPÍTULO XVIII — DA CERTEZA DA GRAÇA E DA SALVAÇÃO` | 4 | 41 | `expanded` |
| 2 | `canones-de-dort_capitulo-04_rejeicao-erros_erro-03` | `canones-de-dort` | `Quinto Capítulo da Doutrina — A Perseverança dos Santos` | 3 | 28-29 | `expanded` |
| 3 | `confissao-batista-londres-1689_capitulo-18_paragrafo-4` | `confissao-batista-londres-1689` | `CAPÍTULO 18 — A CERTEZA DA GRAÇA E DA SALVAÇÃO` | 2 | 43-46 | `expanded` |
| 4 | `canones-de-dort_capitulo-04_artigo-09` | `canones-de-dort` | `Quinto Capítulo da Doutrina — A Perseverança dos Santos` | 3 | 25-26 | `expanded` |
| 5 | `confissao-fe-westminster_capitulo-xviii_secao-iii` | `confissao-fe-westminster` | `CAPÍTULO XVIII — DA CERTEZA DA GRAÇA E DA SALVAÇÃO` | 4 | 41 | `expanded` |

### O que é regeneração?

- Top-k de âncoras: `5`
- Contextos gerados: `5`

| Rank | Âncora | Documento | Unidade | Chunks | Páginas | Status |
| ---: | --- | --- | --- | ---: | --- | --- |
| 1 | `canones-de-dort_capitulo-03_artigo-12` | `canones-de-dort` | `Terceiro e Quarto Capítulos da Doutrina — A Corrupção do Homem, a sua Conversão a Deus e o Modo como isso Ocorre` | 3 | 18-19 | `expanded` |
| 2 | `confissao-batista-londres-1689_capitulo-13_paragrafo-1` | `confissao-batista-londres-1689` | `CAPÍTULO 13 — A SANTIFICAÇÃO` | 3 | 32-34 | `expanded` |
| 3 | `canones-de-dort_capitulo-03_artigo-13` | `canones-de-dort` | `Terceiro e Quarto Capítulos da Doutrina — A Corrupção do Homem, a sua Conversão a Deus e o Modo como isso Ocorre` | 3 | 19 | `expanded` |
| 4 | `canones-de-dort_capitulo-03_artigo-16` | `canones-de-dort` | `Terceiro e Quarto Capítulos da Doutrina — A Corrupção do Homem, a sua Conversão a Deus e o Modo como isso Ocorre` | 3 | 19-20 | `expanded` |
| 5 | `confissao-batista-londres-1689_capitulo-15_paragrafo-1` | `confissao-batista-londres-1689` | `CAPÍTULO 15 — ARREPENDIMENTO PARA VIDA E SALVAÇÃO` | 5 | 35-37 | `expanded` |

### O que é expiação?

- Top-k de âncoras: `5`
- Contextos gerados: `5`

| Rank | Âncora | Documento | Unidade | Chunks | Páginas | Status |
| ---: | --- | --- | --- | ---: | --- | --- |
| 1 | `canones-de-dort_introducao_pagina-01` | `canones-de-dort` | `Material introdutório` | 1 | 1 | `anchor_only` |
| 2 | `confissao-batista-londres-1689_capitulo-11_paragrafo-3` | `confissao-batista-londres-1689` | `CAPÍTULO 11 — A JUSTIFICAÇÃO` | 3 | 29-31 | `expanded` |
| 3 | `confissao-batista-londres-1689_capitulo-11_paragrafo-5` | `confissao-batista-londres-1689` | `CAPÍTULO 11 — A JUSTIFICAÇÃO` | 3 | 30-31 | `expanded` |
| 4 | `confissao-batista-londres-1689_capitulo-2_paragrafo-1` | `confissao-batista-londres-1689` | `CAPÍTULO 2 — DEUS E A SANTÍSSIMA TRINDADE` | 1 | 6-8 | `anchor_only` |
| 5 | `confissao-batista-londres-1689_capitulo-15_paragrafo-3` | `confissao-batista-londres-1689` | `CAPÍTULO 15 — ARREPENDIMENTO PARA VIDA E SALVAÇÃO` | 5 | 35-37 | `expanded` |

## Agregados

Documentos:

{
  "confissao-batista-londres-1689": 21,
  "canones-de-dort": 12,
  "confissao-fe-westminster": 6,
  "catecismo-heidelberg": 1
}

Tipos de chunk âncora:

{
  "confessional_paragraph": 21,
  "doctrinal_article": 7,
  "confessional_section": 4,
  "introductory_context": 4,
  "error_refutation": 3,
  "catechism_question_answer": 1
}

Status de expansão:

{
  "expanded": 35,
  "anchor_only": 5
}

## Notas técnicas

- Execução real do RerankedRetriever: `executada`.
- Bloqueio: `nenhum`.
- A expansão usa apenas chunks do mesmo documento e da mesma chave estrutural.
- O chunk âncora é colocado antes dos trechos relacionados.

## Limitações

- A chave estrutural depende dos metadados já presentes nos chunks.
- A expansão usa janela estrutural simples, sem sumarização e sem geração textual.
- Contextos longos são limitados por caracteres.
