# Auditoria estrutural — Cânones de Dort

## Registro

O JSON estrutural dos Cânones de Dort foi reorganizado para refletir a hierarquia real do documento. Antes, artigos, rejeições, erros e refutações apareciam como eventos soltos; agora ficam agrupados em `canons_structure`.

## Estrutura usada

`canons_structure` contém:

- capítulos doutrinários;
- artigos positivos;
- seção de rejeição de erros;
- pares `Erro N` + `Refutação`;
- conclusão;
- contadores de capítulos, artigos, pares erro/refutação e conclusão.

No nível geral:

- `introductory_pages`: página 1;
- `special_layout_pages`: nenhuma ocorrência.

Campos genéricos que não ajudam neste documento foram removidos do JSON, como `lords_days`, `parts`, `questions`, `answers`, contadores brutos de referências e lista técnica de páginas.

## Artigos positivos

Cada artigo positivo passou a ter:

- `article_number`;
- `article_heading`;
- `article_title`;
- `article_text`;
- `reference_in_text`;
- `article_references`;
- `chunk_type=doctrinal_article`.

Caso verificado no quinto capítulo:

```json
{
  "article_number": "12",
  "article_title": "Esta certeza é um estímulo à piedade",
  "reference_in_text": [],
  "article_references": "Rm 12.1; Sl 56.12, 13; 116.12; Tt 2.11-14; 1Jo 3.3."
}
```

Referências que aparecem dentro do próprio texto permanecem em `article_text` e também são registradas em `reference_in_text`.

## Rejeição de erros

Cada `Erro N` foi associado à sua `Refutação`. O par recebe `chunk_type=error_refutation`, preservando o erro, a refutação e as referências bíblicas presentes nos parênteses da refutação.

## Conclusão

A conclusão fica separada dos capítulos doutrinários. Seus blocos foram classificados como parágrafo comum ou afirmação numerada.

## Contadores

- capítulos doutrinários: 4;
- artigos positivos: 59;
- pares erro/refutação: 34;
- conclusão: presente.

## Decisão para chunking

O chunking usa `doctrinal_article` para artigos, `error_refutation` para pares erro/refutação e `conclusion_paragraph` para a conclusão. Essa separação evita misturar exposição positiva da doutrina com refutação de erro.
