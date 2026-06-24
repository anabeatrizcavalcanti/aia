# Auditoria estrutural dos PDFs reformados

## Nota geral

Esta auditoria registra problemas encontrados na primeira leitura estrutural dos quatro PDFs reformados. O foco aqui é distinguir falhas reais de extração de casos em que o texto foi extraído corretamente, mas a estrutura visual do PDF confundiu o analisador.

## Cânones de Dort

Nos Cânones de Dort, os títulos de capítulos apareciam incompletos no relatório inicial. Não era perda de texto no PDF: o PyMuPDF extraía alguns títulos em duas ou três linhas, e o analisador guardava apenas a primeira linha.

Depois do ajuste, os capítulos passaram a ser reconhecidos como:

- `Primeiro Capítulo da Doutrina: A Eleição e a Reprovação Divinas`
- `Segundo Capítulo da Doutrina: A Morte de Cristo e a Redenção do Homem Através Dela`
- `Terceiro e Quarto Capítulos da Doutrina: A Corrupção do Homem, a sua Conversão a Deus e o Modo como isso Ocorre`
- `Quinto Capítulo da Doutrina: A Perseverança dos Santos`

Exemplos do padrão observado:

- página 1: `Primeiro Capítulo da Doutrina: A Eleição e a` + `Reprovação Divinas`
- página 10: `Segundo Capítulo da Doutrina: A Morte de Cristo` + `e a Redenção do Homem Através Dela`
- página 15: `Terceiro e Quarto Capítulos da Doutrina: A` + `Corrupção do Homem, a sua Conversão a Deus e` + `o Modo como isso Ocorre`
- página 24: `Quinto Capítulo da Doutrina: A Perseverança dos` + `Santos`

Também foi corrigido o reconhecimento de `Quinto Capítulo`, que não entrava no padrão anterior.

Decisão adotada: artigos positivos, rejeições de erro, erros e refutações ficam separados na estrutura, porque cumprem funções documentais diferentes.

## Confissão de Fé de Westminster

A principal inconsistência era a mistura entre sumário e corpo confessional. O relatório inicial encontrava capítulos na página do sumário e depois reencontrava os mesmos capítulos no corpo principal, iniciado na página 18 com `CAPÍTULO I`.

O documento passou a exigir zoneamento explícito:

- `table_of_contents`;
- `introductory_material`;
- `confessional_body`;
- `special_layout`;
- `biblical_references`.

Também foi marcada a estrutura especial do capítulo sobre as Escrituras, que contém a lista dos livros do Antigo e Novo Testamento.

Decisão adotada: material histórico, sumário e corpo confessional não devem receber o mesmo tratamento no chunking.

## Catecismo de Heidelberg

O Catecismo de Heidelberg tem 129 perguntas. No relatório inicial, algumas respostas não eram detectadas porque começavam na mesma linha da pergunta ou vinham precedidas por marcador numérico.

Casos observados:

- página 22: `P.101. ...? R. Sim,`
- página 26: `P.117. ...? R. Primeiro, devemos`

Decisão adotada: a unidade estrutural principal é sempre pergunta-resposta, mesmo quando `P.` e `R.` aparecem na mesma linha.

Também foi ajustado o tratamento de linhas como `Dia do Senhor N`, `Parte I` e referências bíblicas, para que esses elementos não sejam anexados indevidamente à unidade anterior.

## Confissão Batista de Londres de 1689

A Confissão Batista de Londres de 1689 teve problema parecido com Westminster: o sumário aparece no início do PDF e é seguido pelo corpo confessional. Isso fazia o analisador contar entradas de sumário como se fossem capítulos reais.

Entradas que precisaram ser diferenciadas:

- entradas do sumário;
- cabeçalhos reais de capítulos;
- algumas linhas em caixa alta usadas como títulos.

O documento também contém muitos blocos extensos de referências bíblicas. Como os parágrafos confessionais e as referências usam numeração, o analisador passou a depender do contexto estrutural do capítulo para diferenciar texto confessional de referência.

Decisão adotada: o chunk principal é o parágrafo confessional numerado, com referências preservadas como conteúdo associado, não como chunks doutrinários independentes.

## Ajustes feitos no analisador

O script `scripts/corpus/analyze_reformed_pdf_structure.py` foi ajustado para:

- recomposição de títulos estruturais extraídos em múltiplas linhas;
- reconhecimento de `Quinto Capítulo`;
- detecção de respostas iniciadas por `R.` e por formas como `1 R.`;
- ampliação da detecção aproximada de referências bíblicas em abreviações como `2 Tm 3.15-17`, `Is.8.20` e `Rm.1.19-21`.
