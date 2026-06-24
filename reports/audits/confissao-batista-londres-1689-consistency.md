# Auditoria estrutural — Confissão Batista de Londres de 1689

## Registro

O JSON estrutural da Confissão Batista de Londres de 1689 foi reorganizado por capítulos e parágrafos numerados. As referências bíblicas foram mantidas associadas ao parágrafo correspondente.

## Estrutura usada

`london_baptist_structure` contém:

- `chapters`;
- `paragraphs`;
- `paragraph_text`;
- `reference_in_text`;
- `reference_text`;
- `references`;
- `reference_associations`;
- `special_layouts`.

No nível geral:

- `introductory_pages`: página 1;
- `special_layout_pages`: página 3.

Campos genéricos como `titles`, `articles`, `questions`, `answers`, `rejections`, `lords_days`, `parts`, contadores brutos e lista técnica de páginas foram removidos.

## Capítulo 2, parágrafo 1

O capítulo `CAPÍTULO 2 DEUS E A SANTÍSSIMA TRINDADE` contém o parágrafo 1 como unidade estruturada. O texto confessional fica em `paragraph_text`; as referências ficam em `reference_text`, `references` e `reference_associations`.

Exemplo:

```json
{
  "1": ["1Co.8.4,6", "Dt.6.4"],
  "2": ["Jr.10.10", "Is.48.12"],
  "3": ["Êx.3.14"],
  "16": ["Êx.34.7", "Na.1.2,3"]
}
```

## Decisão para chunking

O chunking usa `london_baptist_structure.chapters[].paragraphs[]`. Cada chunk corresponde a um parágrafo numerado, com capítulo, parágrafo, texto confessional, marcadores e referências bíblicas associadas.
