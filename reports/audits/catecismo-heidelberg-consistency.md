# Auditoria estrutural — Catecismo de Heidelberg

## Registro

O JSON estrutural do Catecismo de Heidelberg foi reorganizado em torno da unidade pergunta-resposta. Essa forma deixa explícita a relação entre pergunta, resposta, referências bíblicas, Parte e Dia do Senhor.

## Estrutura usada

O arquivo `corpus/reports/structure_analysis/catecismo-heidelberg.structure.json` passou a conter:

- `catechism_units`;
- marcadores de referência na pergunta e na resposta;
- mapa `references`;
- `part_label`, `part_title`, `part`, `lords_day` e `section_title`;
- `trailing_section_lines_excluded`;
- resumo de consistência em `catechism_consistency`.

Campos brutos como `titles`, `questions`, `answers`, `lords_days`, contadores genéricos e lista técnica de páginas foram removidos do topo do JSON.

## Pergunta 21

O trecho `pelos méritos de Cristo.5` ficou associado ao marcador `5`:

```json
"5": "Rm 3.20-26; Gl 2.16; Ef 2.8-10."
```

A quebra de linha entre o marcador e a referência não rompeu o vínculo.

## Transição entre Dia do Senhor 5 e 6

O cabeçalho `Dia do Senhor 6` não pertence às referências da pergunta 15. Ele marca o início da seção seguinte.

No JSON:

- pergunta 15: `lords_day=Dia do Senhor 5`;
- pergunta 15: `trailing_section_lines_excluded=["Dia do Senhor 6"]`;
- pergunta 16: `lords_day=Dia do Senhor 6`.

## Parte I

As perguntas 1 e 2 aparecem antes da primeira Parte explícita e, por isso, permanecem sem `part`. A Parte I começa a partir da pergunta 3:

```json
"part_label": "Parte I",
"part_title": "NOSSOS PECADOS E MISÉRIA",
"part": "Parte I NOSSOS PECADOS E MISÉRIA"
```

## Dia do Senhor 45

Na seção `A Oração`, o texto extraído traz `Dia do Senhor 4`, mas a sequência estrutural indica `Dia do Senhor 45`. O JSON preserva a forma bruta e registra a inferência:

```json
"lords_day": "Dia do Senhor 45",
"lords_day_raw": "Dia do Senhor 4",
"lords_day_inferred": true
```

Essa correção é estrutural e auditável; não altera conteúdo doutrinário.

## Pontos pendentes

Persistem marcadores de referência que exigem revisão humana:

- pergunta 10: marcador `2`;
- pergunta 20: marcador `2`;
- pergunta 29: marcador `2`;
- pergunta 60: marcador `2`.

Esses casos foram preservados como avisos e não impedem o chunking da unidade pergunta-resposta.

## Decisão para chunking

O chunking usa `catechism_units` como base. Cada chunk corresponde a uma pergunta-resposta, preservando Parte, Dia do Senhor, pergunta, resposta e referências bíblicas.
