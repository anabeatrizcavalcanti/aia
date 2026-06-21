# Relatorio de normalizacao do corpus reformado

## Status

PASS

## Sintese

A normalizacao processou 4 documentos extraidos. As paginas foram preservadas como unidade de rastreabilidade, e as acoes aplicadas foram registradas pagina a pagina.

## Documentos normalizados

### Cânones de Dort

- `document_id`: `canones-de-dort`
- Paginas normalizadas: 33
- Caracteres normalizados: 72297
- Acoes aplicadas: {'normalized_excess_blank_lines': 33, 'normalized_whitespace': 33, 'recomposed_safe_hyphenation': 2}
- Zonas preliminares: {'confessional_body': 30, 'introductory_material': 1, 'unknown': 2}
- Marcadores estruturais preservados: {'Capítulo da Doutrina': True, 'Artigo': True, 'Rejeição de Erros': True, 'Refutação': True}
- Paginas com avisos: nenhuma ocorrencia
- JSON: `corpus/processed/normalized/reformed/canones-de-dort.normalized.json`
- TXT: `corpus/processed/normalized/reformed/canones-de-dort.normalized.txt`

### Catecismo de Heidelberg

- `document_id`: `catecismo-heidelberg`
- Paginas normalizadas: 29
- Caracteres normalizados: 61661
- Acoes aplicadas: {'normalized_excess_blank_lines': 29, 'normalized_whitespace': 29, 'recomposed_safe_hyphenation': 1}
- Zonas preliminares: {'confessional_body': 28, 'introductory_material': 1}
- Marcadores estruturais preservados: {'Dia do Senhor': True, 'P.': True, 'R.': True}
- Paginas com avisos: nenhuma ocorrencia
- JSON: `corpus/processed/normalized/reformed/catecismo-heidelberg.normalized.json`
- TXT: `corpus/processed/normalized/reformed/catecismo-heidelberg.normalized.txt`

### Confissão Batista de Londres de 1689

- `document_id`: `confissao-batista-londres-1689`
- Paginas normalizadas: 81
- Caracteres normalizados: 282900
- Acoes aplicadas: {'normalized_excess_blank_lines': 81, 'normalized_whitespace': 71, 'recomposed_safe_hyphenation': 10}
- Zonas preliminares: {'confessional_body': 70, 'introductory_material': 1, 'special_layout': 1, 'unknown': 9}
- Marcadores estruturais preservados: {'CAPÍTULO': True, 'AS SAGRADAS ESCRITURAS': True, '1.': True}
- Paginas com avisos: nenhuma ocorrencia
- JSON: `corpus/processed/normalized/reformed/confissao-batista-londres-1689.normalized.json`
- TXT: `corpus/processed/normalized/reformed/confissao-batista-londres-1689.normalized.txt`

### Confissão de Fé de Westminster

- `document_id`: `confissao-fe-westminster`
- Paginas normalizadas: 60
- Caracteres normalizados: 129667
- Acoes aplicadas: {'normalized_excess_blank_lines': 60, 'normalized_whitespace': 60, 'recomposed_safe_hyphenation': 5}
- Zonas preliminares: {'confessional_body': 40, 'introductory_material': 14, 'special_layout': 1, 'table_of_contents': 1, 'unknown': 4}
- Marcadores estruturais preservados: {'CAPÍTULO': True, 'DA ESCRITURA SAGRADA': True, 'I.': True}
- Paginas com avisos: [1]
- JSON: `corpus/processed/normalized/reformed/confissao-fe-westminster.normalized.json`
- TXT: `corpus/processed/normalized/reformed/confissao-fe-westminster.normalized.txt`

## Escopo mantido fora desta etapa

- Nao foram gerados chunks finais.
- Nao foram gerados embeddings.
- Nao foi criado indice vetorial.
- Nao houve chamada a OpenAI.
- Nao houve OCR.
- Nao houve alteracao manual de conteudo doutrinario.
