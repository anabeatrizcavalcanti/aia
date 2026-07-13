# Seleção de chunks e geração de embeddings com OpenAI

## Status

PASS

## Objetivo da etapa

Selecionar chunks elegíveis do corpus doutrinário e normativo da Aliança e gerar embeddings com OpenAI, preservando rastreabilidade documental para a etapa posterior de indexação no ChromaDB.

## Entradas utilizadas

- `corpus/raw/reformed_manifest.json`
- `reports/specs/reformed-corpus-foundation.md`
- `reports/specs/extraction-normalization.md`
- `reports/specs/structural-chunking-base.md`
- `reports/specs/structural-chunking-final.md`
- `corpus/processed/chunks/alliance/all_chunks.jsonl`

## Auditoria manual prévia

A auditoria manual dos chunks foi realizada pela desenvolvedora/pesquisadora antes desta etapa.

- `reports/audits/canones-de-dort-consistency.md`
- `reports/audits/catecismo-heidelberg-consistency.md`
- `reports/audits/confissao-batista-londres-1689-consistency.md`
- `reports/audits/confissao-fe-westminster-consistency.md`
- `reports/audits/structure-inconsistencies.md`

## Seleção de chunks para embeddings

Foram lidos 1119 chunks. A seleção marcou 1115 chunks como elegíveis e 4 como excluídos.

Motivos de exclusão: {'summary_or_non_retrievable_layout': 4}.

## Modelo de embeddings

- Provedor: `openai`
- Modelo: `text-embedding-3-large`
- Dimensões solicitadas: 3072

## Embeddings gerados

Foram gerados 1115 embeddings.

## Validações executadas

```bash
python scripts/pipeline/generate_openai_embeddings.py
python -m py_compile scripts/pipeline/generate_openai_embeddings.py
python -m pytest tests/test_openai_embeddings.py
```

Problemas de validação: nenhuma ocorrência.

## Pontos de atenção

- Chave OpenAI: configurada.
- Erro de API: nenhuma ocorrência.
- Chunks `special_layout` foram excluídos da geração de embeddings por serem layouts técnicos/listas isoladas.

## O que não foi feito nesta etapa

- não foi criado índice ChromaDB;
- não foi implementado chatbot;
- não houve geração de respostas com LLM;
- não foi feita avaliação com documentos de outras tradições;
- não houve upload de documentos pelo usuário;
- não houve alteração manual de texto doutrinário;
- não houve nova extração, normalização ou chunking.
