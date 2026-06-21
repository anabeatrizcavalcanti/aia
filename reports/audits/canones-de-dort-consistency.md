# Auditoria de consistência — Cânones de Dort

## Síntese

O relatório estrutural dos Cânones de Dort foi reorganizado para representar a lógica documental do texto. Antes, o JSON listava artigos, rejeições, erros e refutações como eventos separados. Agora ele inclui `canons_structure`, que preserva a hierarquia própria do documento.

## Estrutura criada

O campo `canons_structure` contém:

- `doctrinal_chapters`: capítulos doutrinários;
- `articles`: artigos positivos de cada capítulo;
- `rejection_of_errors`: seção de rejeição de erros de cada capítulo;
- `pairs`: pares formados por `Erro N` e `Refutação`;
- `conclusion`: conclusão final dos Cânones de Dort;
- contadores de capítulos, artigos, pares erro/refutação e presença de conclusão.

No nível geral do relatório, a classificação de páginas foi ajustada para evitar falsos positivos:

- `introductory_pages`: apenas a página 1;
- `special_layout_pages`: nenhuma ocorrência nesta análise.

Também foram removidos da saída JSON dos Cânones os campos genéricos que não ajudam a representar este documento, como `lords_days`, `parts`, `questions`, `answers`, `pages`, contadores brutos de possíveis referências e a lista genérica de riscos. A estratégia de chunking continua documentada no relatório Markdown, mas não precisa ser repetida dentro da estrutura JSON usada como base para o pipeline.

## Artigos positivos

Cada artigo positivo passou a ser representado como uma unidade própria com:

- `article_number`;
- `article_heading`;
- `article_title`;
- `article_text`;
- `reference_in_text`;
- `article_references`;
- `chunk_type` igual a `doctrinal_article`.

Exemplo verificado no quinto capítulo:

```json
{
  "article_number": "12",
  "article_title": "Esta certeza é um estímulo à piedade",
  "reference_in_text": [],
  "article_references": "Rm 12.1; Sl 56.12, 13; 116.12; Tt 2.11-14; 1Jo 3.3."
}
```

Nesse caso, o título do artigo, o texto doutrinário e as referências bíblicas finais foram separados corretamente.
Quando o próprio texto do artigo contém referências bíblicas entre parênteses, essas referências permanecem em `article_text` e também são registradas em `reference_in_text`.

## Rejeição de Erros

Cada capítulo possui uma seção `Rejeição de Erros`. Dentro dela, o parser agrupa cada `Erro N` com sua `Refutação` correspondente.

Cada par recebe:

- `error_number`;
- `error_text`;
- `refutation_text`;
- `refutation_references`;
- `chunk_type` igual a `error_refutation`.

As referências bíblicas das refutações são extraídas a partir dos parênteses presentes no texto, preservando a refutação completa como texto principal.

## Conclusão

A seção final `Conclusão` foi tratada separadamente dos capítulos doutrinários. Ela contém parágrafos comuns e afirmações numeradas, com `paragraph_type` indicando se o trecho é um parágrafo ordinário ou uma afirmação numerada.

## Contadores atuais

- capítulos doutrinários: 4;
- artigos positivos: 59;
- pares erro/refutação: 34;
- conclusão: presente.

## Recomendação para chunking

Na etapa de chunking, os Cânones de Dort devem usar:

- `doctrinal_article` para artigos positivos;
- `error_refutation` para pares erro/refutação;
- um tipo próprio para os parágrafos da conclusão, como `conclusion_paragraph`.

Essa separação é importante porque os artigos positivos e as rejeições de erro têm funções teológicas e documentais diferentes.
