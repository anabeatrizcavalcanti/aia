# Auditoria estrutural — Confissão de Fé de Westminster

## Registro

O JSON estrutural da Confissão de Fé de Westminster foi reorganizado em torno de capítulos e seções em algarismos romanos. As referências bíblicas inline foram preservadas no texto e também extraídas para um campo próprio.

## Estrutura usada

`westminster_structure` contém:

- `chapters`;
- `sections`;
- `section_text`;
- `biblical_references`;
- `special_layouts`.

No nível geral:

- `introductory_pages`: páginas 3 a 17;
- `special_layout_pages`: página 18.

Campos genéricos como `articles`, `questions`, `answers`, `rejections`, `lords_days`, `parts`, contadores brutos e lista técnica de páginas foram removidos.

## Capítulo I, seção I

`CAPÍTULO I DA ESCRITURA SAGRADA` passou a conter seções estruturadas. A seção I preserva o texto confessional e registra as referências bíblicas encontradas no próprio texto.

Exemplo de referências extraídas:

```json
[
  "Rm 2:14,15",
  "Rm 1:19,20",
  "Sl 19:1-3",
  "1Co 1:21",
  "Hb 1:1",
  "2Tm 3:15",
  "2Pe 1:19"
]
```

## Capítulo I, seção II

A seção II contém a lista dos livros bíblicos. Essa estrutura foi preservada em `special_layouts` e também mantida dentro de `section_text`, sem transformar cada livro em chunk isolado.

## Decisão para chunking

O chunking usa `westminster_structure.chapters[].sections[]`. Cada chunk corresponde a uma seção confessional, com capítulo, número da seção, texto e referências bíblicas.
