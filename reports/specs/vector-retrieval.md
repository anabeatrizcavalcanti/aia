# Retrieval vetorial do corpus reformado

## Status

PASS

## Objetivo

Implementar a primeira camada de recuperação documental do SolaBot: gerar embedding da pergunta, consultar o índice ChromaDB do corpus reformado e retornar chunks com metadados e fontes rastreáveis.

## Entradas utilizadas

- `reports/specs/openai-embeddings.md`
- `reports/specs/chroma-vector-index.md`
- `corpus/processed/chunks/reformed/all_chunks_for_embeddings.jsonl`
- `corpus/processed/embeddings/reformed/embedding_manifest.json`
- `corpus/indexes/chroma/reformed/`

## Implementação do retriever vetorial

Foram criados módulos específicos para geração de embedding de consulta, representação estruturada dos resultados e consulta vetorial no ChromaDB.

## Configuração de filtros

Todas as consultas mantêm os filtros obrigatórios `corpus_id=reformed` e `retrieval_namespace=reformed_confessional`. Filtros adicionais, como documento ou tipo de chunk, são combinados sem remover essa restrição do corpus ativo.

## Consultas de validação

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

## Resultados observados

- Documentos mais recuperados: `{'confissao-batista-londres-1689': 15, 'canones-de-dort': 6, 'catecismo-heidelberg': 5, 'confissao-fe-westminster': 4}`
- Tipos de chunk mais recuperados: `{'confessional_paragraph': 15, 'catechism_question_answer': 5, 'confessional_section': 4, 'doctrinal_article': 3, 'error_refutation': 3}`
- Erro de retrieval: nenhuma ocorrência

## Validações executadas

```bash
python scripts/pipeline/query_vector_retriever.py "O que é o batismo?" --top-k 5
python scripts/pipeline/query_vector_retriever.py "O que é eleição?" --top-k 5
python scripts/pipeline/query_vector_retriever.py "O que é justificação?" --top-k 5
python -m py_compile src/sola_bot/retrieval/query_embedder.py
python -m py_compile src/sola_bot/retrieval/retrieval_result.py
python -m py_compile src/sola_bot/retrieval/vector_retriever.py
python -m py_compile scripts/pipeline/query_vector_retriever.py
python -m pytest tests/test_vector_retriever.py
```

## Pontos de atenção

- O campo `score` replica a distância retornada pelo ChromaDB nesta etapa.
- Valores menores de distância indicam maior proximidade vetorial.
- Esta camada ainda não decide resposta final nem aplica política de evidência.
- A consulta sobre eleição trouxe um chunk de Londres 1689 sobre escolha de oficiais da igreja entre os resultados; esse tipo de ruído é esperado no baseline vetorial simples e deve ser tratado nas próximas camadas de recuperação.

## O que não foi feito

- não foi implementado chatbot final;
- não houve geração de resposta com LLM;
- não houve chamada a modelo de chat da OpenAI;
- não foi feita avaliação com documentos de outras tradições;
- não houve upload de documentos pelo usuário;
- não houve alteração de chunks, embeddings ou PDFs;
- não houve nova extração, normalização, chunking ou indexação;
- não foi implementada busca híbrida BM25 + RRF;
- não foi implementado reranking;
- não foi implementado parent/hierarchical retrieval.

