# Relatório de geração RAG com fontes

## Status

PASS

## Configuração

{
  "provider": "openai",
  "model": "gpt-5.4-mini",
  "temperature": 0.1,
  "max_output_tokens": 1200,
  "require_citations": true,
  "answer_language": "pt-BR",
  "use_retrieval_pipeline": true,
  "default_filters": {
    "corpus_id": "reformed",
    "retrieval_namespace": "reformed_confessional"
  }
}

## Consultas

### O que é o batismo?

- Tipo: `main`
- Status: `answered`
- Modelo: `gpt-5.4-mini`
- Contextos usados: `3`
- Total de caracteres de contexto: `10543`
- Documentos usados: `['confissao-batista-londres-1689', 'confissao-fe-westminster']`
- Fontes citadas: `['source_1: Confissão Batista de Londres de 1689 (74-75)', 'source_2: Confissão de Fé de Westminster (54)', 'source_3: Confissão Batista de Londres de 1689 (73)']`
- Recusa: `False`
- Motivo de recusa: `nenhum`
- Erro técnico: `nenhum`
- Prévia da resposta: Resposta: O batismo é uma ordenança do Novo Testamento, instituída por Jesus Cristo, e também descrita como um sacramento do Novo Testamento. Ele é apresentado como um sinal da comunhão e união com Cristo, de sua morte e ressurreição, da remissão dos pecados, da consagração a Deus e do andar em novidade de vida [1][2]. Quanto à forma, os documentos divergem: a Confissão Batista de Londres de 1689 afirma que a administração correta requer imersão, ou submersão, na água [1], enquanto a Confissão de Fé de Westminster afirma que o batismo é corretamente administrado por efusão ou aspersão de água 

### O que é necessário para a salvação?

- Tipo: `main`
- Status: `answered`
- Modelo: `gpt-5.4-mini`
- Contextos usados: `3`
- Total de caracteres de contexto: `15411`
- Documentos usados: `['catecismo-heidelberg', 'confissao-batista-londres-1689']`
- Fontes citadas: `['source_1: Confissão Batista de Londres de 1689 (2-3)', 'source_2: Confissão Batista de Londres de 1689 (35-37)', 'source_3: Catecismo de Heidelberg (9-10)']`
- Recusa: `False`
- Motivo de recusa: `nenhum`
- Erro técnico: `nenhum`
- Prévia da resposta: Resposta: Com base nos contextos fornecidos, a salvação é apresentada como ligada à Escritura, ao arrependimento e à obra de Cristo. - A Confissão Batista de Londres de 1689 afirma que a Sagrada Escritura é a “única regra suficiente, certa e infalível de conhecimento para a salvação” e que o conhecimento de Deus e de sua vontade necessário à salvação está nela revelado [1]. - Também afirma que Deus concede “arrependimento para vida” aos eleitos, e que esse arrependimento salvador é uma graça evangélica pela qual a pessoa, por obra do Espírito Santo, é levada a sentir o pecado, humilhar-se, ora

### O que é eleição?

- Tipo: `main`
- Status: `answered`
- Modelo: `gpt-5.4-mini`
- Contextos usados: `1`
- Total de caracteres de contexto: `4126`
- Documentos usados: `['canones-de-dort']`
- Fontes citadas: `['source_1: Cânones de Dort (3-9)']`
- Recusa: `False`
- Motivo de recusa: `nenhum`
- Erro técnico: `nenhum`
- Prévia da resposta: Resposta: Eleição, segundo os Cânones de Dort, é o propósito imutável de Deus pelo qual Ele, antes da fundação do mundo, por pura graça e segundo o beneplácito da sua vontade, escolheu em Cristo um número definido de pessoas para a salvação. Esse decreto inclui chamá-las eficazmente, conceder-lhes fé, justificá-las, santificá-las e glorificá-las, para a demonstração da misericórdia de Deus e o louvor da sua graça [1]. Base documental: [1] Cânones de Dort, Primeiro Capítulo da Doutrina — A Eleição e a Reprovação Divinas, Artigo 7. Observação: O contexto também afirma que há um único decreto de 

### O que é justificação?

- Tipo: `main`
- Status: `answered`
- Modelo: `gpt-5.4-mini`
- Contextos usados: `2`
- Total de caracteres de contexto: `9117`
- Documentos usados: `['confissao-batista-londres-1689', 'confissao-fe-westminster']`
- Fontes citadas: `['source_1: Confissão Batista de Londres de 1689 (29-31)', 'source_2: Confissão de Fé de Westminster (33)']`
- Recusa: `False`
- Motivo de recusa: `nenhum`
- Erro técnico: `nenhum`
- Prévia da resposta: Resposta: Justificação é o ato pelo qual Deus chama eficazmente certos pecadores e os justifica gratuitamente, não por infundir neles justiça nem por algo que eles façam, mas por perdoar seus pecados e aceitá-los como justos por causa de Cristo. Ela envolve a imputação da obediência e satisfação de Cristo como a justiça deles, recebida pela fé, que é o único instrumento de justificação [1][2]. Base documental: [1] Confissão Batista de Londres de 1689, Capítulo 11 — A Justificação, parágrafos 1 e 2. [2] Confissão de Fé de Westminster, Capítulo XI — Da Justificação, seções I e II. Observação: Os

### O que a tradição reformada ensina sobre as Escrituras?

- Tipo: `main`
- Status: `answered`
- Modelo: `gpt-5.4-mini`
- Contextos usados: `1`
- Total de caracteres de contexto: `6721`
- Documentos usados: `['confissao-batista-londres-1689']`
- Fontes citadas: `['source_1: Confissão Batista de Londres de 1689 (3-5)']`
- Recusa: `False`
- Motivo de recusa: `nenhum`
- Erro técnico: `nenhum`
- Prévia da resposta: Resposta: A tradição reformada, conforme este documento, ensina que as Escrituras têm autoridade divina própria: elas devem ser cridas e obedecidas porque vêm de Deus, e não porque a autoridade dependa do testemunho de homens ou da igreja [1]. Ensina também que a certeza plena de sua verdade e autoridade divina vem da operação interna do Espírito Santo, que testifica aos corações pela Palavra e com a Palavra [1]. Além disso, afirma que todo o conselho de Deus necessário para a glória de Deus, a salvação, a fé e a vida está expressamente declarado ou necessariamente contido nas Escrituras, de m

### O crente pode perder a salvação?

- Tipo: `main`
- Status: `answered`
- Modelo: `gpt-5.4-mini`
- Contextos usados: `3`
- Total de caracteres de contexto: `16624`
- Documentos usados: `['canones-de-dort', 'confissao-batista-londres-1689', 'confissao-fe-westminster']`
- Fontes citadas: `['source_1: Confissão de Fé de Westminster (41)', 'source_2: Cânones de Dort (25-29)', 'source_3: Confissão Batista de Londres de 1689 (43-46)']`
- Recusa: `False`
- Motivo de recusa: `nenhum`
- Erro técnico: `nenhum`
- Prévia da resposta: Resposta: Com base nos documentos recuperados, a resposta é **não, o crente verdadeiro não perde totalmente a salvação**. Os textos afirmam que os verdadeiros crentes podem ter a certeza da salvação abalada, diminuída ou interrompida por pecado, tentação ou pela retirada da sensação da presença de Deus, **mas não ficam inteiramente privados** da “semente de Deus” e da vida de fé, sendo preservados para não caírem em desespero absoluto [1]. A Confissão Batista de Londres de 1689 diz o mesmo: os crentes verdadeiros podem ter a certeza de salvação abalada, porém “jamais ficam destituídos” da divi

### O que é regeneração?

- Tipo: `main`
- Status: `answered`
- Modelo: `gpt-5.4-mini`
- Contextos usados: `3`
- Total de caracteres de contexto: `16654`
- Documentos usados: `['canones-de-dort', 'confissao-batista-londres-1689']`
- Fontes citadas: `['source_1: Cânones de Dort (18-20)', 'source_2: Confissão Batista de Londres de 1689 (32-34)', 'source_3: Confissão Batista de Londres de 1689 (35-37)']`
- Recusa: `False`
- Motivo de recusa: `nenhum`
- Erro técnico: `nenhum`
- Prévia da resposta: Resposta: Regeneração, nos contextos fornecidos, é a obra de Deus pela qual Ele realiza em nós uma nova criação, um ressurgir dos mortos e uma vivificação espiritual. Os Cânones de Dort dizem que essa regeneração é operada por Deus “a despeito de nós”, não por ensino exterior ou persuasão moral, mas como uma obra sobrenatural, poderosíssima, pela qual a vontade é restaurada e a pessoa crê e se arrepende pela graça recebida [1]. O mesmo documento também descreve essa obra como a ação eficaz do “Espírito regenerador”, que abre o coração, infunde novas qualidades na vontade e faz viver a vontade 

### O que é expiação?

- Tipo: `main`
- Status: `answered`
- Modelo: `gpt-5.4-mini`
- Contextos usados: `2`
- Total de caracteres de contexto: `12442`
- Documentos usados: `['confissao-batista-londres-1689']`
- Fontes citadas: `['source_1: Confissão Batista de Londres de 1689 (29-31)', 'source_2: Confissão Batista de Londres de 1689 (35-37)']`
- Recusa: `False`
- Motivo de recusa: `nenhum`
- Erro técnico: `nenhum`
- Prévia da resposta: Resposta: Nos contextos fornecidos, “expiação” é apresentada como a obra de Cristo pela qual ele, por sua obediência e morte, pagou plenamente a dívida dos justificados, deu satisfação adequada, verdadeira e plena à justiça de Deus, tomou o lugar deles e recebeu a punição que lhes era devida [1]. Também é descrita como o sacrifício de si mesmo, no sangue da cruz, pelo qual há redenção e remissão dos pecados [1]. Base documental: [1] Confissão Batista de Londres de 1689, Capítulo 11 — A Justificação, parágrafo 3. Observação: Os contextos recuperados não trazem uma definição técnica isolada do t

### O que a tradição reformada ensina sobre a sucessão papal?

- Tipo: `refusal`
- Status: `refused`
- Modelo: `gpt-5.4-mini`
- Contextos usados: `4`
- Total de caracteres de contexto: `10210`
- Documentos usados: `['canones-de-dort', 'confissao-fe-westminster']`
- Fontes citadas: `['source_1: Cânones de Dort (32)', 'source_2: Confissão de Fé de Westminster (7)', 'source_3: Confissão de Fé de Westminster (12)', 'source_4: Cânones de Dort (1)']`
- Recusa: `True`
- Motivo de recusa: `insufficient_query_context_overlap`
- Erro técnico: `nenhum`
- Prévia da resposta: Não encontrei base documental suficiente no corpus reformado disponível para responder com segurança a essa pergunta. Posso responder apenas quando houver evidência nos documentos recuperados.

### Qual é a posição reformada sobre um documento que não está no corpus?

- Tipo: `refusal`
- Status: `refused`
- Modelo: `gpt-5.4-mini`
- Contextos usados: `2`
- Total de caracteres de contexto: `5161`
- Documentos usados: `['canones-de-dort', 'confissao-batista-londres-1689']`
- Fontes citadas: `['source_1: Confissão Batista de Londres de 1689 (29-30)', 'source_2: Cânones de Dort (32)']`
- Recusa: `True`
- Motivo de recusa: `requested_material_outside_active_corpus`
- Erro técnico: `nenhum`
- Prévia da resposta: Não encontrei base documental suficiente no corpus reformado disponível para responder com segurança a essa pergunta. Posso responder apenas quando houver evidência nos documentos recuperados.

### Segundo os documentos reformados disponíveis, qual é a doutrina da assunção de Maria?

- Tipo: `refusal`
- Status: `refused`
- Modelo: `gpt-5.4-mini`
- Contextos usados: `4`
- Total de caracteres de contexto: `12763`
- Documentos usados: `['canones-de-dort', 'confissao-fe-westminster']`
- Fontes citadas: `['source_1: Cânones de Dort (1)', 'source_2: Confissão de Fé de Westminster (12)', 'source_3: Confissão de Fé de Westminster (13)', 'source_4: Confissão de Fé de Westminster (4)']`
- Recusa: `True`
- Motivo de recusa: `only_introductory_context`
- Erro técnico: `nenhum`
- Prévia da resposta: Não encontrei base documental suficiente no corpus reformado disponível para responder com segurança a essa pergunta. Posso responder apenas quando houver evidência nos documentos recuperados.

## Agregados

- Respostas geradas: `8`
- Recusas geradas: `3`
- Erros técnicos: `0`

Documentos usados:

{
  "confissao-batista-londres-1689": 8,
  "canones-de-dort": 6,
  "confissao-fe-westminster": 5,
  "catecismo-heidelberg": 1
}

Status por consulta:

{
  "answered": 8,
  "refused": 3
}

## Notas técnicas

- A geração usa OpenAI apenas após decisão positiva da política de evidência.
- Recusas não chamam o modelo de chat.
- As citações são derivadas do `source_map` do pacote final de retrieval.
- A política de evidência usa critérios documentais gerais; regras hardcoded por tema específico foram removidas.
- O caminho oficial de geração é `RagGenerator` com `PromptBuilder`; `rag_chain.py` e `source_grounded_prompt.py` permanecem apenas como compatibilidade.

## Limitações

- A política de recusa é inicial e baseada em metadados, tamanho de contexto e sobreposição lexical.
- A etapa não faz avaliação automática de qualidade.
