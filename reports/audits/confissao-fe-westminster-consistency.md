# Auditoria de consistência — Confissão de Fé de Westminster

## Síntese

O relatório estrutural da Confissão de Fé de Westminster foi reorganizado para representar a lógica documental do texto: capítulos, seções em algarismos romanos, texto confessional e referências bíblicas inline.

## Estrutura criada

O campo `westminster_structure` contém:

- `chapters`: capítulos do corpo principal da confissão;
- `sections`: seções numeradas em algarismos romanos dentro de cada capítulo;
- `section_text`: texto confessional da seção;
- `biblical_references`: referências bíblicas extraídas do próprio texto da seção;
- `special_layouts`: estruturas especiais preservadas, como a tabela dos livros bíblicos no capítulo I.

## Classificação de páginas

No nível geral do relatório, a classificação de páginas foi ajustada para evitar falsos positivos:

- `introductory_pages`: páginas 3 a 17, incluindo sumário, breve história e textos introdutórios;
- `special_layout_pages`: página 18, onde aparece a tabela dos livros do Antigo e do Novo Testamento.

## Campos removidos

Foram removidos da saída JSON os campos genéricos que não ajudam a representar este documento, como `articles`, `questions`, `answers`, `rejections`, `lords_days`, `parts`, contadores brutos de possíveis referências, exemplos de notas, lista técnica de páginas, riscos genéricos e recomendação de chunking.

## Caso verificado: capítulo I, seção I

O capítulo `CAPÍTULO I DA ESCRITURA SAGRADA` passou a conter seções estruturadas. A seção I preserva o texto confessional e extrai as referências bíblicas inline.

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

## Caso verificado: capítulo I, seção II

A seção II contém uma tabela de livros bíblicos. Essa estrutura foi preservada em `special_layouts` e também recomposta dentro de `section_text`, para não transformar cada livro bíblico em uma unidade confessional isolada.

## Recomendação

Na etapa de chunking, a Confissão de Westminster deve usar `westminster_structure.chapters[].sections[]` como base principal. Cada chunk deve corresponder preferencialmente a uma seção confessional, preservando capítulo, número da seção, texto e referências bíblicas.
