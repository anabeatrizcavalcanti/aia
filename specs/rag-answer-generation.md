# Geração RAG com fontes do corpus reformado

## Escopo

Camada de geração de respostas doutrinárias com base no pacote final de contextos produzido pela `RetrievalPipeline`.

A geração usa OpenAI apenas depois da política de evidência permitir resposta. Quando o pacote de contexto não sustenta a pergunta, a etapa retorna recusa documentada e não chama o modelo de chat.

## Entradas

- `reports/specs/retrieval-pipeline.md`
- `corpus/reports/retrieval/retrieval-pipeline-report.md`
- `corpus/reports/retrieval/retrieval-pipeline-report.json`
- `corpus/processed/chunks/reformed/all_chunks_for_embeddings.jsonl`
- `corpus/processed/embeddings/reformed/embedding_manifest.json`
- `corpus/indexes/chroma/reformed/`
- `config/retrieval_config.example.yaml`
- `requirements.txt`

## Código

- `src/aia/generation/prompt_builder.py`
- `src/aia/generation/evidence_policy.py`
- `src/aia/generation/citation_formatter.py`
- `src/aia/generation/rag_answer.py`
- `src/aia/generation/rag_generator.py`
- `scripts/pipeline/query_rag_generator.py`

## Configuração

Arquivo:

- `config/generation_config.example.yaml`

Modelo padrão:

- `gpt-5.4-mini`

Sobrescrita por ambiente:

- `OPENAI_CHAT_MODEL`

## Saídas

- `reports/specs/rag-answer-generation.md`
- `corpus/reports/generation/rag-answer-generation-report.md`
- `corpus/reports/generation/rag-answer-generation-report.json`

## Fora do escopo

- interface web
- upload de documentos pelo usuário
- avaliação com documentos de outras tradições
- avaliação automática com RAGAS ou ARES
- alteração de chunks, embeddings ou PDFs
- nova extração, normalização, chunking ou indexação
- treinamento ou fine-tuning de modelo
