# Estratégia de Recuperação

O projeto deverá comparar estratégias de recuperação para observar qual delas recupera melhor os trechos confessionais relevantes para perguntas doutrinárias.

## Baseline 1: busca vetorial simples

A primeira linha de base será dense retrieval com embeddings. Essa estratégia permite recuperar trechos semanticamente próximos mesmo quando a pergunta usa palavras diferentes das presentes no documento.

## Baseline 2: busca lexical BM25

A segunda linha de base será BM25. Essa estratégia é importante para termos doutrinários técnicos, nos quais a presença do termo exato pode ser decisiva para a recuperação correta.

## Estratégia principal: busca híbrida + RRF + reranking + filtros por metadados

A estratégia principal combinará busca vetorial e busca lexical. Os rankings serão fundidos por Reciprocal Rank Fusion, os candidatos mais relevantes poderão ser reordenados por Cross-Encoder Reranking, e filtros por metadados controlarão corpus ativo, tradição, documento e namespace de recuperação.

Essa comparação permitirá avaliar o ganho de qualidade da recuperação híbrida em relação às estratégias isoladas.
