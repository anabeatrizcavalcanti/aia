# Auditoria de consistência — Confissão Batista de Londres de 1689

## Síntese

O relatório estrutural da Confissão Batista de Londres de 1689 foi reorganizado para representar a lógica documental do texto: capítulos, parágrafos numerados, texto confessional e blocos de referências bíblicas associados aos marcadores do texto.

## Estrutura criada

O campo `london_baptist_structure` contém:

- `chapters`: capítulos do corpo principal da confissão;
- `paragraphs`: parágrafos numerados dentro de cada capítulo;
- `paragraph_text`: texto confessional do parágrafo;
- `reference_in_text`: marcadores de referência encontrados no texto;
- `reference_text`: bloco completo de referências daquele parágrafo;
- `references`: bloco de referência agrupado por marcador;
- `reference_associations`: associação entre marcador e referências bíblicas curtas;
- `special_layouts`: estruturas especiais preservadas, como a tabela dos livros bíblicos.

## Classificação de páginas

No nível geral do relatório, a classificação de páginas foi ajustada para evitar falsos positivos:

- `introductory_pages`: apenas a página 1;
- `special_layout_pages`: página 3, onde aparece a tabela dos livros do Antigo e do Novo Testamento.

## Campos removidos

Foram removidos da saída JSON os campos genéricos que não ajudam a representar este documento, como `titles`, `articles`, `questions`, `answers`, `rejections`, `lords_days`, `parts`, contadores brutos de possíveis referências, exemplos de notas, lista técnica de páginas, riscos genéricos e recomendação de chunking.

## Caso verificado: capítulo 2, parágrafo 1

O capítulo `CAPÍTULO 2 DEUS E A SANTÍSSIMA TRINDADE` passou a conter o parágrafo 1 como uma unidade estruturada. O texto confessional permanece em `paragraph_text`, enquanto as referências bíblicas ficam em `reference_text`, `references` e `reference_associations`.

Exemplo de associação:

```json
{
  "1": ["1Co.8.4,6", "Dt.6.4"],
  "2": ["Jr.10.10", "Is.48.12"],
  "3": ["Êx.3.14"],
  "16": ["Êx.34.7", "Na.1.2,3"]
}
```

## Recomendação

Na etapa de chunking, a Confissão Batista de Londres deve usar `london_baptist_structure.chapters[].paragraphs[]` como base principal. Cada chunk deve corresponder preferencialmente a um parágrafo numerado, preservando capítulo, parágrafo, texto confessional, marcadores e referências bíblicas associadas.
