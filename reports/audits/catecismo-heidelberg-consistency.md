# Auditoria de consistência — Catecismo de Heidelberg

## Síntese

O relatório estrutural do Catecismo de Heidelberg foi melhorado para refletir melhor a unidade documental própria de um catecismo: pergunta, resposta e referências associadas. Antes, o JSON listava perguntas e respostas como eventos separados, o que dificultava verificar se uma referência como `Cristo.5` estava ligada ao bloco bíblico correto.

O arquivo `corpus/reports/structure_analysis/catecismo-heidelberg.structure.json` agora inclui:

- `catechism_units`: unidades pergunta-resposta com texto da pergunta, resposta, referências e páginas;
- `question_reference_markers`: marcadores de referência presentes na pergunta;
- `answer_reference_markers`: marcadores de referência presentes na resposta;
- `references`: mapa entre marcador e referência bíblica;
- `part_label`, `part_title`, `part`, `lords_day` e `section_title`: contexto estrutural da unidade;
- `trailing_section_lines_excluded`: cabeçalhos estruturais encontrados depois das referências e removidos da unidade anterior;
- `catechism_consistency`: resumo de consistência das 129 unidades.

## Caso verificado: Pergunta 21

Na pergunta 21, o trecho `pelos méritos de Cristo.5` foi associado corretamente à referência `5`.

Mapeamento no JSON:

```json
"5": "Rm 3.20-26; Gl 2.16; Ef 2.8-10."
```

Isso confirma que a quebra de linha entre `5.` e `Rm 3.20-26` não representa perda de vínculo. O parser recompõe o bloco de referências a partir das linhas extraídas.

## Melhorias aplicadas

- montagem de 129 unidades pergunta-resposta;
- detecção de respostas iniciadas por `R.`;
- detecção de respostas com marcador antes do `R.`, como `1 R.`;
- detecção de respostas na mesma linha da pergunta, como nas perguntas 101 e 117;
- separação entre texto da resposta e referências quando aparecem na mesma linha;
- mapeamento de marcadores como `1`, `2`, `3` para seus blocos bíblicos;
- remoção de cabeçalhos como `Dia do Senhor` e `Parte` de `reference_lines`;
- atribuição desses cabeçalhos como contexto da pergunta seguinte;
- representação de `Parte I NOSSOS PECADOS E MISÉRIA` como escopo das perguntas 3 a 11;
- preservação das perguntas 1 e 2 sem `part`, pois aparecem antes da primeira Parte explícita;
- geração de `parts` com o título completo de cada Parte;
- remoção de campos brutos que não são necessários para o pipeline, como `titles`, `questions`, `answers`, `lords_days`, `rejections`, contadores genéricos de possíveis referências e a lista técnica de páginas;
- redução de falsos positivos em números de capítulos e versículos;
- suporte a abreviações bíblicas usadas no PDF, incluindo `Fl`.

## Caso verificado: transição entre Dia do Senhor 5 e Dia do Senhor 6

O cabeçalho `Dia do Senhor 6` não pertence às referências da pergunta 15. Ele marca o início da próxima seção, onde começam as perguntas 16 a 19.

O JSON agora preserva essa distinção:

- pergunta 15: `lords_day` igual a `Dia do Senhor 5`;
- pergunta 15: `reference_lines` contém apenas referências bíblicas;
- pergunta 15: `trailing_section_lines_excluded` contém `Dia do Senhor 6`;
- pergunta 16: `lords_day` igual a `Dia do Senhor 6`.

## Caso verificado: Parte I e Dia do Senhor 1

O trecho inicial do catecismo contém `CATECISMO DE HEIDELBERG`, `Dia do Senhor 1` e as perguntas 1 e 2 antes da primeira parte explícita. Por isso, essas perguntas permanecem sem `part`.

A primeira parte explícita começa em `Parte I` e recebe como título `NOSSOS PECADOS E MISÉRIA`. No JSON, as perguntas 3 a 11 passaram a receber:

```json
"part_label": "Parte I",
"part_title": "NOSSOS PECADOS E MISÉRIA",
"part": "Parte I NOSSOS PECADOS E MISÉRIA"
```

No nível superior do relatório estrutural, `parts` registra a Parte completa:

```json
{
  "page": 2,
  "text": "Parte I NOSSOS PECADOS E MISÉRIA"
}
```

Os títulos e cabeçalhos do Heidelberg deixaram de ser listados em um array bruto no topo do JSON. A informação estrutural relevante fica em `catechism_units`, especialmente nos campos `part`, `lords_day` e `section_title`. Isso evita misturar o primeiro parágrafo histórico ou subtítulos auxiliares como se fossem títulos estruturais independentes.

No nível geral do relatório, a classificação de páginas também foi ajustada:

- `introductory_pages`: apenas a página 1;
- `special_layout_pages`: nenhuma ocorrência nesta análise.

## Caso verificado: Dia do Senhor 45

Na seção `A Oração`, o texto extraído pelo PyMuPDF traz `Dia do Senhor 4`, embora a sequência estrutural indique `Dia do Senhor 45`. O JSON preserva a linha bruta em `lords_day_raw` e registra o valor normalizado em `lords_day`.

```json
"lords_day": "Dia do Senhor 45",
"lords_day_raw": "Dia do Senhor 4",
"lords_day_inferred": true
```

Essa correção é estrutural e auditável; ela não altera o conteúdo doutrinário do PDF.

## Pontos ainda pendentes

Restaram quatro unidades com marcador de resposta sem referência mapeada automaticamente:

- Pergunta 10: marcador `2`;
- Pergunta 20: marcador `2`;
- Pergunta 29: marcador `2`;
- Pergunta 60: marcador `2`.

Esses casos parecem estar ligados a ambiguidades ou perdas na própria extração textual, por exemplo referências sem abreviação bíblica explícita ou marcador duplicado no bloco de referências. Eles devem ser revisados manualmente antes do chunking definitivo.

## Recomendação

Na etapa de chunking, o Catecismo de Heidelberg deve usar `catechism_units` como base principal. Cada chunk deve corresponder preferencialmente a uma unidade pergunta-resposta, preservando `Parte`, `Dia do Senhor`, pergunta, resposta e referências bíblicas como metadados ou campos estruturados.
