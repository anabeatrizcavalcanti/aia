# Relatório de retrieval vetorial

## Status

PASS

## Configuração consultada

- Collection: `solabot_reformed_v1`
- Diretório ChromaDB: `corpus/indexes/chroma/reformed`
- Modelo para embedding da pergunta: `text-embedding-3-large`
- Filtros padrão: `{'corpus_id': 'reformed', 'retrieval_namespace': 'reformed_confessional'}`
- Nota sobre score: Nesta etapa, o campo score repete a distância retornada pelo ChromaDB; valores menores indicam maior proximidade vetorial.

## Consultas executadas

### O que é o batismo?

- Top-k: 5
- Resultados retornados: 5
- Documentos recuperados: catecismo-heidelberg, confissao-batista-londres-1689, confissao-fe-westminster
- Tipos de chunk: catechism_question_answer, confessional_paragraph, confessional_section
- Observação: A consulta sobre batismo recuperou trechos confessionais sobre sacramentos, incluindo documentos que tratam diretamente do tema.

- `confissao-batista-londres-1689_capitulo-29_paragrafo-1` | `confissao-batista-londres-1689` | `confessional_paragraph` | páginas 74-74 | distância 0.37774646282196045
- `catecismo-heidelberg_pergunta-069` | `catecismo-heidelberg` | `catechism_question_answer` | páginas 15-15 | distância 0.39641451835632324
- `confissao-fe-westminster_capitulo-xxviii_secao-i` | `confissao-fe-westminster` | `confessional_section` | páginas 54-54 | distância 0.40666401386260986
- `confissao-batista-londres-1689_capitulo-29_paragrafo-4` | `confissao-batista-londres-1689` | `confessional_paragraph` | páginas 74-75 | distância 0.4128737449645996
- `catecismo-heidelberg_pergunta-073` | `catecismo-heidelberg` | `catechism_question_answer` | páginas 15-16 | distância 0.41750359535217285

### O que é necessário para a salvação?

- Top-k: 5
- Resultados retornados: 5
- Documentos recuperados: catecismo-heidelberg, confissao-batista-londres-1689
- Tipos de chunk: catechism_question_answer, confessional_paragraph
- Observação: A consulta sobre salvação retornou unidades catequéticas e confessionais úteis para a futura composição de resposta fundamentada.

- `catecismo-heidelberg_pergunta-030` | `catecismo-heidelberg` | `catechism_question_answer` | páginas 7-7 | distância 0.4570353627204895
- `catecismo-heidelberg_pergunta-029` | `catecismo-heidelberg` | `catechism_question_answer` | páginas 7-7 | distância 0.4577103853225708
- `confissao-batista-londres-1689_capitulo-18_paragrafo-3` | `confissao-batista-londres-1689` | `confessional_paragraph` | páginas 43-45 | distância 0.4683588743209839
- `catecismo-heidelberg_pergunta-012` | `catecismo-heidelberg` | `catechism_question_answer` | páginas 3-3 | distância 0.4718514680862427
- `confissao-batista-londres-1689_capitulo-14_paragrafo-2` | `confissao-batista-londres-1689` | `confessional_paragraph` | páginas 34-35 | distância 0.4720070958137512

### O que é eleição?

- Top-k: 5
- Resultados retornados: 5
- Documentos recuperados: canones-de-dort, confissao-batista-londres-1689
- Tipos de chunk: confessional_paragraph, doctrinal_article, error_refutation
- Observação: A consulta sobre eleição retornou Cânones de Dort entre os principais resultados, o que é coerente com a centralidade desse documento para o tema.

- `canones-de-dort_capitulo-01_artigo-07` | `canones-de-dort` | `doctrinal_article` | páginas 3-3 | distância 0.6099228858947754
- `confissao-batista-londres-1689_capitulo-26_paragrafo-9` | `confissao-batista-londres-1689` | `confessional_paragraph` | páginas 69-69 | distância 0.6226888298988342
- `canones-de-dort_capitulo-01_rejeicao-erros_erro-02` | `canones-de-dort` | `error_refutation` | páginas 7-7 | distância 0.6336961984634399
- `canones-de-dort_capitulo-01_artigo-14` | `canones-de-dort` | `doctrinal_article` | páginas 5-5 | distância 0.6468544006347656
- `canones-de-dort_capitulo-01_rejeicao-erros_erro-01` | `canones-de-dort` | `error_refutation` | páginas 7-7 | distância 0.6540249586105347

### O que é justificação?

- Top-k: 5
- Resultados retornados: 5
- Documentos recuperados: confissao-batista-londres-1689, confissao-fe-westminster
- Tipos de chunk: confessional_paragraph, confessional_section
- Observação: A consulta sobre justificação recuperou seções confessionais diretamente ligadas ao vocabulário soteriológico reformado.

- `confissao-batista-londres-1689_capitulo-11_paragrafo-1` | `confissao-batista-londres-1689` | `confessional_paragraph` | páginas 29-29 | distância 0.42806339263916016
- `confissao-fe-westminster_capitulo-xi_secao-i` | `confissao-fe-westminster` | `confessional_section` | páginas 33-33 | distância 0.4508723020553589
- `confissao-batista-londres-1689_capitulo-11_paragrafo-4` | `confissao-batista-londres-1689` | `confessional_paragraph` | páginas 30-31 | distância 0.45227885246276855
- `confissao-batista-londres-1689_capitulo-11_paragrafo-5` | `confissao-batista-londres-1689` | `confessional_paragraph` | páginas 31-31 | distância 0.46482837200164795
- `confissao-batista-londres-1689_capitulo-11_paragrafo-2` | `confissao-batista-londres-1689` | `confessional_paragraph` | páginas 29-30 | distância 0.4657236933708191

### O que a tradição reformada ensina sobre as Escrituras?

- Top-k: 5
- Resultados retornados: 5
- Documentos recuperados: confissao-batista-londres-1689, confissao-fe-westminster
- Tipos de chunk: confessional_paragraph, confessional_section
- Observação: A consulta sobre Escrituras recuperou capítulos confessionais sobre a doutrina da Palavra de Deus, preservando fonte e localização.

- `confissao-batista-londres-1689_capitulo-1_paragrafo-6` | `confissao-batista-londres-1689` | `confessional_paragraph` | páginas 4-5 | distância 0.3433920741081238
- `confissao-batista-londres-1689_capitulo-1_paragrafo-4` | `confissao-batista-londres-1689` | `confessional_paragraph` | páginas 3-4 | distância 0.35548168420791626
- `confissao-fe-westminster_capitulo-i_secao-vi` | `confissao-fe-westminster` | `confessional_section` | páginas 19-19 | distância 0.3563649654388428
- `confissao-batista-londres-1689_capitulo-1_paragrafo-1` | `confissao-batista-londres-1689` | `confessional_paragraph` | páginas 2-2 | distância 0.3610323667526245
- `confissao-batista-londres-1689_capitulo-1_paragrafo-10` | `confissao-batista-londres-1689` | `confessional_paragraph` | páginas 6-6 | distância 0.3678545355796814

### O crente pode perder a salvação?

- Top-k: 5
- Resultados retornados: 5
- Documentos recuperados: canones-de-dort, confissao-batista-londres-1689, confissao-fe-westminster
- Tipos de chunk: confessional_paragraph, confessional_section, doctrinal_article, error_refutation
- Observação: A consulta sobre perseverança retornou chunks doutrinários associados à salvação e à perseverança dos santos.

- `canones-de-dort_capitulo-04_rejeicao-erros_erro-03` | `canones-de-dort` | `error_refutation` | páginas 29-29 | distância 0.39286935329437256
- `confissao-batista-londres-1689_capitulo-17_paragrafo-1` | `confissao-batista-londres-1689` | `confessional_paragraph` | páginas 40-41 | distância 0.40777862071990967
- `confissao-batista-londres-1689_capitulo-18_paragrafo-4` | `confissao-batista-londres-1689` | `confessional_paragraph` | páginas 45-46 | distância 0.4167522192001343
- `confissao-fe-westminster_capitulo-xviii_secao-iv` | `confissao-fe-westminster` | `confessional_section` | páginas 41-41 | distância 0.42200690507888794
- `canones-de-dort_capitulo-04_artigo-04` | `canones-de-dort` | `doctrinal_article` | páginas 24-25 | distância 0.4253253936767578

## Documentos mais recuperados

{
  "confissao-batista-londres-1689": 15,
  "canones-de-dort": 6,
  "catecismo-heidelberg": 5,
  "confissao-fe-westminster": 4
}

## Tipos de chunk mais recuperados

{
  "confessional_paragraph": 15,
  "catechism_question_answer": 5,
  "confessional_section": 4,
  "doctrinal_article": 3,
  "error_refutation": 3
}

## Observações iniciais de qualidade

- A camada ainda avalia apenas recuperação vetorial simples, sem resposta final.
- Os resultados preservam fonte, tipo de chunk, páginas e identificador do chunk.
- A qualidade fina ainda dependerá de refinamentos como busca híbrida, RRF e reranking.
