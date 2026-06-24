# Extração do corpus reformado

## Status

PARTIAL

## Resumo

Foram processados 4 PDFs a partir do manifesto reformado. O texto extraído foi salvo por página, com metadados suficientes para manter a rastreabilidade até o arquivo bruto.

## Documentos

### Cânones de Dort

- `document_id`: `canones-de-dort`
- PDF: `corpus/raw/reformed/Os-Canones-de-Dort.pdf`
- Páginas: 33
- Caracteres extraídos: 91456
- Páginas vazias: nenhuma
- Páginas muito curtas: 33

### Catecismo de Heidelberg

- `document_id`: `catecismo-heidelberg`
- PDF: `corpus/raw/reformed/O CATECISMO DE HEIDELBERG (Portuguese).pdf`
- Páginas: 29
- Caracteres extraídos: 62653
- Páginas vazias: nenhuma
- Páginas muito curtas: nenhuma

### Confissão Batista de Londres de 1689

- `document_id`: `confissao-batista-londres-1689`
- PDF: `corpus/raw/reformed/A Confissão de Fé Batista de Londres de 1689.pdf`
- Páginas: 81
- Caracteres extraídos: 283175
- Páginas vazias: nenhuma
- Páginas muito curtas: nenhuma

### Confissão de Fé de Westminster

- `document_id`: `confissao-fe-westminster`
- PDF: `corpus/raw/reformed/A_Confissao_de_Fe_de_Westminster_1647_Or.pdf`
- Páginas: 60
- Caracteres extraídos: 131783
- Páginas vazias: 1
- Páginas muito curtas: 2

## Arquivos gerados

Para cada documento foram criados:

- `<document_id>.extracted.json`
- `<document_id>.extracted.txt`

Diretório: `corpus/processed/extracted/reformed/`.

## Observações

A página 1 de Westminster não retornou texto extraível. Nenhum OCR foi aplicado. Não houve geração de chunks, embeddings ou índice vetorial.
