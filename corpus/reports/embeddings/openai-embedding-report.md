# Relatório de embeddings — OpenAI

## Status

PASS

## Síntese

Foram lidos 1119 chunks do corpus documental da Aliança. A seleção marcou 1115 chunks como elegíveis para embeddings e excluiu 4 chunks por critérios de recuperação.

## Seleção

- Chunks lidos: 1119
- Chunks elegíveis: 1115
- Chunks excluídos: 4
- Motivos de exclusão: {'summary_or_non_retrievable_layout': 4}

## Geração de embeddings

- Provedor: `openai`
- Modelo: `text-embedding-3-large`
- Dimensões: 3072
- Embeddings gerados: 1115
- Retomada parcial: True
- Chave OpenAI: configurada
- Erro de API: nenhuma ocorrência

## O que não foi feito nesta etapa

- Não foi criado índice ChromaDB.
- Não foi implementado chatbot.
- Não houve geração de respostas com LLM.
- Não foi feita avaliação com documentos de outras tradições.
- Não houve upload de documentos pelo usuário.
- Não houve alteração manual de texto doutrinário.
- Não houve nova extração, normalização ou chunking.
