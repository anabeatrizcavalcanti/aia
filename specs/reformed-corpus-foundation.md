# Corpus Reformado: validação, manifesto, análise estrutural e scripts-base

## Objetivo

Registrar a primeira organização do corpus reformado do SolaBot. Nesta etapa, os PDFs colocados manualmente em `corpus/raw/reformed/` são validados, associados aos identificadores oficiais do projeto e descritos no manifesto do corpus.

## Escopo

O trabalho desta etapa fica concentrado na base documental bruta:

- validar os quatro documentos confessionais reformados esperados;
- associar os arquivos encontrados aos `document_id` oficiais;
- manter o manifesto em `corpus/raw/reformed_manifest.json`;
- analisar a estrutura inicial dos PDFs com PyMuPDF;
- registrar os achados em relatórios de acompanhamento;
- deixar prontos os scripts-base de extração, normalização e chunking estrutural;
- cobrir a estrutura mínima do corpus com testes básicos.

## Documentos Esperados

| document_id | Documento |
| --- | --- |
| `confissao-fe-westminster` | Confissão de Fé de Westminster |
| `canones-de-dort` | Cânones de Dort |
| `catecismo-heidelberg` | Catecismo de Heidelberg |
| `confissao-batista-londres-1689` | Confissão Batista de Londres de 1689 |

## Fora de Escopo

Esta etapa não gera embeddings, não cria índice vetorial e não implementa chatbot. Também não inclui upload de usuário, avaliação com documentos de outras tradições ou alteração manual de conteúdo doutrinário.
