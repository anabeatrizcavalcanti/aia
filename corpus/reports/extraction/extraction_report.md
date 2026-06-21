# Relatorio de extracao do corpus reformado

## Status

PARTIAL

## Sintese

A extracao processou 4 documentos do corpus reformado a partir do manifesto validado. O texto foi preservado por pagina, com caminho bruto, identificador documental e metadados confessionais.

## Documentos processados

### Cânones de Dort

- `document_id`: `canones-de-dort`
- PDF bruto: `corpus/raw/reformed/Os-Canones-de-Dort.pdf`
- Paginas extraidas: 33
- Caracteres extraidos: 91456
- Paginas vazias: nenhuma ocorrencia
- Paginas muito curtas: [33]
- JSON: `corpus/processed/extracted/reformed/canones-de-dort.extracted.json`
- TXT: `corpus/processed/extracted/reformed/canones-de-dort.extracted.txt`

### Catecismo de Heidelberg

- `document_id`: `catecismo-heidelberg`
- PDF bruto: `corpus/raw/reformed/O CATECISMO DE HEIDELBERG (Portuguese).pdf`
- Paginas extraidas: 29
- Caracteres extraidos: 62653
- Paginas vazias: nenhuma ocorrencia
- Paginas muito curtas: nenhuma ocorrencia
- JSON: `corpus/processed/extracted/reformed/catecismo-heidelberg.extracted.json`
- TXT: `corpus/processed/extracted/reformed/catecismo-heidelberg.extracted.txt`

### Confissão Batista de Londres de 1689

- `document_id`: `confissao-batista-londres-1689`
- PDF bruto: `corpus/raw/reformed/A Confissão de Fé Batista de Londres de 1689.pdf`
- Paginas extraidas: 81
- Caracteres extraidos: 283175
- Paginas vazias: nenhuma ocorrencia
- Paginas muito curtas: nenhuma ocorrencia
- JSON: `corpus/processed/extracted/reformed/confissao-batista-londres-1689.extracted.json`
- TXT: `corpus/processed/extracted/reformed/confissao-batista-londres-1689.extracted.txt`

### Confissão de Fé de Westminster

- `document_id`: `confissao-fe-westminster`
- PDF bruto: `corpus/raw/reformed/A_Confissao_de_Fe_de_Westminster_1647_Or.pdf`
- Paginas extraidas: 60
- Caracteres extraidos: 131783
- Paginas vazias: [1]
- Paginas muito curtas: [2]
- JSON: `corpus/processed/extracted/reformed/confissao-fe-westminster.extracted.json`
- TXT: `corpus/processed/extracted/reformed/confissao-fe-westminster.extracted.txt`

## Escopo mantido fora desta etapa

- Nao foram gerados chunks finais.
- Nao foram gerados embeddings.
- Nao foi criado indice vetorial.
- Nao houve chamada a OpenAI.
- Nao houve OCR.
- Nao houve alteracao manual de conteudo doutrinario.
